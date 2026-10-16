"""PATH herdado acima do limite do cmd não pode quebrar os subprocessos."""

from pathlib import Path

import pytest

from opencode_config.bootstrap.main import _merge_path_values
from opencode_config.lib.environment import EnvironmentKind

CMD_PATH_LIMIT = 8191


def _stale_entries(count: int) -> list[str]:
    return [f"Z:\\pytest-of-fake\\pytest-{index}\\bin" for index in range(count)]


@pytest.mark.unit
def test_windows_path_above_cmd_limit_drops_missing_directories(
    tmp_path: Path,
) -> None:
    kept = tmp_path / "ferramentas"
    kept.mkdir()
    inherited = ";".join([str(kept), *_stale_entries(400)])
    assert len(inherited) > CMD_PATH_LIMIT

    merged = _merge_path_values(
        {"Path": inherited},
        "",
        EnvironmentKind.WINDOWS,
    )

    assert merged["Path"] == str(kept)


@pytest.mark.unit
def test_windows_path_below_cmd_limit_keeps_every_entry(tmp_path: Path) -> None:
    inherited = ";".join([str(tmp_path), *_stale_entries(3)])
    assert len(inherited) < CMD_PATH_LIMIT

    merged = _merge_path_values(
        {"Path": inherited},
        "",
        EnvironmentKind.WINDOWS,
    )

    assert merged["Path"] == inherited
