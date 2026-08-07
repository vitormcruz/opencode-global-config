"""Deteccao do ambiente de execucao em tempo de chamada."""

from enum import Enum
from pathlib import Path

import platform


class EnvironmentKind(str, Enum):
    """Ambientes suportados pelo bootstrap."""

    LINUX = "linux"
    WSL = "wsl"
    WINDOWS = "windows"


class UnsupportedEnvironmentError(RuntimeError):
    """Indica que o sistema operacional nao e suportado."""


def _read_proc_version() -> str:
    try:
        return Path("/proc/version").read_text(encoding="utf-8")
    except OSError:
        return ""


def detect_environment() -> EnvironmentKind:
    """Detecta Linux nativo, WSL ou Windows sem efeitos no import."""

    system = platform.system().lower()
    if system == "windows":
        return EnvironmentKind.WINDOWS

    if system == "linux":
        runtime_markers = f"{platform.release()} {_read_proc_version()}".lower()
        if "microsoft" in runtime_markers or "wsl" in runtime_markers:
            return EnvironmentKind.WSL
        return EnvironmentKind.LINUX

    raise UnsupportedEnvironmentError(
        f"Sistema operacional nao suportado: {platform.system()}"
    )
