"""Wrapper fino do entrypoint opencode-copilot-adapter sobre o harness Copilot."""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import os
from pathlib import Path
import sys
from typing import TextIO

from opencode_config.harnesses import ApplyOptions, criar_adapters
from opencode_config.harnesses.copilot import AdapterError
from opencode_config.lib.environment import (
    UnsupportedEnvironmentError,
    detect_environment,
)
from opencode_config.lib.paths import HARNESS_CONF_DIR

HELP_TEXT = """opencode-copilot-adapter

Sincroniza a fonte canonica deste repositorio com o Copilot CLI.

Uso:
  opencode-copilot-adapter [--yes] [--quiet] [--repo-root PATH]
                           [--dest-root PATH]

Opcoes:
  --yes             Nao pede confirmacao
  --quiet           Suprime saidas detalhadas
  --repo-root PATH  Define a raiz do repositorio
  --dest-root PATH  Substitui a raiz de destino (usado em testes)
  --help            Mostra esta ajuda
"""


def _resolve_repo_root(explicit: str | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))

    configured = os.environ.get("OPENCODE_CONFIG_REPO")
    if configured:
        candidates.append(Path(configured))

    candidates.append(Path.cwd())
    candidates.append(Path(__file__).resolve().parents[3])

    for candidate in candidates:
        root = candidate.expanduser().resolve()
        harness = root / HARNESS_CONF_DIR
        if (
            (harness / "agents").is_dir()
            and (harness / "commands").is_dir()
            and (harness / "skills").is_dir()
        ):
            return root

    raise AdapterError(
        "Raiz do repositorio nao encontrada; use --repo-root PATH"
    )


def _parse_arguments(
    arguments: Sequence[str],
) -> tuple[bool, bool, str | None, str | None]:
    assume_yes = False
    quiet = False
    repository: str | None = None
    destination: str | None = None
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == "--yes":
            assume_yes = True
        elif argument == "--quiet":
            quiet = True
        elif argument in {"--help", "-h"}:
            raise SystemExit(0)
        elif argument in {"--repo-root", "--dest-root"}:
            index += 1
            if index >= len(arguments):
                raise AdapterError(f"{argument} exige um caminho")
            if argument == "--repo-root":
                repository = arguments[index]
            else:
                destination = arguments[index]
        elif argument.startswith("--repo-root="):
            repository = argument.split("=", 1)[1]
        elif argument.startswith("--dest-root="):
            destination = argument.split("=", 1)[1]
        else:
            raise AdapterError(f"Opcao desconhecida: {argument}")
        index += 1
    return assume_yes, quiet, repository, destination


def _default_dest_root() -> Path:
    return Path(
        os.environ.get("DestRoot")
        or os.environ.get("DEST_ROOT")
        or os.environ.get("USERPROFILE")
        or os.environ.get("HOME")
        or Path.home()
    )


def _dispatch(
    arguments: Sequence[str],
    output: TextIO,
    error: TextIO,
) -> int:
    try:
        assume_yes, quiet, repository_arg, destination_arg = _parse_arguments(
            arguments
        )
    except SystemExit:
        output.write(HELP_TEXT)
        return 0
    except AdapterError as problem:
        error.write(f"ERRO: {problem}\n")
        output.write(HELP_TEXT)
        return 2

    try:
        adapter = criar_adapters(detect_environment(), ["copilot"])[0]
        adapter.apply(
            _resolve_repo_root(repository_arg),
            ApplyOptions(
                home=(
                    Path(destination_arg)
                    if destination_arg
                    else _default_dest_root()
                ),
                assume_yes=assume_yes,
                quiet=quiet,
                output=output,
                error=error,
            ),
        )
    except (AdapterError, OSError, UnsupportedEnvironmentError) as problem:
        error.write(f"ERRO: {problem}\n")
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Executa o adapter usando os streams reais do processo."""

    return _dispatch(
        list(sys.argv[1:] if argv is None else argv),
        sys.stdout,
        sys.stderr,
    )


def run_cli(argv: Sequence[str]) -> tuple[int, str, str]:
    """Executa o CLI com streams capturados para testes e integrações."""

    output = StringIO()
    error = StringIO()
    with redirect_stdout(output), redirect_stderr(error):
        status = _dispatch(list(argv), output, error)
    return status, output.getvalue(), error.getvalue()


if __name__ == "__main__":
    raise SystemExit(main())
