"""Resolucao de diretorios user-space por ambiente."""

from collections.abc import Mapping
from dataclasses import dataclass
import os
from pathlib import Path

from .environment import EnvironmentKind


@dataclass(frozen=True)
class UserSpacePaths:
    """Diretorios usados por ferramentas instaladas sem privilegio."""

    home: Path
    config_dir: Path
    data_dir: Path
    bin_dir: Path
    pipx_bin: Path
    npm_bin: Path


def resolve_user_space_paths(
    environment: EnvironmentKind,
    *,
    home: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> UserSpacePaths:
    """Resolve caminhos sem consultar variaveis de SO durante o import."""

    resolved_home = Path.home() if home is None else Path(home)
    variables = os.environ if env is None else env

    if environment in (EnvironmentKind.LINUX, EnvironmentKind.WSL):
        local_data = resolved_home / ".local"
        return UserSpacePaths(
            home=resolved_home,
            config_dir=resolved_home / ".config",
            data_dir=local_data / "share",
            bin_dir=local_data / "bin",
            pipx_bin=local_data / "bin",
            npm_bin=local_data / "bin",
        )

    if environment is EnvironmentKind.WINDOWS:
        local_app_data = Path(
            variables.get("LOCALAPPDATA") or resolved_home / "AppData" / "Local"
        )
        app_data = Path(
            variables.get("APPDATA") or resolved_home / "AppData" / "Roaming"
        )
        return UserSpacePaths(
            home=resolved_home,
            config_dir=app_data,
            data_dir=local_app_data,
            bin_dir=local_app_data / "opencode-config" / "bin",
            pipx_bin=resolved_home / ".local" / "bin",
            npm_bin=app_data / "npm",
        )

    raise ValueError(f"Ambiente nao suportado: {environment}")
