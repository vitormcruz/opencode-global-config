import json
import platform
import subprocess
import sys

import pytest

from opencode_config.lib import environment
from opencode_config.lib.config import (
    remove_marked_block,
    update_marked_block,
)
from opencode_config.lib.contract import ToolResult
from opencode_config.lib.environment import EnvironmentKind, detect_environment
from opencode_config.lib.paths import resolve_user_space_paths
from opencode_config.lib.process import run_command


@pytest.mark.unit
def test_detects_linux_with_runtime_platform_values(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setattr(platform, "release", lambda: "6.8.0")
    monkeypatch.setattr(
        environment,
        "_read_proc_version",
        lambda: "Linux version 6.8.0-generic",
    )

    assert detect_environment() is EnvironmentKind.LINUX


@pytest.mark.unit
def test_detects_wsl_from_runtime_proc_version(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setattr(platform, "release", lambda: "5.15.153-microsoft-standard")
    monkeypatch.setattr(
        environment,
        "_read_proc_version",
        lambda: "Linux version 5.15.153-microsoft-standard-WSL2",
    )

    assert detect_environment() is EnvironmentKind.WSL


@pytest.mark.unit
def test_detects_windows_without_reading_linux_proc_version(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Windows")

    def fail_if_proc_version_is_read():
        raise AssertionError("Windows detection must not read /proc/version")

    monkeypatch.setattr(environment, "_read_proc_version", fail_if_proc_version_is_read)

    assert detect_environment() is EnvironmentKind.WINDOWS


@pytest.mark.unit
def test_resolves_linux_user_space_directories(tmp_path):
    paths = resolve_user_space_paths(EnvironmentKind.LINUX, home=tmp_path)

    assert paths.home == tmp_path
    assert paths.config_dir == tmp_path / ".config"
    assert paths.data_dir == tmp_path / ".local" / "share"
    assert paths.bin_dir == tmp_path / ".local" / "bin"
    assert paths.pipx_bin == tmp_path / ".local" / "bin"


@pytest.mark.unit
def test_resolves_windows_user_space_directories(tmp_path):
    local_app_data = tmp_path / "AppData" / "Local"
    app_data = tmp_path / "AppData" / "Roaming"
    paths = resolve_user_space_paths(
        EnvironmentKind.WINDOWS,
        home=tmp_path,
        env={
            "LOCALAPPDATA": str(local_app_data),
            "APPDATA": str(app_data),
        },
    )

    assert paths.home == tmp_path
    assert paths.config_dir == app_data
    assert paths.data_dir == local_app_data
    assert paths.bin_dir == local_app_data / "opencode-config" / "bin"
    assert paths.pipx_bin == tmp_path / ".local" / "bin"
    assert paths.npm_bin == app_data / "npm"


@pytest.mark.unit
def test_run_command_captures_stdout_stderr_and_exit_code():
    result = run_command(
        [
            sys.executable,
            "-c",
            "import sys; print('out'); print('err', file=sys.stderr)",
        ]
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "out"
    assert result.stderr.strip() == "err"
    assert result.succeeded
    assert not result.timed_out


@pytest.mark.unit
def test_run_command_reports_nonzero_exit_code():
    result = run_command([sys.executable, "-c", "raise SystemExit(7)"])

    assert result.returncode == 7
    assert not result.succeeded
    assert not result.timed_out


@pytest.mark.unit
def test_run_command_reports_timeout():
    result = run_command(
        [sys.executable, "-c", "import time; time.sleep(1)"],
        timeout=0.1,
    )

    assert result.timed_out
    assert result.returncode is None
    assert not result.succeeded


@pytest.mark.unit
def test_tool_result_serializes_one_shared_json_contract():
    result = ToolResult.success(
        engine="fake-engine",
        artifacts=["/tmp/result.md"],
        stdout="done",
        stderr="",
    )

    assert json.loads(result.to_json()) == {
        "ok": True,
        "engine": "fake-engine",
        "artifacts": ["/tmp/result.md"],
        "stdout": "done",
        "stderr": "",
        "hint": "",
    }


@pytest.mark.unit
def test_tool_result_serializes_failure_with_hint():
    result = ToolResult.failure(
        engine="fake-engine",
        stderr="missing dependency",
        hint="Install fake-engine",
    )

    assert result.to_dict() == {
        "ok": False,
        "engine": "fake-engine",
        "artifacts": [],
        "stdout": "",
        "stderr": "missing dependency",
        "hint": "Install fake-engine",
    }


@pytest.mark.unit
def test_update_marked_block_is_idempotent(tmp_path):
    config_path = tmp_path / ".bashrc"
    config_path.write_text("before\n", encoding="utf-8")

    update_marked_block(config_path, "path", 'export PATH="$HOME/.local/bin:$PATH"')
    first_content = config_path.read_text(encoding="utf-8")

    update_marked_block(config_path, "path", 'export PATH="$HOME/.local/bin:$PATH"')

    assert config_path.read_text(encoding="utf-8") == first_content
    assert first_content.count("# >>> opencode-config:path >>>") == 1
    assert first_content.count("# <<< opencode-config:path <<<") == 1


@pytest.mark.unit
def test_update_marked_block_replaces_existing_content(tmp_path):
    config_path = tmp_path / ".bashrc"

    update_marked_block(config_path, "exa", "export OLD=1")
    update_marked_block(config_path, "exa", "export NEW=1")

    content = config_path.read_text(encoding="utf-8")
    assert "export OLD=1" not in content
    assert "export NEW=1" in content
    assert content.count("# >>> opencode-config:exa >>>") == 1


@pytest.mark.unit
def test_update_marked_block_accepts_windows_paths(tmp_path):
    config_path = tmp_path / "profile.ps1"

    update_marked_block(
        config_path,
        "path",
        '$env:Path = "C:\\Users\\tester\\.local\\bin;$env:Path"',
    )
    update_marked_block(
        config_path,
        "path",
        '$env:Path = "C:\\Users\\tester\\AppData\\npm;$env:Path"',
    )

    content = config_path.read_text(encoding="utf-8")
    assert "C:\\Users\\tester\\.local\\bin" not in content
    assert "C:\\Users\\tester\\AppData\\npm" in content


@pytest.mark.unit
def test_remove_marked_block_removes_only_requested_block(tmp_path):
    config_path = tmp_path / ".bashrc"
    config_path.write_text("before\n", encoding="utf-8")
    update_marked_block(config_path, "first", "export FIRST=1")
    update_marked_block(config_path, "second", "export SECOND=1")

    assert remove_marked_block(config_path, "first")
    content = config_path.read_text(encoding="utf-8")
    assert "export FIRST=1" not in content
    assert "export SECOND=1" in content
    assert not remove_marked_block(config_path, "first")
