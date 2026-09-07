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
    assert 'tools: ["read", "edit", "execute", "search", "web"]' in agent
    assert "temperature:" not in agent


@pytest.mark.unit
def test_copilot_adapter_maps_task_permissions_to_copilot_agent_types(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    status, _, error = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    assert error == ""
    agent = (
        tmp_path / ".copilot" / "agents" / "curador-produto.agent.md"
    ).read_text(encoding="utf-8")
    assert "name: curador-produto" in agent
    assert "dba, eng-software, front, qa, rev, sec" not in agent
    assert "Delegacao de subagentes" not in agent
    assert "gpt-5.6-luna" not in agent


@pytest.mark.unit
def test_copilot_adapter_hides_agent_tool_when_task_allowlist_has_only_model_ids(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    agents = repo / "harness-conf" / "agents"
    agents.mkdir(parents=True)
    (repo / "harness-conf" / "commands").mkdir()
    (repo / "harness-conf" / "skills").mkdir()
    (repo / "harness-conf" / "opencode.json").write_text("{}", encoding="utf-8")
    (repo / ".github").mkdir()
    (agents / "planner.md").write_text(
        """---
description: Planner
permission:
  edit: deny
  bash: deny
  webfetch: deny
  websearch: deny
  task:
    gpt-5.6-luna: allow
    "*": deny
---
Planner
""",
        encoding="utf-8",
    )

    status, _, error = run_adapter(monkeypatch, repo, tmp_path)

    assert status == 0
    assert error == ""
    agent = (
        tmp_path / ".copilot" / "agents" / "planner.agent.md"
    ).read_text(encoding="utf-8")
    assert 'tools: ["read", "search"]' in agent
    assert "gpt-5.6-luna" not in agent


@pytest.mark.unit
def test_copilot_adapter_keeps_builtin_agent_type_in_task_allowlist(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    agents = repo / "harness-conf" / "agents"
    agents.mkdir(parents=True)
    (repo / "harness-conf" / "commands").mkdir()
    (repo / "harness-conf" / "skills").mkdir()
    (repo / "harness-conf" / "opencode.json").write_text("{}", encoding="utf-8")
    (repo / ".github").mkdir()
    (agents / "planner.md").write_text(
        """---
description: Planner
permission:
  edit: deny
  bash: deny
  webfetch: deny
  websearch: deny
  task:
    explore: allow
    gpt-5.6-luna: allow
    "*": deny
---
Planner
""",
        encoding="utf-8",
    )

    status, _, error = run_adapter(monkeypatch, repo, tmp_path)

    assert status == 0
    assert error == ""
    agent = (
        tmp_path / ".copilot" / "agents" / "planner.agent.md"
    ).read_text(encoding="utf-8")
    assert 'tools: ["read", "search", "agent"]' in agent
    assert "`explore`" in agent
    assert "gpt-5.6-luna" not in agent


@pytest.mark.unit
def test_copilot_adapter_materializes_inherited_agent_permissions(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    status, _, error = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    assert error == ""
    agent = (
        tmp_path / ".copilot" / "agents" / "aws-analista.agent.md"
    ).read_text(encoding="utf-8")
    assert 'tools: ["read", "execute", "search", "web", "agent"]' in agent


@pytest.mark.unit
def test_copilot_adapter_materializes_smart_planner_subagent_capability(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    status, _, error = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    assert error == ""
    agent = (
        tmp_path / ".copilot" / "agents" / "smart-planner.agent.md"
    ).read_text(encoding="utf-8")
    assert (
        'tools: ["read", "edit", "execute", "search", "web", "agent"]'
        in agent
    )


@pytest.mark.unit
def test_copilot_adapter_revisor_historia_is_primary(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    status, _, _ = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    agent = (
        tmp_path / ".copilot" / "agents" / "revisor-historia.agent.md"
    ).read_text(encoding="utf-8")
    assert "user-invocable: false" not in agent


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
def test_copilot_adapter_copies_question_orchestration_skill(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    status, _, _ = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    skill = (
        tmp_path
        / ".copilot"
        / "skills"
        / "question-orchestration"
        / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "name: question-orchestration" in skill
    assert "question-orchestration" in skill


@pytest.mark.unit
def test_copilot_adapter_preserves_skill_content_without_path_rewrite(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    status, _, _ = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    source = (
        repo_root / "harness-conf" / "skills" / "web-research-exa-crawl4ai" / "SKILL.md"
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
    (repo / "harness-conf" / "agents").mkdir(parents=True)
    (repo / "harness-conf" / "commands").mkdir()
    (repo / "harness-conf" / "skills" / "Invalid_Name").mkdir(parents=True)
    (repo / "harness-conf" / "skills" / "Invalid_Name" / "SKILL.md").write_text(
        "# Invalid",
        encoding="utf-8",
    )
    (repo / "harness-conf" / "opencode.json").write_text("{}", encoding="utf-8")
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


@pytest.mark.unit
def test_copilot_adapter_skips_opencode_only_agents(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    status, _, error = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    assert error == ""
    assert not (
        tmp_path / ".copilot" / "agents" / "worker.agent.md"
    ).exists()
    assert not (
        tmp_path / ".copilot" / "agents" / "revisor.agent.md"
    ).exists()


@pytest.mark.unit
def test_copilot_adapter_does_not_skip_regular_agents(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    status, _, error = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    assert error == ""
    assert (
        tmp_path / ".copilot" / "agents" / "eng-software.agent.md"
    ).is_file()
    assert (
        tmp_path / ".copilot" / "agents" / "curador-produto.agent.md"
    ).is_file()


@pytest.mark.unit
def test_copilot_adapter_copies_agents_base_as_global_agents_md(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    status, _, error = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    assert error == ""
    global_agents = (tmp_path / ".copilot" / "AGENTS.md").read_text(
        encoding="utf-8"
    )
    base = (
        repo_root / "harness-conf" / "AGENTS.base.md"
    ).read_text(encoding="utf-8")
    assert global_agents.rstrip("\n") == base.rstrip("\n")
    assert "# Regras Globais" in global_agents
