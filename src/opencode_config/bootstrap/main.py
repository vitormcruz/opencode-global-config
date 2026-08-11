"""Entrypoint do bootstrap multiplataforma."""

from collections.abc import Sequence
from pathlib import Path
import os
import re
import sys
from typing import TextIO

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

Opcoes:
  --yes             Instala dependencias ausentes sem perguntar
  --quiet           Suprime a tabela e o progresso
  --check-only      Detecta e exibe comandos manuais sem instalar
  --repo-root PATH  Define a raiz do repositorio
  --help            Mostra esta ajuda
"""


def _parse_arguments(
    arguments: Sequence[str],
) -> tuple[bool, bool, bool, str | None, bool]:
    assume_yes = False
    quiet = False
    check_only = False
    repo_root: str | None = None
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
            return assume_yes, quiet, check_only, None, True
        elif argument == "--repo-root":
            index += 1
            if index >= len(arguments):
                raise ValueError("--repo-root exige um caminho")
            repo_root = arguments[index]
        elif argument.startswith("--repo-root="):
            repo_root = argument.split("=", 1)[1]
        else:
            raise ValueError(f"Opcao desconhecida: {argument}")
        index += 1
    return assume_yes, quiet, check_only, repo_root, False


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _adapter_arguments(
    repo_root: Path,
    *,
    assume_yes: bool,
    quiet: bool,
) -> list[str]:
    arguments: list[str] = []
    if assume_yes:
        arguments.append("--yes")
    if quiet:
        arguments.append("--quiet")
    arguments.extend(["--repo-root", str(repo_root)])
    return arguments


def _run_opencode_adapter(repo_root: Path, arguments: Sequence[str]) -> int:
    from opencode_config.adapters.opencode import main as adapter_main

    return adapter_main(arguments)


def _run_copilot_adapter(repo_root: Path, arguments: Sequence[str]) -> int:
    from opencode_config.adapters.copilot import main as adapter_main

    return adapter_main(arguments)


def _context_for(
    environment: EnvironmentKind,
    repo_root: Path,
    *,
    persist_paths: bool = True,
) -> InstallContext:
    profile = None
    if environment is not EnvironmentKind.WINDOWS:
        profile = Path.home() / ".bashrc"
    context = InstallContext(
        environment=environment,
        paths=resolve_user_space_paths(environment),
        repo_root=repo_root,
        profile_path=profile,
        current_environment=dict(os.environ),
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

    bashrc = Path.home() / ".bashrc"
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
        assume_yes, quiet, check_only, repo_arg, show_help = _parse_arguments(
            arguments
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

    adapter_args = _adapter_arguments(
        repo_root,
        assume_yes=assume_yes,
        quiet=quiet,
    )
    if environment is EnvironmentKind.WINDOWS:
        if os.environ.get("OPENCODE_SKIP_COPILOT_ADAPTER") == "1":
            return status
        adapter_status = _run_copilot_adapter(repo_root, adapter_args)
    else:
        if os.environ.get("OPENCODE_SKIP_OPENCODE_ADAPTER") == "1":
            return status
        adapter_status = _run_opencode_adapter(repo_root, adapter_args)
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
