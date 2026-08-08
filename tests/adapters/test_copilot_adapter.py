from pathlib import Path

import pytest


def run_adapter(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
    dest_root: Path,
    arguments: list[str] | None = None,
) -> tuple[int, str, str]:
    from opencode_config.adapters import copilot

    monkeypatch.setenv("HOME", str(dest_root))
    monkeypatch.setenv("USERPROFILE", str(dest_root))
    cli_arguments = [
        *(arguments or ["--yes", "--quiet"]),
        "--repo-root",
        str(repo_root),
        "--dest-root",
        str(dest_root),
    ]
    return copilot.run_cli(cli_arguments)


@pytest.mark.unit
def test_copilot_adapter_converts_agent_frontmatter(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    status, _, error = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    assert error == ""
    agent = (
        tmp_path / ".copilot" / "agents" / "eng-software.agent.md"
    ).read_text(encoding="utf-8")
    assert 'tools: ["read", "edit", "execute", "search"]' in agent
    assert "temperature:" not in agent


@pytest.mark.unit
def test_copilot_adapter_marks_subagent_not_user_invocable(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    status, _, _ = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    agent = (
        tmp_path / ".copilot" / "agents" / "revisor-historia.agent.md"
    ).read_text(encoding="utf-8")
    assert "user-invocable: false" in agent


@pytest.mark.unit
def test_copilot_adapter_converts_commands_to_skills(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    status, _, _ = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    for name in ("index-codebase", "bench-indexing", "sync-upstream-skills"):
        skill = tmp_path / ".copilot" / "skills" / name / "SKILL.md"
        assert skill.is_file()
        assert f"name: {name}" in skill.read_text(encoding="utf-8")


@pytest.mark.unit
def test_copilot_adapter_adds_skill_frontmatter(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    status, _, _ = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    skill = (
        tmp_path / ".copilot" / "skills" / "browser-testing" / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "name: browser-testing" in skill
    assert "description:" in skill


@pytest.mark.unit
def test_copilot_adapter_preserves_skill_content_without_path_rewrite(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    status, _, _ = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    source = (
        repo_root / "skills" / "web-research-exa-crawl4ai" / "SKILL.md"
    )
    copied = (
        tmp_path
        / ".copilot"
        / "skills"
        / "web-research-exa-crawl4ai"
        / "SKILL.md"
    )
    assert copied.read_text(encoding="utf-8") == source.read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_copilot_adapter_copies_default_artifacts_and_avoids_legacy_targets(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    status, _, _ = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    assert (
        tmp_path / ".copilot" / "agents" / "default-artifacts" /
        "doc-readme.md"
    ).is_file()
    assert not (tmp_path / ".vscode-server").exists()
    assert not (tmp_path / ".copilot" / "agents" / "eng-software.md").exists()
    assert not (tmp_path / ".copilot" / "commands").exists()


@pytest.mark.unit
def test_copilot_adapter_does_not_create_mcp_configuration(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    status, _, _ = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    assert not (tmp_path / ".config" / "mcp" / "servers.json").exists()


@pytest.mark.unit
def test_copilot_adapter_backups_existing_destinations(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    existing = tmp_path / ".copilot" / "skills" / "browser-testing"
    existing.mkdir(parents=True)
    (existing / "SKILL.md").write_text("old", encoding="utf-8")

    status, _, _ = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    backup_root = tmp_path / ".config" / "copilot-backup"
    backup_dirs = list(backup_root.iterdir())
    assert len(backup_dirs) == 1
    assert (
        backup_dirs[0] / "browser-testing" / "SKILL.md"
    ).read_text(encoding="utf-8") == "old"


@pytest.mark.unit
def test_copilot_adapter_rejects_invalid_skill_name(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    (repo / "agents").mkdir(parents=True)
    (repo / "commands").mkdir()
    (repo / "skills" / "Invalid_Name").mkdir(parents=True)
    (repo / "skills" / "Invalid_Name" / "SKILL.md").write_text(
        "# Invalid",
        encoding="utf-8",
    )
    (repo / "opencode.json").write_text("{}", encoding="utf-8")
    (repo / ".github").mkdir()

    status, _, error = run_adapter(monkeypatch, repo, tmp_path)

    assert status != 0
    assert "invalid" in error.lower()


@pytest.mark.unit
def test_copilot_adapter_help_returns_success(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from opencode_config.adapters import copilot

    status = copilot.main(["--help"])

    captured = capsys.readouterr()
    assert status == 0
    assert "copilot-adapter" in captured.out
    assert captured.err == ""


@pytest.mark.unit
def test_project_registers_copilot_adapter_entrypoint(repo_root: Path) -> None:
    pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8")

    assert (
        'opencode-copilot-adapter = "opencode_config.adapters.copilot:main"'
        in pyproject
    )


@pytest.mark.unit
def test_bootstrap_invokes_python_copilot_adapter(repo_root: Path) -> None:
    bootstrap = (
        repo_root / "scripts/bootstrap_repo/configurar-repo.sh"
    ).read_text(encoding="utf-8")

    assert "adapters/copilot-cli/copilot-cli-adapter.sh" not in bootstrap
    assert "opencode_config.bootstrap.main" in bootstrap
