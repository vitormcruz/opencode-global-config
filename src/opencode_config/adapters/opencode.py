"""Wrapper fino do entrypoint opencode-adapter sobre o harness OpenCode."""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import os
from pathlib import Path
import sys
from typing import TextIO

from opencode_config.harnesses import ApplyOptions, criar_adapters
from opencode_config.harnesses.opencode import AdapterError
from opencode_config.lib.environment import (
    UnsupportedEnvironmentError,
    detect_environment,
)
from opencode_config.lib.paths import HARNESS_CONF_DIR

HELP_TEXT = """opencode-adapter

Configura a config global do OpenCode a partir deste repositorio
(links simbolicos em Linux/WSL; copia sincronizada no Windows).

Uso:
  opencode-adapter [--yes] [--quiet] [--repo-root PATH]

Opcoes:
  --yes             Nao pergunta confirmacao
  --quiet           Suprime saidas detalhadas
  --repo-root PATH  Define a raiz do repositorio
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
            and (harness / "opencode.json").is_file()
        ):
            return root

    raise AdapterError(
        "Raiz do repositorio nao encontrada; use --repo-root PATH"
    )


def _parse_arguments(
    arguments: Sequence[str],
) -> tuple[bool, bool, str | None]:
    assume_yes = False
    quiet = False
    repository: str | None = None
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == "--yes":
            assume_yes = True
        elif argument == "--quiet":
            quiet = True
        elif argument in {"--help", "-h"}:
            raise SystemExit(0)
        elif argument == "--repo-root":
            index += 1
            if index >= len(arguments):
                raise AdapterError("--repo-root exige um caminho")
            repository = arguments[index]
        elif argument.startswith("--repo-root="):
            repository = argument.split("=", 1)[1]
        else:
            raise AdapterError(f"Opcao desconhecida: {argument}")
        index += 1
    return assume_yes, quiet, repository


def _dispatch(
    arguments: Sequence[str],
    output: TextIO,
    error: TextIO,
) -> int:
    try:
        assume_yes, quiet, repository_argument = _parse_arguments(arguments)
    except SystemExit:
        output.write(HELP_TEXT)
        return 0
    except AdapterError as problem:
        error.write(f"ERRO: {problem}\n")
        error.write(HELP_TEXT)
        return 2

    try:
        adapter = criar_adapters(detect_environment(), ["opencode"])[0]
        adapter.apply(
            _resolve_repo_root(repository_argument),
            ApplyOptions(
                home=Path.home(),
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
