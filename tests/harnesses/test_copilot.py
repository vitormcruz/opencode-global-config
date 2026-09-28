"""Testes do harness Copilot CLI: adapter, conversoes e wrapper CLI."""

import json
from fnmatch import fnmatchcase
from pathlib import Path
import re

import pytest

from opencode_config.harnesses.copilot import CopilotAdapter
from opencode_config.harnesses import ApplyOptions


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
def test_copilot_adapter_describes_agents_md_optimization_command(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    status, _, error = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    assert error == ""
    skill = (
        tmp_path
        / ".copilot"
        / "skills"
        / "otimizar-agents-md"
        / "SKILL.md"
    ).read_text(encoding="utf-8")

    assert "Analisa e otimiza arquivos AGENTS.md" in skill
    assert "Executa o comando otimizar-agents-md." not in skill


@pytest.mark.unit
def test_copilot_adapter_adds_skill_frontmatter(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    status, _, _ = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    skill = (
        tmp_path
        / ".copilot"
        / "referencias"
        / "skills"
        / "browser-testing"
        / "SKILL.md"
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
    assert not (
        tmp_path
        / ".copilot"
        / "referencias"
        / "skills"
        / "question-orchestration"
    ).exists()


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
    assert not (
        tmp_path
        / ".copilot"
        / "referencias"
        / "skills"
        / "web-research-exa-crawl4ai"
    ).exists()


@pytest.mark.unit
def test_copilot_adapter_generates_skill_references_only_for_allowed_agents(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo com espaços"
    harness_dir = repo_root / "harness-conf"
    agents_dir = harness_dir / "agents"
    skills_dir = harness_dir / "skills"
    agents_dir.mkdir(parents=True)
    (harness_dir / "commands").mkdir()
    skill_directory = skills_dir / "architecture-skill"
    skill_directory.mkdir(parents=True)
    (harness_dir / "opencode.json").write_text(
        json.dumps(
            {"permission": {"skill": {"architecture-skill": "deny"}}}
        ),
        encoding="utf-8",
    )
    skill_source = skill_directory / "SKILL.md"
    skill_source.write_text(
        "---\n"
        "name: architecture-skill\n"
        "description: >\n"
        "  Descrição completa da skill, com detalhes que não podem ser\n"
        "  truncados durante a geração do perfil. Frase final verificável.\n"
        "---\n\n"
        "EXTERNAL_SKILL_BODY_MARKER\n",
        encoding="utf-8",
    )
    allowed_agent = agents_dir / "planner.md"
    allowed_agent.write_text(
        "---\n"
        "description: Planner\n"
        "permission:\n"
        "  skill:\n"
        "    architecture-skill: allow\n"
        "---\n\n"
        "Corpo original do perfil.\n",
        encoding="utf-8",
    )
    agent_without_allow = agents_dir / "reader.md"
    agent_without_allow.write_text(
        "---\n"
        "description: Reader\n"
        "permission:\n"
        "  edit: deny\n"
        "---\n\n"
        "Corpo original do leitor.\n",
        encoding="utf-8",
    )
    destination_root = tmp_path / "home com espaços"

    status, _, error = run_adapter(
        monkeypatch,
        repo_root,
        destination_root,
    )

    assert status == 0
    assert error == ""
    copied_agents = destination_root / ".copilot" / "agents"
    planner = (copied_agents / "planner.agent.md").read_text(encoding="utf-8")
    reader = (copied_agents / "reader.agent.md").read_text(encoding="utf-8")
    source_planner = allowed_agent.read_text(encoding="utf-8")
    begin_marker = "<!-- BEGIN COPILOT GENERATED SKILLS -->"
    end_marker = "<!-- END COPILOT GENERATED SKILLS -->"

    assert begin_marker in planner
    assert end_marker in planner
    generated_block = planner.split(begin_marker, maxsplit=1)[1].split(
        end_marker,
        maxsplit=1,
    )[0]
    assert "architecture-skill" in generated_block
    expected_description = (
        "Descrição completa da skill, com detalhes que não podem ser truncados "
        "durante a geração do perfil. Frase final verificável."
    )
    assert expected_description in generated_block
    expected_skill_path = (
        destination_root.resolve()
        / ".copilot"
        / "referencias"
        / "skills"
        / "architecture-skill"
        / "SKILL.md"
    )
    assert expected_skill_path.is_file()
    assert str(expected_skill_path) in generated_block
    assert "~/.copilot" not in generated_block
    assert "EXTERNAL_SKILL_BODY_MARKER" not in generated_block
    assert begin_marker not in source_planner
    assert end_marker not in source_planner
    assert begin_marker not in reader
    assert end_marker not in reader


@pytest.mark.unit
def test_copilot_adapter_routes_skills_from_global_permissions(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    status, _, error = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    assert error == ""
    harness_dir = repo_root / "harness-conf"
    source_skills = {
        path.name
        for path in (harness_dir / "skills").iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    }
    global_deny = json.loads(
        (harness_dir / "opencode.json").read_text(encoding="utf-8")
    )["permission"]["skill"]
    domain_skills = {
        name
        for name in source_skills
        if any(
            action == "deny" and fnmatchcase(name, pattern)
            for pattern, action in global_deny.items()
        )
    }
    global_skills = source_skills - domain_skills

    copilot_skills = tmp_path / ".copilot" / "skills"
    auxiliary_skills = tmp_path / ".copilot" / "referencias" / "skills"
    discovered_source_skills = source_skills & {
        path.name for path in copilot_skills.iterdir() if path.is_dir()
    }
    auxiliary_source_skills = {
        path.name for path in auxiliary_skills.iterdir() if path.is_dir()
    }

    assert len(global_skills) == 10
    assert len(domain_skills) == 23
    assert global_skills.isdisjoint(domain_skills)
    assert global_skills | domain_skills == source_skills
    assert discovered_source_skills == global_skills
    assert auxiliary_source_skills == domain_skills


@pytest.mark.unit
def test_copilot_adapter_changes_skill_destination_when_global_deny_changes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    harness_dir = repo_root / "harness-conf"
    skills_dir = harness_dir / "skills"
    (harness_dir / "agents" / "default-artifacts").mkdir(parents=True)
    (harness_dir / "commands").mkdir()
    skills_dir.mkdir()
    (harness_dir / "AGENTS.base.md").write_text("# Agents\n", encoding="utf-8")
    for skill_name in ("global-skill", "domain-skill"):
        skill_dir = skills_dir / skill_name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            f"# {skill_name}\nDescription for {skill_name}.\n",
            encoding="utf-8",
        )

    config_path = harness_dir / "opencode.json"
    config_path.write_text(
        json.dumps({"permission": {"skill": {"domain-skill": "deny"}}}),
        encoding="utf-8",
    )
    first_destination = tmp_path / "first"
    status, _, error = run_adapter(
        monkeypatch, repo_root, first_destination
    )

    assert status == 0
    assert error == ""
    assert (first_destination / ".copilot" / "skills" / "global-skill").is_dir()
    assert not (
        first_destination / ".copilot" / "skills" / "domain-skill"
    ).exists()
    assert (
        first_destination
        / ".copilot"
        / "referencias"
        / "skills"
        / "domain-skill"
    ).is_dir()

    config_path.write_text(
        json.dumps({"permission": {"skill": {"global-skill": "deny"}}}),
        encoding="utf-8",
    )
    second_destination = tmp_path / "second"
    status, _, error = run_adapter(
        monkeypatch, repo_root, second_destination
    )

    assert status == 0
    assert error == ""
    assert not (
        second_destination / ".copilot" / "skills" / "global-skill"
    ).exists()
    assert (second_destination / ".copilot" / "skills" / "domain-skill").is_dir()
    assert (
        second_destination
        / ".copilot"
        / "referencias"
        / "skills"
        / "global-skill"
    ).is_dir()


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
    existing = (
        tmp_path
        / ".copilot"
        / "skills"
        / "browser-testing"
    )
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
    assert (
        tmp_path
        / ".copilot"
        / "referencias"
        / "skills"
        / "browser-testing"
        / "SKILL.md"
    ).is_file()
    assert not (
        tmp_path / ".copilot" / "skills" / "browser-testing"
    ).exists()


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

    smart-planner usa ``"*": deny`` com lista nomeada de
    delegação, que inclui worker e revisor (OpenCode-only);
    a prosa do adapter deve excluí-los.
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
def test_copilot_adapter_merges_ai_memory_without_losing_existing_servers(
    monkeypatch: pytest.MonkeyPatch,
    fake_repo,
    tmp_path: Path,
) -> None:
    repo_root = fake_repo(
        {
            "harness-conf/agents/planner.md": "---\ndescription: Planner\n---\n",
            "harness-conf/commands/example.md": "# Example\n",
            "harness-conf/skills/global/SKILL.md": "# Global\n",
            "harness-conf/opencode.json": json.dumps(
                {
                    "mcp": {
                        "ai-memory": {
                            "type": "remote",
                            "url": "http://127.0.0.1:49374/mcp",
                        }
                    }
                }
            ),
        }
    )
    ready_marker = (
        tmp_path / ".local" / "share" / "ai-memory" / ".bootstrap-provisioned"
    )
    ready_marker.parent.mkdir(parents=True)
    ready_marker.write_text("ready", encoding="utf-8")
    config_path = tmp_path / ".copilot" / "mcp-config.json"
    config_path.parent.mkdir(parents=True)
    preexisting_config = {
        "otherSetting": "preserved",
        "mcpServers": {
            "existing-server": {
                "type": "http",
                "url": "http://127.0.0.1:49375/mcp",
            }
        },
    }
    original_config_content = json.dumps(preexisting_config)
    config_path.write_text(original_config_content, encoding="utf-8")

    status, output, error = run_adapter(
        monkeypatch,
        repo_root,
        tmp_path,
        arguments=["--yes"],
    )

    assert status == 0
    assert error == ""
    merged = json.loads(config_path.read_text(encoding="utf-8"))
    assert merged["otherSetting"] == "preserved"
    assert (
        merged["mcpServers"]["existing-server"]
        == (preexisting_config["mcpServers"]["existing-server"])
    )
    assert merged["mcpServers"]["ai-memory"] == {
        "type": "http",
        "url": "http://127.0.0.1:49374/mcp",
    }
    backups = list(config_path.parent.glob("mcp-config.json.*.bak"))
    assert len(backups) == 1
    backup_path = backups[0]
    assert backup_path.parent == config_path.parent
    assert re.fullmatch(
        r"mcp-config\.json\.\d{8}-\d{6}(?:\.\d+)?\.bak",
        backup_path.name,
    )
    assert backup_path.read_text(encoding="utf-8") == original_config_content
    assert f"Backup da configuração Copilot: {backup_path}" in output


@pytest.mark.unit
def test_copilot_updates_only_its_previous_internal_bridge_endpoint(
    fake_repo,
    tmp_path: Path,
) -> None:
    repo_root = fake_repo(
        {
            "harness-conf/agents/planner.md": "---\ndescription: Planner\n---\n",
            "harness-conf/commands/example.md": "# Example\n",
            "harness-conf/skills/global/SKILL.md": "# Global\n",
            "harness-conf/opencode.json": json.dumps(
                {
                    "mcp": {
                        "ai-memory": {
                            "type": "remote",
                            "url": "http://127.0.0.1:49374/mcp",
                        }
                    }
                }
            ),
        }
    )
    previous_url = "http://172.30.0.2:49374/mcp"
    current_url = "http://172.30.0.3:49374/mcp"
    config_path = tmp_path / ".copilot" / "mcp-config.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "ai-memory": {"type": "http", "url": previous_url},
                    "user-server": {"type": "http", "url": "http://localhost"},
                }
            }
        ),
        encoding="utf-8",
    )

    CopilotAdapter().apply(
        repo_root,
        ApplyOptions(
            home=tmp_path,
            assume_yes=True,
            quiet=True,
            ai_memory_enabled=True,
            ai_memory_url=current_url,
            previous_ai_memory_url=previous_url,
        ),
    )

    merged = json.loads(config_path.read_text(encoding="utf-8"))
    assert merged["mcpServers"]["ai-memory"] == {
        "type": "http",
        "url": current_url,
    }
    assert merged["mcpServers"]["user-server"] == {
        "type": "http",
        "url": "http://localhost",
    }


