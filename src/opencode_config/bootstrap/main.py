"""Entrypoint do bootstrap multiplataforma."""

from collections.abc import Mapping, Sequence
from pathlib import Path
import json
import os
import re
import sys
from typing import TextIO

from opencode_config.harnesses import (
    ApplyOptions,
    HarnessError,
    selecionar_harnesses,
)
from opencode_config.lib.environment import (
    EnvironmentKind,
    UnsupportedEnvironmentError,
    detect_environment,
)
from opencode_config.lib.paths import resolve_user_space_paths

from .ai_memory import (
    disable_ai_memory,
    provision_ai_memory,
    rollback_ai_memory,
)
from .installers import InstallContext, ensure_path_entry
from .interactive import InteractiveError, run_bootstrap


HELP_TEXT = """opencode-bootstrap

Uso:
  opencode-bootstrap [--yes] [--quiet] [--check-only] [--rollback-ai-memory]
                     [--repo-root PATH]
                     [--harness LISTA]

Opcoes:
  --yes             Instala dependencias ausentes sem perguntar
  --quiet           Suprime a tabela e o progresso
  --check-only      Detecta e exibe comandos manuais sem instalar
  --rollback-ai-memory  Remove a integração e preserva os dados ai-memory
  --repo-root PATH  Define a raiz do repositorio
  --harness LISTA   Configura apenas os harnesses listados
                    (ex.: opencode,copilot); default: todos os instalados
  --help            Mostra esta ajuda
"""


def _parse_harness_selection(raw: str) -> list[str]:
    selection = [name.strip() for name in raw.split(",") if name.strip()]
    if not selection:
        raise ValueError("--harness exige ao menos um nome de harness")
    return selection


