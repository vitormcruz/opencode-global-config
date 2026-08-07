from pathlib import Path

import pytest


@pytest.mark.unit
def test_mcp_wrapper_artifacts_are_not_orchestrated(repo_root: Path):
    files = (
        repo_root / "scripts/bootstrap_repo/wsl-install-deps.sh",
        repo_root / "adapters/copilot-cli/copilot-cli-adapter.sh",
        repo_root / "adapters/copilot-cli/copilot-cli-adapter.ps1",
        repo_root / "Makefile",
    )

    for path in files:
        content = path.read_text(encoding="utf-8")
        assert "servers.json" not in content


@pytest.mark.unit
def test_copilot_integration_does_not_reference_removed_mcp_suite(repo_root: Path):
    makefile = (repo_root / "Makefile").read_text(encoding="utf-8")

    assert "command -v mcp" not in makefile
    assert "copilot-mcp-test.bats" not in makefile
    assert not (repo_root / "tests/integration/copilot-mcp-test.bats").exists()
