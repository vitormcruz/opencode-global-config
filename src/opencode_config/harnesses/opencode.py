"""Harness OpenCode: adapter de fluxo e strategies de materializacao por SO.

O adapter cuida do plano, da confirmacao, do AGENTS.md global e do backup.
A strategy decide como materializar cada destino e como persistir env vars
do usuario; o adapter nunca consulta o sistema operacional.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Protocol, TextIO

from opencode_config.harnesses import ApplyOptions, HarnessError
from opencode_config.lib.environment import EnvironmentKind
from opencode_config.lib.paths import HARNESS_CONF_DIR
from opencode_config.lib.sync import (
    backup_move,
    link_one,
    link_target,
    paths_equal,
    resolve_target,
    sync_path,
)
from opencode_config.lib.versions import fnm_node_bin_dir
from opencode_config.lib.windows_env import get_user_env, set_user_env


class AdapterError(HarnessError):
    """Erro esperado durante a configuracao do harness OpenCode."""


_POSIX_DESTINATIONS: tuple[tuple[str, str], ...] = (
    (f"{HARNESS_CONF_DIR}/agents", "agents"),
    (f"{HARNESS_CONF_DIR}/commands", "commands"),
    (f"{HARNESS_CONF_DIR}/opencode.json", "opencode.json"),
    (f"{HARNESS_CONF_DIR}/skills", "skills"),
    ("scripts", "scripts"),
)

# No Windows nao ha link para scripts/: a infra do repo fica acessivel
# pelo proprio clone (D1); os 4 destinos de harness-conf bastam.
_WINDOWS_DESTINATIONS: tuple[tuple[str, str], ...] = (
    (f"{HARNESS_CONF_DIR}/agents", "agents"),
    (f"{HARNESS_CONF_DIR}/commands", "commands"),
    (f"{HARNESS_CONF_DIR}/opencode.json", "opencode.json"),
    (f"{HARNESS_CONF_DIR}/skills", "skills"),
)

_EXA_EXPORT = (
    r"^[ \t]*export[ \t]+OPENCODE_ENABLE_EXA=1([ \t]*|[ \t]*#.*)$"
)
_LOCAL_BIN = r"\$HOME/\.local/bin|\$\{HOME\}/\.local/bin"
_FNM_NODE = r"fnm/node-versions"


class OpenCodeEnvStrategy(Protocol):
    """Contrato de materializacao do OpenCode para um sistema operacional."""

    def config_dir(self, home: Path) -> Path: ...

    def destinations(self) -> tuple[tuple[str, str], ...]: ...

    def status_line(self, source: Path, destination: Path) -> str: ...

    def materialize(
        self,
        source: Path,
        destination: Path,
        backup_dir: Path,
    ) -> None: ...

    def env_status(
        self,
        home: Path,
        environment: Mapping[str, str],
    ) -> list[str]: ...

    def setup_env(self, home: Path, environment: Mapping[str, str]) -> None: ...


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


_MARKED_BLOCK = re.compile(
    r"<!-- (?P<marker>[A-Za-z0-9_.-]+):start -->.*?<!-- (?P=marker):end -->",
    flags=re.DOTALL,
)


def _managed_blocks(content: str) -> list[str]:
    """Extrai blocos `<!-- ferramenta:start -->...<!-- ferramenta:end -->`."""

    return [match.group(0).strip() for match in _MARKED_BLOCK.finditer(content)]


def _desired_agents_content(repository: Path, existing: str) -> str | None:
    """Base global + blocos gerenciados por ferramentas externas.

    O destino e arquivo regular, nunca symlink: ferramentas como o
    codebase-memory-mcp escrevem no path atraves de symlinks e mutariam
    a base versionada do repositorio.
    """

    base = repository / HARNESS_CONF_DIR / "AGENTS.base.md"
    if not base.is_file():
        return None
    desired = base.read_text(encoding="utf-8").strip() + "\n"
    for block in _managed_blocks(existing):
        desired += f"\n{block}\n"
    return desired


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


def _sync_agents_base(
    repository: Path,
    config_dir: Path,
    backup_dir: Path,
    output: Callable[[str], None],
) -> None:
    destination = config_dir / "AGENTS.md"
    existing = _read_text(destination)
    desired = _desired_agents_content(repository, existing)
    if desired is None:
        return
    if existing == desired:
        output(f"OK    {destination}")
        return
    if existing:
        backup_move(destination, backup_dir)
    destination.write_text(desired, encoding="utf-8")
    blocks = len(_managed_blocks(existing))
    output(f"CP    {destination} (base + {blocks} bloco(s) gerenciado(s))")


class OpenCodePosix:
    """Strategy POSIX: symlinks para o repo e env vars no .bashrc."""

    def config_dir(self, home: Path) -> Path:
        return home / ".config" / "opencode"

    def destinations(self) -> tuple[tuple[str, str], ...]:
        return _POSIX_DESTINATIONS

    def status_line(self, source: Path, destination: Path) -> str:
        source_resolved = resolve_target(source)
        current = link_target(destination)
        if current is not None and current == source_resolved:
            return f"OK    {destination}"
        if destination.exists() or destination.is_symlink():
            return (
                f"BK    {destination}\n"
                f"LN    {destination} -> {source_resolved}"
            )
        return f"LN    {destination} -> {source_resolved}"

    def materialize(
        self,
        source: Path,
        destination: Path,
        backup_dir: Path,
    ) -> None:
        link_one(source, destination, backup_dir)

    def env_status(
        self,
        home: Path,
        environment: Mapping[str, str],
    ) -> list[str]:
        bashrc = home / ".bashrc"
        lines: list[str] = []
        if _bashrc_has(bashrc, _EXA_EXPORT):
            lines.append(f"OK    {bashrc} OPENCODE_ENABLE_EXA=1")
        else:
            lines.append(f"ENV   {bashrc} << OPENCODE_ENABLE_EXA=1")

        if _bashrc_has(bashrc, _LOCAL_BIN):
            lines.append(f"OK    {bashrc} PATH includes ~/.local/bin")
        else:
            lines.append(
                f"ENV   {bashrc} << PATH=$HOME/.local/bin:$PATH"
            )

        if _bashrc_has(bashrc, _FNM_NODE):
            lines.append(f"OK    {bashrc} PATH includes fnm node")
        else:
            node_bin = fnm_node_bin_dir(home, environment)
            if node_bin is not None:
                lines.append(f"ENV   {bashrc} << PATH={node_bin}:$PATH")
        return lines

    def setup_env(self, home: Path, environment: Mapping[str, str]) -> None:
        _setup_bashrc(home, environment)


class OpenCodeWindows:
    """Strategy Windows: copia sincronizada e env vars em HKCU (D1/D4)."""

    def config_dir(self, home: Path) -> Path:
        return home / ".config" / "opencode"

    def destinations(self) -> tuple[tuple[str, str], ...]:
        return _WINDOWS_DESTINATIONS

    def status_line(self, source: Path, destination: Path) -> str:
        if paths_equal(source, destination):
            return f"OK    {destination}"
        if destination.exists() or destination.is_symlink():
            return (
                f"BK    {destination}\n"
                f"CP    {destination} << {source}"
            )
        return f"CP    {destination} << {source}"

    def materialize(
        self,
        source: Path,
        destination: Path,
        backup_dir: Path,
    ) -> None:
        sync_path(source, destination, backup_dir)

    def env_status(
        self,
        home: Path,
        environment: Mapping[str, str],
    ) -> list[str]:
        if get_user_env("OPENCODE_ENABLE_EXA") == "1":
            return [r"OK    HKCU\Environment OPENCODE_ENABLE_EXA=1"]
        return [r"ENV   HKCU\Environment << OPENCODE_ENABLE_EXA=1"]

    def setup_env(self, home: Path, environment: Mapping[str, str]) -> None:
        if get_user_env("OPENCODE_ENABLE_EXA") != "1":
            set_user_env("OPENCODE_ENABLE_EXA", "1")


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

    if not _bashrc_has(bashrc, _EXA_EXPORT):
        _append_block(
            bashrc,
            "# opencode-config: websearch (Exa AI)\n"
            "export OPENCODE_ENABLE_EXA=1",
        )

    if not _bashrc_has(bashrc, _LOCAL_BIN):
        _append_block(
            bashrc,
            "# opencode-config: binarios locais\n"
            'export PATH="$HOME/.local/bin:$PATH"',
        )

    if not _bashrc_has(bashrc, _FNM_NODE):
        node_bin = fnm_node_bin_dir(home, environment)
        if node_bin is not None:
            _append_block(
                bashrc,
                "# opencode-config: node (fnm) - path estatico para shells "
                "nao-interativos\n"
                f'export PATH="{node_bin}:$PATH"',
            )


class OpenCodeAdapter:
    """Aplica a configuracao global do OpenCode delegando a strategy."""

    def __init__(self, strategy: OpenCodeEnvStrategy) -> None:
        self.strategy = strategy

    @property
    def name(self) -> str:
        return "opencode"

    def installed(self, environment: EnvironmentKind) -> bool:
        return shutil.which("opencode") is not None

    def apply(self, repository: Path, options: ApplyOptions) -> None:
        strategy = self.strategy
        output, error = options.resolve_streams()
        write = (
            (lambda message: output.write(f"{message}\n"))
            if not options.quiet
            else (lambda _message: None)
        )

        home = options.home.expanduser().resolve()
        resolved_repository = repository.expanduser().resolve()
        config_dir = strategy.config_dir(home)
        backup_name = options.timestamp or datetime.now().strftime(
            "%Y%m%d-%H%M%S"
        )
        backup_dir = home / ".config" / "opencode-backup" / backup_name

        _print_plan(
            resolved_repository,
            home,
            config_dir,
            backup_dir,
            strategy,
            write,
        )
        _confirm(options.assume_yes, sys.stdin, output, error)

        write("Aplicando...")
        config_dir.mkdir(parents=True, exist_ok=True)
        for source, destination in strategy.destinations():
            strategy.materialize(
                resolved_repository / source,
                config_dir / destination,
                backup_dir,
            )
        _sync_agents_base(
            resolved_repository,
            config_dir,
            backup_dir,
            write,
        )
        strategy.setup_env(home, os.environ)
        write("Pronto.")


def _print_plan(
    repository: Path,
    home: Path,
    config_dir: Path,
    backup_dir: Path,
    strategy: OpenCodeEnvStrategy,
    output: Callable[[str], None],
) -> None:
    output(f"Repo:   {repository}")
    output(f"Destino: {config_dir}")
    output(f"Backup: {backup_dir}")
    output("Plano:")

    if not config_dir.is_dir():
        output(f"MKDIR {config_dir}")

    for source, destination in strategy.destinations():
        output(
            strategy.status_line(
                repository / source,
                config_dir / destination,
            )
        )

    agents_md = config_dir / "AGENTS.md"
    existing = _read_text(agents_md)
    desired = _desired_agents_content(repository, existing)
    if desired is not None:
        if existing == desired:
            output(f"OK    {agents_md}")
        else:
            base = repository / HARNESS_CONF_DIR / "AGENTS.base.md"
            output(f"CP    {agents_md} << {base}")

    for line in strategy.env_status(home, os.environ):
        output(line)
