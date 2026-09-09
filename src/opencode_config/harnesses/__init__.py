"""Contrato comum de harnesses e reexport do registry de adapters."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Protocol, TextIO, runtime_checkable

from opencode_config.lib.environment import EnvironmentKind


@dataclass(frozen=True)
class ApplyOptions:
    """Parametros de aplicacao de um harness sobre a home do usuario."""

    home: Path
    assume_yes: bool = False
    quiet: bool = False
    timestamp: str | None = None
    output: TextIO | None = None
    error: TextIO | None = None

    def resolve_streams(
        self,
    ) -> tuple[TextIO, TextIO]:
        """Retorna os streams de saida/erro, caindo nos do processo."""
        return (
            self.output if self.output is not None else sys.stdout,
            self.error if self.error is not None else sys.stderr,
        )


@runtime_checkable
class HarnessAdapter(Protocol):
    """Contrato de um harness configuravel pelo bootstrap."""

    @property
    def name(self) -> str: ...

    def installed(self, environment: EnvironmentKind) -> bool: ...

    def apply(self, repository: Path, options: ApplyOptions) -> None: ...


@dataclass(frozen=True)
class HarnessDefinition:
    """Entrada do registry: nome, construtor com strategy e var de escape."""

    name: str
    create: Callable[[EnvironmentKind], HarnessAdapter]
    skip_variable: str


from opencode_config.harnesses.factory import (  # noqa: E402
    HARNESSES,
    criar_adapters,
    selecionar_harnesses,
)

__all__ = [
    "ApplyOptions",
    "HARNESSES",
    "HarnessAdapter",
    "HarnessDefinition",
    "criar_adapters",
    "selecionar_harnesses",
]
