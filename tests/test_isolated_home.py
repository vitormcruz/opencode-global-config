"""O HOME isolado também isola os diretórios de dados do Windows."""

import os
from pathlib import Path

import pytest

from opencode_config.lib.environment import EnvironmentKind
from opencode_config.lib.paths import resolve_user_space_paths


@pytest.mark.unit
def test_isolated_home_redirects_windows_app_data_directories(
    isolated_home: Path,
) -> None:
    assert Path(os.environ["LOCALAPPDATA"]).is_relative_to(isolated_home)
    assert Path(os.environ["APPDATA"]).is_relative_to(isolated_home)


@pytest.mark.unit
def test_windows_user_space_paths_stay_inside_isolated_home(
    isolated_home: Path,
) -> None:
    paths = resolve_user_space_paths(EnvironmentKind.WINDOWS)

    for path in (paths.data_dir, paths.config_dir, paths.bin_dir):
        assert path.is_relative_to(isolated_home)
