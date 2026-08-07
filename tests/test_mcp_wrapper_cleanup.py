from pathlib import Path
import json

import pytest


@pytest.mark.unit
def test_opencode_configs_have_no_mcp_block(repo_root: Path):
    config_paths = (
        repo_root / "opencode.json",
        repo_root / "tests/integration/config/opencode.test.json",
    )

    for path in config_paths:
        config = json.loads(path.read_text(encoding="utf-8"))
        assert config.get("mcp", {}) == {}


@pytest.mark.unit
def test_codebase_memory_install_keeps_cli_install_and_auto_index(repo_root: Path):
    content = (repo_root / "scripts/codebase-memory/install.sh").read_text(
        encoding="utf-8"
    )

    assert "npm install -g codebase-memory-mcp" in content
    assert "codebase-memory-mcp config set auto_index true" in content
    assert "codebase-memory-mcp install -y" not in content
    assert "OPENCODE_JSON" not in content


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
    assert "copilot-mcp-test.bats" not in makefile
    assert not (repo_root / "tests/integration/copilot-mcp-test.bats").exists()


@pytest.mark.unit
def test_opencode_mcp_integration_artifacts_are_removed(repo_root: Path):
    assert not (repo_root / "tests/integration/mcp-test.bats").exists()
    assert not (repo_root / "tests/integration/mcp-mock").exists()