def _parse_arguments(
    arguments: Sequence[str],
) -> tuple[bool, bool, bool, bool, str | None, list[str] | None, bool]:
    assume_yes = False
    quiet = False
    check_only = False
    rollback = False
    repo_root: str | None = None
    harness_selection: list[str] | None = None
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == "--yes":
            assume_yes = True
        elif argument == "--quiet":
            quiet = True
        elif argument == "--check-only":
            check_only = True
        elif argument == "--rollback-ai-memory":
            rollback = True
        elif argument in {"--help", "-h"}:
            return assume_yes, quiet, check_only, rollback, None, None, True
        elif argument == "--repo-root":
            index += 1
            if index >= len(arguments):
                raise ValueError("--repo-root exige um caminho")
            repo_root = arguments[index]
        elif argument.startswith("--repo-root="):
            repo_root = argument.split("=", 1)[1]
        elif argument == "--harness":
            index += 1
            if index >= len(arguments):
                raise ValueError("--harness exige uma lista")
            harness_selection = _parse_harness_selection(arguments[index])
        elif argument.startswith("--harness="):
            harness_selection = _parse_harness_selection(
                argument.split("=", 1)[1]
            )
        else:
            raise ValueError(f"Opcao desconhecida: {argument}")
        index += 1
    return (
        assume_yes,
        quiet,
        check_only,
        rollback,
        repo_root,
        harness_selection,
        False,
    )


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _repo_declares_ai_memory(repository: Path) -> bool:
    configuration = repository / "harness-conf" / "opencode.json"
    if not configuration.is_file():
        return False
    try:
        parsed = json.loads(configuration.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    servers = parsed.get("mcp", {}) if isinstance(parsed, dict) else {}
    return isinstance(servers, dict) and "ai-memory" in servers


def _apply_harnesses(
    environment: EnvironmentKind,
    repo_root: Path,
    selecao: Sequence[str] | None,
    *,
    assume_yes: bool,
    quiet: bool,
    output: TextIO,
    error: TextIO,
    ai_memory_enabled: bool | None = None,
    ai_memory_url: str | None = None,
    previous_ai_memory_url: str | None = None,
) -> int:
    """Configura cada harness selecionado, instalado e nao-pulado (ADR-0004)."""

    status = 0
    for definition in selecionar_harnesses(selecao):
        if os.environ.get(definition.skip_variable) == "1":
            continue
        adapter = definition.create(environment)
        if not adapter.installed(environment):
            output.write(
                f"AVISO: harness {definition.name} nao instalado; pulando\n"
            )
            continue
        try:
            adapter.apply(
                repo_root,
                ApplyOptions(
                    home=Path.home(),
                    assume_yes=assume_yes,
                    quiet=quiet,
                    output=output,
                    error=error,
                    ai_memory_enabled=ai_memory_enabled,
                    ai_memory_url=ai_memory_url,
                    previous_ai_memory_url=previous_ai_memory_url,
                ),
            )
        except (HarnessError, OSError) as problem:
            error.write(f"ERRO: harness {definition.name}: {problem}\n")
            status = 1
    return status


def _read_windows_user_path() -> str:
    if sys.platform != "win32":
        return ""

    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, _ = winreg.QueryValueEx(key, "Path")
    except OSError:
        return ""
    return str(value)


def _merge_path_values(
    current: Mapping[str, str],
    user_path: str,
    environment: EnvironmentKind,
) -> dict[str, str]:
    merged = dict(current)
    path_key = next(
        (name for name in merged if name.casefold() == "path"),
        "Path" if environment is EnvironmentKind.WINDOWS else "PATH",
    )
    separator = ";" if environment is EnvironmentKind.WINDOWS else ":"
    current_value = next(
        (value for name, value in merged.items() if name.casefold() == "path"),
        "",
    )
    values = [
        entry
        for entry in f"{current_value}{separator}{user_path}".split(separator)
        if entry
    ]
    unique: list[str] = []
    for entry in values:
        normalized = entry.casefold() if environment is EnvironmentKind.WINDOWS else entry
        if not any(
            (
                existing.casefold()
                if environment is EnvironmentKind.WINDOWS
                else existing
            )
            == normalized
            for existing in unique
        ):
            unique.append(entry)
    merged[path_key] = separator.join(unique)
    for name in list(merged):
        if name.casefold() == "path" and name != path_key:
            del merged[name]
    return merged


def _context_for(
    environment: EnvironmentKind,
    repo_root: Path,
    *,
    persist_paths: bool = True,
) -> InstallContext:
    profile = None
    if environment is not EnvironmentKind.WINDOWS:
        profile = Path.home() / ".bashrc"
    current_environment = dict(os.environ)
    if environment is EnvironmentKind.WINDOWS:
        current_environment = _merge_path_values(
            current_environment,
            _read_windows_user_path(),
            environment,
        )
    context = InstallContext(
        environment=environment,
        paths=resolve_user_space_paths(environment),
        repo_root=repo_root,
        profile_path=profile,
        current_environment=current_environment,
        persist_paths=persist_paths,
    )
    if environment is EnvironmentKind.WINDOWS:
        for path in (
            context.paths.pipx_bin,
            context.paths.npm_bin,
            context.paths.bin_dir,
        ):
            ensure_path_entry(
                path,
                environment_kind=environment,
                environ=context.current_environment,
                persist=persist_paths,
            )
    return context


def _cleanup_legacy_bashrc(*, check_only: bool) -> None:
    if check_only:
        return

    home = (
        os.environ.get("HOME")
        or os.environ.get("USERPROFILE")
        or os.fspath(Path.home())
    )
    bashrc = Path(home) / ".bashrc"
    if not bashrc.is_file():
        return

    content = bashrc.read_text(encoding="utf-8")
    cleaned = re.sub(
        r"^# Crawl4AI MCP - INICIO$\n.*?"
        r"^# Crawl4AI MCP - FIM$\n?",
        "",
        content,
        flags=re.MULTILINE | re.DOTALL,
    )
    if cleaned != content:
        bashrc.write_text(cleaned, encoding="utf-8")


def run(
    arguments: Sequence[str],
    *,
    output: TextIO,
    error: TextIO,
) -> int:
    try:
        (
            assume_yes,
            quiet,
            check_only,
            rollback,
            repo_arg,
            harness_selection,
            show_help,
        ) = _parse_arguments(arguments)
    except ValueError as problem:
        error.write(f"ERRO: {problem}\n{HELP_TEXT}")
        return 2

    if show_help:
        output.write(HELP_TEXT)
        return 0

    try:
        environment = detect_environment()
        repo_root = (
            _default_repo_root()
            if repo_arg is None
            else Path(repo_arg).expanduser().resolve()
        )
        if rollback and (check_only or harness_selection is not None):
            error.write(
                "ERRO: --rollback-ai-memory não aceita --check-only nem "
                "--harness; o rollback precisa atualizar os dois harnesses.\n"
            )
            return 2

        if rollback:
            context = _context_for(environment, repo_root, persist_paths=False)
            rollback_result = rollback_ai_memory(context, output=output)
            adapter_status = _apply_harnesses(
                environment,
                repo_root,
                None,
                assume_yes=True,
                quiet=quiet,
                output=output,
                error=error,
                ai_memory_enabled=False,
                previous_ai_memory_url=rollback_result.previous_mcp_url,
            )
            return max(1 if rollback_result.failed else 0, adapter_status)

        _cleanup_legacy_bashrc(check_only=check_only)
        context = _context_for(
            environment,
            repo_root,
            persist_paths=not check_only,
        )
        if os.environ.get("OPENCODE_SKIP_DEPS") == "1":
            bootstrap_result = None
            memory_result = (
                None
                if check_only
                else disable_ai_memory(
                    context,
                    reason="provisionamento ignorado por OPENCODE_SKIP_DEPS=1.",
                    output=output,
                )
            )
        else:
            bootstrap_result = run_bootstrap(
                context=context,
                repo_root=repo_root,
                environment=environment,
                assume_yes=assume_yes,
                quiet=quiet,
                check_only=check_only,
                input_stream=sys.stdin,
                output=output,
            )
            memory_result = None
    except (InteractiveError, UnsupportedEnvironmentError) as problem:
        error.write(f"ERRO: {problem}\n")
        return 1

    status = 0
    if bootstrap_result is not None and any(
        not result.success for result in bootstrap_result.install_results
    ):
        status = 1
    if check_only:
        return status

    if memory_result is None and _repo_declares_ai_memory(repo_root):
        memory_result = provision_ai_memory(context, output=output)
    elif memory_result is None:
        memory_result = disable_ai_memory(
            context,
            reason="a configuração canônica não declara mcp.ai-memory.",
            output=output,
        )
    if memory_result.failed:
        status = 1

    adapter_status = _apply_harnesses(
        environment,
        repo_root,
        harness_selection,
        assume_yes=assume_yes,
        quiet=quiet,
        output=output,
        error=error,
        ai_memory_enabled=memory_result.provisioned,
        ai_memory_url=memory_result.mcp_url,
        previous_ai_memory_url=memory_result.previous_mcp_url,
    )
    return max(status, adapter_status)


def main(argv: Sequence[str] | None = None) -> int:
    """Executa o bootstrap com os streams reais do processo."""

    return run(
        list(sys.argv[1:] if argv is None else argv),
        output=sys.stdout,
        error=sys.stderr,
    )


if __name__ == "__main__":
    raise SystemExit(main())
