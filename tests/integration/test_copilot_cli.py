"""Smoke tests for the Copilot CLI."""

import re
import shutil
import subprocess

import pytest


pytestmark = pytest.mark.copilot


COPILOT_INSTALL_ERROR = (
    "copilot CLI nao encontrado. Instale: "
    "npm install -g @github/copilot && copilot --login"
)


def _require_copilot() -> str:
    executable = shutil.which("copilot")
    if executable is None:
        pytest.fail(COPILOT_INSTALL_ERROR)
    return executable


def test_copilot_help_returns_exit_zero(copilot_home):
    executable = _require_copilot()
    result = subprocess.run(
        [executable, "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0


def test_copilot_version_displays_version(copilot_home):
    executable = _require_copilot()
    result = subprocess.run(
        [executable, "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert re.search(r"[0-9]+\.[0-9]+", result.stdout)
