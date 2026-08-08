"""Fixtures shared by non-Docker integration suites."""

from pathlib import Path

import pytest

from behavioral_helper import OpenCodeClient


@pytest.fixture(scope="module")
def opencode() -> OpenCodeClient:
    """Provide an OpenCode client after checking the service is available."""

    client = OpenCodeClient()
    client.require_available()
    return client


@pytest.fixture
def copilot_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate Copilot CLI configuration like the former BATS setup helper."""

    home = tmp_path / "home"
    home.mkdir()
    (home / ".bashrc").touch()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    return home
