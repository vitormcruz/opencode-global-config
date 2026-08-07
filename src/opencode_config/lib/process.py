"""Execucao controlada de subprocessos."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class CommandResult:
    """Resultado observavel de um comando executado."""

    args: tuple[str, ...]
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0 and not self.timed_out


def _as_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def run_command(
    command: Sequence[str | os.PathLike[str]],
    *,
    input_text: str | None = None,
    timeout: float | None = None,
    cwd: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> CommandResult:
    """Executa comando capturando streams e tratando timeout explicitamente."""

    args = tuple(os.fspath(argument) for argument in command)
    try:
        completed = subprocess.run(
            args,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        return CommandResult(
            args=args,
            returncode=None,
            stdout=_as_text(error.stdout),
            stderr=_as_text(error.stderr),
            timed_out=True,
        )

    return CommandResult(
        args=args,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