@pytest.mark.unit
def test_copilot_adapter_removes_ai_memory_entry_when_provisioning_is_incomplete(
    monkeypatch: pytest.MonkeyPatch,
    fake_repo,
    tmp_path: Path,
) -> None:
    repo_root = fake_repo(
        {
            "harness-conf/agents/planner.md": "---\ndescription: Planner\n---\n",
            "harness-conf/commands/example.md": "# Example\n",
            "harness-conf/skills/global/SKILL.md": "# Global\n",
            "harness-conf/opencode.json": "{}",
        }
    )
    config_path = tmp_path / ".copilot" / "mcp-config.json"
    config_path.parent.mkdir(parents=True)
    existing_config = {
        "mcpServers": {
            "ai-memory": {"type": "http", "url": "http://127.0.0.1:49374/mcp"},
            "user-server": {"type": "http", "url": "http://127.0.0.1:49375/mcp"},
        }
    }
    config_path.write_text(json.dumps(existing_config), encoding="utf-8")

    status, _, error = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    assert error == ""
    merged = json.loads(config_path.read_text(encoding="utf-8"))
    assert merged["mcpServers"] == {
        "user-server": existing_config["mcpServers"]["user-server"]
    }
    backups = list(config_path.parent.glob("mcp-config.json.*.bak"))
    assert backups


