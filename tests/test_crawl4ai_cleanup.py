import io

import pytest


@pytest.mark.unit
def test_crawl4ai_legacy_tree_and_orphaned_doctree_suite_are_removed(repo_root):
    assert not (repo_root / "scripts/crawl4ai").exists()
    assert not (repo_root / "tests/scripts/crawl4ai").exists()
    assert not (repo_root / "tests/scripts/doctree").exists()


@pytest.mark.unit
def test_make_test_tools_does_not_reference_removed_crawl4ai_suite(repo_root):
    assert not (repo_root / "Makefile").exists()


@pytest.mark.unit
def test_bootstrap_does_not_orchestrate_removed_crawl4ai_installer(repo_root):
    bootstrap = (
        repo_root / "scripts/bootstrap_repo/configurar-repo.sh"
    ).read_text(encoding="utf-8"    )

    assert "install-crawl4ai-mcp.sh" not in bootstrap
    assert "run_crawl4ai" not in bootstrap


@pytest.mark.unit
def test_bootstrap_removes_legacy_crawl4ai_bashrc_block(
    repo_root, tmp_path, monkeypatch
):
    home = tmp_path / "home"
    home.mkdir()
    bashrc = home / ".bashrc"
    bashrc.write_text(
        "before\n"
        "# Crawl4AI MCP - INICIO\n"
        "export CRAWL4AI_API_TOKEN=legacy\n"
        "# Crawl4AI MCP - FIM\n"
        "after\n",
        encoding="utf-8",
    )

    from opencode_config.bootstrap import main as bootstrap_main

    # No mesmo processo para que o fake_winreg autouse proteja o PATH real.
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("OPENCODE_SKIP_DEPS", "1")
    monkeypatch.setenv("OPENCODE_SKIP_COPILOT_ADAPTER", "1")
    monkeypatch.setenv("OPENCODE_SKIP_OPENCODE_ADAPTER", "1")
    status = bootstrap_main.run(
        ["--quiet", "--repo-root", str(repo_root)],
        output=io.StringIO(),
        error=io.StringIO(),
    )

    assert status == 0
    assert "Crawl4AI MCP" not in bashrc.read_text(encoding="utf-8")
    assert "CRAWL4AI_API_TOKEN" not in bashrc.read_text(encoding="utf-8")
