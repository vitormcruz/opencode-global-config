from pathlib import Path
import json

import pytest


@pytest.mark.unit
def test_opencode_canonical_declares_ai_memory_mcp(repo_root: Path):
    config_path = repo_root / "harness-conf" / "opencode.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    mcp_servers = config["mcp"]

    assert set(mcp_servers) == {"ai-memory"}
    assert mcp_servers["ai-memory"] == {
        "type": "remote",
        "url": "http://127.0.0.1:49374/mcp",
        "enabled": True,
    }


@pytest.mark.unit
def test_opencode_integration_config_does_not_declare_mcp(repo_root: Path) -> None:
    config_path = (
        repo_root / "tests" / "integration" / "config" / "opencode.test.json"
    )
    config = json.loads(config_path.read_text(encoding="utf-8"))

    assert "mcp" not in config


@pytest.mark.unit
def test_legacy_install_wrappers_are_removed(repo_root: Path):
    assert not (repo_root / "scripts/browser-test/install-playwright.sh").exists()
    assert not (repo_root / "scripts/codebase-memory/install.sh").exists()


@pytest.mark.unit
def test_makefile_is_removed(repo_root: Path):
    assert not (repo_root / "Makefile").exists()


@pytest.mark.unit
def test_mcp_wrapper_artifacts_are_not_orchestrated(repo_root: Path):
    files = (
        repo_root / "scripts/bootstrap_repo/wsl-install-deps.sh",
        repo_root / "adapters/copilot-cli/copilot-cli-adapter.sh",
        repo_root / "adapters/copilot-cli/copilot-cli-adapter.ps1",
        repo_root / "Makefile",
    )

    for path in files:
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        assert "servers.json" not in content


@pytest.mark.unit
def test_copilot_integration_does_not_reference_removed_mcp_suite(repo_root: Path):
    makefile_path = repo_root / "Makefile"
    makefile = (
        makefile_path.read_text(encoding="utf-8")
        if makefile_path.exists()
        else ""
    )

    assert "command -v mcp" not in makefile


@pytest.mark.unit
def test_opencode_mcp_integration_artifacts_are_removed(repo_root: Path):
    tests_root = repo_root / "tests"
    assert not any(
        path.is_dir() and path.name == "mcp-mock"
        for path in tests_root.rglob("*")
    )
