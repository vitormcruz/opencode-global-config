"""Contrato JSON comum aos wrappers de ferramentas."""

from collections.abc import Sequence
from dataclasses import dataclass
import json
from typing import Any, TypeAlias


Artifact: TypeAlias = str | dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    """Resposta estavel para comandos que consomem e produzem JSON."""

    ok: bool
    engine: str
    artifacts: tuple[Artifact, ...] = ()
    stdout: str = ""
    stderr: str = ""
    hint: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "artifacts", tuple(self.artifacts))

    @classmethod
    def success(
        cls,
        *,
        engine: str,
        artifacts: Sequence[Artifact] = (),
        stdout: str = "",
        stderr: str = "",
        hint: str = "",
    ) -> "ToolResult":
        return cls(
            ok=True,
            engine=engine,
            artifacts=tuple(artifacts),
            stdout=stdout,
            stderr=stderr,
            hint=hint,
        )

    @classmethod
    def failure(
        cls,
        *,
        engine: str,
        stderr: str,
        hint: str = "",
        stdout: str = "",
        artifacts: Sequence[Artifact] = (),
    ) -> "ToolResult":
        return cls(
            ok=False,
            engine=engine,
            artifacts=tuple(artifacts),
            stdout=stdout,
            stderr=stderr,
            hint=hint,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "engine": self.engine,
            "artifacts": list(self.artifacts),
            "stdout": self.stdout,
            "stderr": self.stderr,
            "hint": self.hint,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, separators=(",", ":"))
