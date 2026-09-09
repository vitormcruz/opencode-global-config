"""Entrypoint do bootstrap multiplataforma."""

from collections.abc import Mapping, Sequence
from pathlib import Path
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

from .installers import InstallContext, ensure_path_entry
from .interactive import InteractiveError, run_bootstrap


HELP_TEXT = """opencode-bootstrap

Uso:
  opencode-bootstrap [--yes] [--quiet] [--check-only] [--repo-root PATH]
                     [--harness LISTA]

Opcoes:
  --yes             Instala dependencias ausentes sem perguntar
  --quiet           Suprime a tabela e o progresso
  --check-only      Detecta e exibe comandos manuais sem instalar
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
) -> tuple[bool, bool, bool, str | None, list[str] | None, bool]:
    assume_yes = False
    quiet = False
    check_only = False
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
        elif argument in {"--help", "-h"}:
            return assume_yes, quiet, check_only, None, None, True
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
    return assume_yes, quiet, check_only, repo_root, harness_selection, False


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _apply_harnesses(
    environment: EnvironmentKind,
    repo_root: Path,
    selecao: Sequence[str] | None,
    *,
    assume_yes: bool,
    quiet: bool,
    output: TextIO,
    error: TextIO,
) -> int:
    """Configura cada harness selecionado, instalado e nao-pulado (D2)."""

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
        assume_yes, quiet, check_only, repo_arg, harness_selection, show_help = (
            _parse_arguments(arguments)
        )
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
        _cleanup_legacy_bashrc(check_only=check_only)
        if os.environ.get("OPENCODE_SKIP_DEPS") == "1":
            bootstrap_result = None
        else:
            bootstrap_result = run_bootstrap(
                context=_context_for(
                    environment,
                    repo_root,
                    persist_paths=not check_only,
                ),
                repo_root=repo_root,
                environment=environment,
                assume_yes=assume_yes,
                quiet=quiet,
                check_only=check_only,
                input_stream=sys.stdin,
                output=output,
            )
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

    adapter_status = _apply_harnesses(
        environment,
        repo_root,
        harness_selection,
        assume_yes=assume_yes,
        quiet=quiet,
        output=output,
        error=error,
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