@pytest.mark.unit
def test_copilot_adapter_rejects_collision_with_a_user_ai_memory_server(
    monkeypatch: pytest.MonkeyPatch,
    fake_repo,
    tmp_path: Path,
) -> None:
    repo_root = fake_repo(
        {
            "harness-conf/agents/planner.md": "---\ndescription: Planner\n---\n",
            "harness-conf/commands/example.md": "# Example\n",
            "harness-conf/skills/global/SKILL.md": "# Global\n",
            "harness-conf/opencode.json": json.dumps(
                {
                    "mcp": {
                        "ai-memory": {
                            "type": "remote",
                            "url": "http://127.0.0.1:49374/mcp",
                        }
                    }
                }
            ),
        }
    )
    ready_marker = (
        tmp_path / ".local" / "share" / "ai-memory" / ".bootstrap-provisioned"
    )
    ready_marker.parent.mkdir(parents=True)
    ready_marker.write_text("ready", encoding="utf-8")
    config_path = tmp_path / ".copilot" / "mcp-config.json"
    config_path.parent.mkdir(parents=True)
    user_server = {"type": "http", "url": "http://remote.example/mcp"}
    config_path.write_text(
        json.dumps({"mcpServers": {"ai-memory": user_server}}),
        encoding="utf-8",
    )

    status, _, error = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 1
    assert "ai-memory" in error
    assert json.loads(config_path.read_text(encoding="utf-8"))["mcpServers"] == {
        "ai-memory": user_server
    }


@pytest.mark.unit
def test_copilot_adapter_keeps_user_ai_memory_entry_when_provisioning_is_disabled(
    monkeypatch: pytest.MonkeyPatch,
    fake_repo,
    tmp_path: Path,
) -> None:
    repo_root = fake_repo(
        {
            "harness-conf/agents/planner.md": "---\ndescription: Planner\n---\n",
            "harness-conf/commands/example.md": "# Example\n",
            "harness-conf/skills/global/SKILL.md": "# Global\n",
            "harness-conf/opencode.json": "{}",
        }
    )
    config_path = tmp_path / ".copilot" / "mcp-config.json"
    config_path.parent.mkdir(parents=True)
    user_server = {"type": "http", "url": "http://remote.example/mcp"}
    config_path.write_text(
        json.dumps({"mcpServers": {"ai-memory": user_server}}),
        encoding="utf-8",
    )

    status, _, error = run_adapter(monkeypatch, repo_root, tmp_path)

    assert status == 0
    assert error == ""
    assert json.loads(config_path.read_text(encoding="utf-8"))["mcpServers"] == {
        "ai-memory": user_server
    }


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
