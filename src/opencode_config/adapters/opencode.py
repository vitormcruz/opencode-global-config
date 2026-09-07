"""Adapter Linux/WSL para a configuracao global do OpenCode."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from io import StringIO
import os
from pathlib import Path
import re
import sys
from typing import TextIO

from opencode_config.lib.environment import (
    EnvironmentKind,
    UnsupportedEnvironmentError,
    detect_environment,
)
from opencode_config.lib.paths import HARNESS_CONF_DIR
from opencode_config.lib.versions import fnm_node_bin_dir

HELP_TEXT = """opencode-adapter

Cria links simbolicos em ~/.config/opencode apontando para este repo.

Uso:
  opencode-adapter [--yes] [--quiet] [--repo-root PATH]

Opcoes:
  --yes             Nao pergunta confirmacao
  --quiet           Suprime saidas detalhadas
  --repo-root PATH  Define a raiz do repositorio
  --help            Mostra esta ajuda
"""

_DESTINATIONS = (
    (f"{HARNESS_CONF_DIR}/agents", "agents"),
    (f"{HARNESS_CONF_DIR}/commands", "commands"),
    (f"{HARNESS_CONF_DIR}/opencode.json", "opencode.json"),
    (f"{HARNESS_CONF_DIR}/skills", "skills"),
    ("scripts", "scripts"),
)


class AdapterError(RuntimeError):
    """Erro esperado durante a configuracao do adapter."""


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


def _resolve_path(path: Path) -> Path:
    return path.resolve(strict=False)


def _current_target(destination: Path) -> Path | None:
    if not destination.is_symlink():
        return None
    try:
        return _resolve_path(destination)
    except OSError:
        return None


def _backup_if_exists(destination: Path, backup_dir: Path) -> None:
    if not destination.exists() and not destination.is_symlink():
        return

    backup_dir.mkdir(parents=True, exist_ok=True)
    base = backup_dir / destination.name
    output = base
    index = 1
    while output.exists() or output.is_symlink():
        output = backup_dir / f"{destination.name}.{index}"
        index += 1
    destination.rename(output)


def _link_one(source: Path, destination: Path, backup_dir: Path) -> None:
    source_resolved = _resolve_path(source)
    current = _current_target(destination)
    if current is not None and current == source_resolved:
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    _backup_if_exists(destination, backup_dir)
    destination.symlink_to(
        source_resolved,
        target_is_directory=source_resolved.is_dir(),
    )


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _append_block(path: Path, content: str) -> None:
    existing = _read_text(path)
    separator = "" if not existing or existing.endswith("\n\n") else "\n"
    updated = f"{existing}{separator}{content.rstrip()}\n"
    if updated != existing:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(updated, encoding="utf-8")


def _bashrc_has(path: Path, pattern: str) -> bool:
    return bool(re.search(pattern, _read_text(path), flags=re.MULTILINE))


def _remove_legacy_test_library_block(path: Path) -> None:
    existing = _read_text(path)
    updated = re.sub(
        r"^# opencode-config: bibliotecas do [A-Za-z0-9_-]+[ \t]*\n"
        r"^export [A-Z0-9_]+_LIB_PATH="
        r'"\$HOME/\.local/lib/[A-Za-z0-9_-]+"[ \t]*\n?',
        "",
        existing,
        flags=re.MULTILINE,
    )
    updated = re.sub(
        r"^# opencode-config: bin(?:arios|ários) locais \([^)\r\n]*\)[ \t]*\n?",
        "",
        updated,
        flags=re.MULTILINE,
    )
    if updated != existing:
        path.write_text(updated, encoding="utf-8")


def _setup_bashrc(home: Path, environment: Mapping[str, str]) -> None:
    bashrc = home / ".bashrc"
    _remove_legacy_test_library_block(bashrc)

    if not _bashrc_has(
        bashrc,
        r"^[ \t]*export[ \t]+OPENCODE_ENABLE_EXA=1([ \t]*|[ \t]*#.*)$",
    ):
        _append_block(
            bashrc,
            "# opencode-config: websearch (Exa AI)\n"
            "export OPENCODE_ENABLE_EXA=1",
        )

    if not _bashrc_has(
        bashrc,
        r"\$HOME/\.local/bin|\$\{HOME\}/\.local/bin",
    ):
        _append_block(
            bashrc,
            "# opencode-config: binarios locais\n"
            'export PATH="$HOME/.local/bin:$PATH"',
        )

    if not _bashrc_has(bashrc, r"fnm/node-versions"):
        node_bin = fnm_node_bin_dir(home, environment)
        if node_bin is not None:
            _append_block(
                bashrc,
                "# opencode-config: node (fnm) - path estatico para shells "
                "nao-interativos\n"
                f'export PATH="{node_bin}:$PATH"',
            )


def _status_line(
    source: Path,
    destination: Path,
    output: Callable[[str], None],
) -> None:
    source_resolved = _resolve_path(source)
    current = _current_target(destination)
    if current is not None and current == source_resolved:
        output(f"OK    {destination}")
        return

    if destination.exists() or destination.is_symlink():
        output(f"BK    {destination}")
        output(f"LN    {destination} -> {source_resolved}")
        return

    output(f"LN    {destination} -> {source_resolved}")


def _print_plan(
    repository: Path,
    home: Path,
    backup_dir: Path,
    output: Callable[[str], None],
) -> None:
    config_dir = home / ".config" / "opencode"
    bashrc = home / ".bashrc"
    output(f"Repo:   {repository}")
    output(f"Destino: {config_dir}")
    output(f"Backup: {backup_dir}")
    output("Plano:")

    if not config_dir.is_dir():
        output(f"MKDIR {config_dir}")

    for source, destination in _DESTINATIONS:
        _status_line(repository / source, config_dir / destination, output)

    if _bashrc_has(
        bashrc,
        r"^[ \t]*export[ \t]+OPENCODE_ENABLE_EXA=1([ \t]*|[ \t]*#.*)$",
    ):
        output(f"OK    {bashrc} OPENCODE_ENABLE_EXA=1")
    else:
        output(f"ENV   {bashrc} << OPENCODE_ENABLE_EXA=1")

    if _bashrc_has(bashrc, r"\$HOME/\.local/bin|\$\{HOME\}/\.local/bin"):
        output(f"OK    {bashrc} PATH includes ~/.local/bin")
    else:
        output(f"ENV   {bashrc} << PATH=$HOME/.local/bin:$PATH")

    if _bashrc_has(bashrc, r"fnm/node-versions"):
        output(f"OK    {bashrc} PATH includes fnm node")
    else:
        node_bin = fnm_node_bin_dir(home, os.environ)
        if node_bin is not None:
            output(f"ENV   {bashrc} << PATH={node_bin}:$PATH")


def _confirm(
    assume_yes: bool,
    input_stream: TextIO,
    output: TextIO,
    error: TextIO,
) -> None:
    if assume_yes:
        return

    if not input_stream.isatty() or not output.isatty():
        error.write("Sem TTY para confirmacao; use --yes\n")
        raise AdapterError("confirmacao sem TTY")

    output.write("Aplicar estas alteracoes? [y/N] ")
    answer = input_stream.readline().strip().lower()
    if answer not in {"y", "yes"}:
        output.write("Cancelado.\n")
        raise AdapterError("operacao cancelada")


def configure(
    repository: Path,
    home: Path,
    *,
    assume_yes: bool,
    environment: EnvironmentKind | None = None,
    timestamp: str | None = None,
    input_stream: TextIO | None = None,
    output: TextIO | None = None,
    error: TextIO | None = None,
) -> None:
    """Aplica a configuracao global do OpenCode no Linux/WSL."""

    current_environment = (
        detect_environment() if environment is None else environment
    )
    if current_environment is EnvironmentKind.WINDOWS:
        raise UnsupportedEnvironmentError(
            "O adapter OpenCode e exclusivo de Linux/WSL; "
            "no Windows use o adapter Copilot."
        )
    if current_environment not in {
        EnvironmentKind.LINUX,
        EnvironmentKind.WSL,
    }:
        raise UnsupportedEnvironmentError(
            f"Ambiente nao suportado: {current_environment.value}"
        )

    input_stream = sys.stdin if input_stream is None else input_stream
    output = sys.stdout if output is None else output
    error = sys.stderr if error is None else error
    write = lambda message: output.write(f"{message}\n")

    resolved_home = home.expanduser().resolve()
    resolved_repository = repository.expanduser().resolve()
    config_dir = resolved_home / ".config" / "opencode"
    backup_name = timestamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = resolved_home / ".config" / "opencode-backup" / backup_name

    _print_plan(resolved_repository, resolved_home, backup_dir, write)
    _confirm(assume_yes, input_stream, output, error)

    write("Aplicando...")
    config_dir.mkdir(parents=True, exist_ok=True)
    for source, destination in _DESTINATIONS:
        _link_one(
            resolved_repository / source,
            config_dir / destination,
            backup_dir,
        )
    _setup_bashrc(resolved_home, os.environ)
    write("Pronto.")


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
        configure_output = StringIO() if quiet else output
        configure(
            _resolve_repo_root(repository_argument),
            Path(os.environ.get("HOME") or Path.home()),
            assume_yes=assume_yes,
            output=configure_output,
            error=error,
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
