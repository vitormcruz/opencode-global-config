"""Testes do harness Copilot CLI: adapter, conversoes e wrapper CLI."""

from pathlib import Path
import re

import pytest

from opencode_config.harnesses.copilot import CopilotAdapter


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
    # curador-produto spawna apenas eng-software (task: eng-software:
    # allow); a allowlist publicada na prosa reflete exatamente isso.
    assert "Delegacao de subagentes" in agent
    assert "`eng-software`" in agent
    assert "dba, eng-software, front, qa, rev, sec" not in agent
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
        'tools: ["read", "edit", "execute", "search", "web", "agent", '
        '"ask_user"]'
        in agent
    )


@pytest.mark.parametrize("question_permission", ["allow", None, "deny"])
@pytest.mark.unit
def test_copilot_adapter_maps_question_permission_to_ask_user(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    question_permission: str | None,
) -> None:
    repo = tmp_path / "repo"
    agents = repo / "harness-conf" / "agents"
    agents.mkdir(parents=True)
    (repo / "harness-conf" / "commands").mkdir()
    (repo / "harness-conf" / "skills").mkdir()
    (repo / "harness-conf" / "opencode.json").write_text("{}", encoding="utf-8")
    (repo / ".github").mkdir()
    question_line = (
        f"  question: {question_permission}\n"
        if question_permission is not None
        else ""
    )
    (agents / "planner.md").write_text(
        """---
description: Planner
permission:
  edit: deny
  bash: deny
  webfetch: deny
  websearch: deny
{question_line}---
Planner
""".format(question_line=question_line),
        encoding="utf-8",
    )

    status, _, error = run_adapter(monkeypatch, repo, tmp_path)

    assert status == 0
    assert error == ""
    agent = (tmp_path / ".copilot" / "agents" / "planner.agent.md").read_text(
        encoding="utf-8"
    )
    assert ("ask_user" in agent) is (question_permission == "allow")


@pytest.mark.unit
def test_copilot_adapter_mirrors_mode_semantics(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    """Espelha a semântica de modos OpenCode no frontmatter Copilot.

    primary -> disable-model-invocation: true (não spawnável via task);
    subagent -> user-invocable: false (não invocável direto pelo
    usuário); all -> nenhuma das duas propriedades.
    """

    status, _, error = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    assert error == ""
    agents_dir = tmp_path / ".copilot" / "agents"

    devflow = (agents_dir / "devflow.agent.md").read_text(encoding="utf-8")
    assert "disable-model-invocation: true" in devflow
    assert "user-invocable: false" not in devflow

    revisor_historia = (
        agents_dir / "revisor-historia.agent.md"
    ).read_text(encoding="utf-8")
    assert "user-invocable: false" in revisor_historia
    assert "disable-model-invocation: true" not in revisor_historia

    eng_software = (agents_dir / "eng-software.agent.md").read_text(
        encoding="utf-8"
    )
    assert "disable-model-invocation: true" not in eng_software
    assert "user-invocable: false" not in eng_software


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
        "doc-readme-template.md"
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
def test_copilot_adapter_excludes_opencode_only_agents_from_delegation_prose(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    """A prosa de delegação não cita agentes que não existem no Copilot.

    smart-planner tem ``"*": allow`` e publica todo o vocabulário
    disponível; worker e revisor são OpenCode-only e devem ficar fora.
    """

    status, _, error = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    assert error == ""
    agent = (
        tmp_path / ".copilot" / "agents" / "smart-planner.agent.md"
    ).read_text(encoding="utf-8")
    assert "Delegacao de subagentes" in agent
    prose = re.search(
        r"estes `agent_type` Copilot:\n+`([^`]*)`", agent
    )
    assert prose is not None, "Prosa de delegação ausente"
    entries = {name.strip() for name in prose.group(1).split(",")}
    assert "eng-software" in entries
    assert "revisor-historia" in entries
    assert "worker" not in entries
    assert "revisor" not in entries


@pytest.mark.unit
def test_copilot_adapter_prunes_orphan_managed_agents(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Prune remove `.agent.md` de nomes historicamente gerenciados.

    Órfão conhecido (nome na lista histórica, ausente do repo) é
    removido com backup; arquivo do usuário com nome fora da lista
    permanece intacto.
    """

    repo = tmp_path / "repo"
    agents = repo / "harness-conf" / "agents"
    agents.mkdir(parents=True)
    (repo / "harness-conf" / "commands").mkdir()
    (repo / "harness-conf" / "skills").mkdir()
    (repo / "harness-conf" / "opencode.json").write_text("{}", encoding="utf-8")
    (repo / ".github").mkdir()
    (agents / "planner.md").write_text(
        "---\ndescription: Planner\nmode: all\n---\nPlanner\n",
        encoding="utf-8",
    )

    agents_dir = tmp_path / ".copilot" / "agents"
    agents_dir.mkdir(parents=True)
    orphan = agents_dir / "dba.agent.md"
    orphan.write_text("conteudo antigo", encoding="utf-8")
    user_file = agents_dir / "meu-agente-custom.agent.md"
    user_file.write_text("criado pelo usuario", encoding="utf-8")

    status, _, error = run_adapter(monkeypatch, repo, tmp_path)

    assert status == 0
    assert error == ""
    assert not orphan.exists()
    assert user_file.is_file()
    assert user_file.read_text(encoding="utf-8") == "criado pelo usuario"
    assert (agents_dir / "planner.agent.md").is_file()
    backup_root = tmp_path / ".config" / "copilot-backup"
    backups = list(backup_root.rglob("dba.agent.md"))
    assert backups and backups[0].read_text(encoding="utf-8") == (
        "conteudo antigo"
    )


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


@pytest.mark.unit
def test_factory_returns_both_adapters_when_selected() -> None:
    from opencode_config.harnesses import criar_adapters
    from opencode_config.harnesses.opencode import OpenCodeAdapter
    from opencode_config.lib.environment import EnvironmentKind

    adapters = criar_adapters(
        EnvironmentKind.LINUX,
        ["opencode", "copilot"],
    )

    assert [adapter.name for adapter in adapters] == ["opencode", "copilot"]
    assert isinstance(adapters[0], OpenCodeAdapter)
    assert isinstance(adapters[1], CopilotAdapter)


@pytest.mark.unit
def test_copilot_installed_uses_path_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from opencode_config.lib.environment import EnvironmentKind

    adapter = CopilotAdapter()
    monkeypatch.setattr(
        "opencode_config.harnesses.copilot.shutil.which",
        lambda command, **_kwargs: f"/usr/bin/{command}",
    )
    assert adapter.installed(EnvironmentKind.WSL) is True

    monkeypatch.setattr(
        "opencode_config.harnesses.copilot.shutil.which",
        lambda _command, **_kwargs: None,
    )
    assert adapter.installed(EnvironmentKind.WSL) is False
