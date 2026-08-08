"""Valida a estrutura estatica do repositorio."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


pytestmark = pytest.mark.unit


def test_agents_file_exists(repo_root: Path) -> None:
    assert (repo_root / "AGENTS.md").is_file()


def test_opencode_json_exists(repo_root: Path) -> None:
    assert (repo_root / "opencode.json").is_file()


def test_readme_file_exists(repo_root: Path) -> None:
    assert (repo_root / "README.md").is_file()


def test_agents_directory_exists(repo_root: Path) -> None:
    assert (repo_root / "agents").is_dir()


def test_commands_directory_exists(repo_root: Path) -> None:
    assert (repo_root / "commands").is_dir()


def test_skills_directory_exists(repo_root: Path) -> None:
    assert (repo_root / "skills").is_dir()


def test_scripts_directory_exists(repo_root: Path) -> None:
    assert (repo_root / "scripts").is_dir()


def test_doc_extract_skill_exists(repo_root: Path) -> None:
    assert (repo_root / "skills/doc-extract/SKILL.md").is_file()


def test_md_export_skill_exists(repo_root: Path) -> None:
    assert (repo_root / "skills/md-export/SKILL.md").is_file()


def test_svg_to_image_skill_exists(repo_root: Path) -> None:
    assert (repo_root / "skills/svg-to-image/SKILL.md").is_file()


def test_prompt_improver_skill_exists(repo_root: Path) -> None:
    assert (repo_root / "skills/prompt-improver/SKILL.md").is_file()


def test_web_research_skill_exists(repo_root: Path) -> None:
    assert (
        repo_root / "skills/web-research-exa-crawl4ai/SKILL.md"
    ).is_file()


def test_aws_add_account_sso_skill_exists(repo_root: Path) -> None:
    assert (repo_root / "skills/aws-add-account-sso/SKILL.md").is_file()


def test_aws_sso_login_skill_exists(repo_root: Path) -> None:
    assert (repo_root / "skills/aws-sso-login/SKILL.md").is_file()


def test_all_skill_directories_have_skill_file(repo_root: Path) -> None:
    skill_directories = list((repo_root / "skills").glob("*/"))
    missing = [
        skill_dir
        for skill_dir in skill_directories
        if not (skill_dir / "SKILL.md").is_file()
    ]

    if not skill_directories:
        missing.append(repo_root / "skills/*/")
    assert not missing, f"SKILL.md ausente em: {missing[0]}"


@pytest.mark.parametrize(
    "skill_name",
    (
        "test-driven-development",
        "code-review-and-quality",
        "code-simplification",
        "security-and-hardening",
        "documentation-and-adrs",
        "debugging-and-error-recovery",
        "git-workflow-and-versioning",
        "spec-driven-development",
        "planning-and-task-breakdown",
        "api-and-interface-design",
        "performance-optimization",
        "frontend-ui-engineering",
    ),
)
def test_addyosmani_skill_has_skill_and_upstream_files(
    repo_root: Path,
    skill_name: str,
) -> None:
    skill_dir = repo_root / "skills" / skill_name
    assert (skill_dir / "SKILL.md").is_file()
    assert (skill_dir / "UPSTREAM.md").is_file()


def test_test_driven_development_has_testing_patterns(repo_root: Path) -> None:
    assert (
        repo_root
        / "skills/test-driven-development/references/testing-patterns.md"
    ).is_file()


def test_security_hardening_has_security_checklist(repo_root: Path) -> None:
    assert (
        repo_root
        / "skills/security-and-hardening/references/security-checklist.md"
    ).is_file()


def test_performance_optimization_has_performance_checklist(
    repo_root: Path,
) -> None:
    assert (
        repo_root
        / "skills/performance-optimization/references/performance-checklist.md"
    ).is_file()


def test_frontend_ui_engineering_has_accessibility_checklist(
    repo_root: Path,
) -> None:
    assert (
        repo_root
        / "skills/frontend-ui-engineering/references/accessibility-checklist.md"
    ).is_file()


def test_accessibility_audit_has_skill_and_upstream_files(
    repo_root: Path,
) -> None:
    skill_dir = repo_root / "skills/accessibility-audit"
    assert (skill_dir / "SKILL.md").is_file()
    assert (skill_dir / "UPSTREAM.md").is_file()


def test_accessibility_audit_has_implementation_playbook(
    repo_root: Path,
) -> None:
    assert (
        repo_root
        / "skills/accessibility-audit/resources/implementation-playbook.md"
    ).is_file()


def _count_matching_lines(path: Path, text: str) -> int:
    return sum(
        text in line
        for line in path.read_text(encoding="utf-8").splitlines()
    )


def _assert_frontmatter(path: Path) -> None:
    count = sum(
        line == "---"
        for line in path.read_text(encoding="utf-8").splitlines()
    )
    assert count >= 1
    assert count >= 2


def test_dba_agent_has_frontmatter(repo_root: Path) -> None:
    _assert_frontmatter(repo_root / "agents/dba.md")


def test_analista_agent_has_frontmatter(repo_root: Path) -> None:
    _assert_frontmatter(repo_root / "agents/analista.md")


def test_aws_analista_agent_has_frontmatter(repo_root: Path) -> None:
    _assert_frontmatter(repo_root / "agents/aws-analista.md")


def test_revisor_historia_agent_has_frontmatter(repo_root: Path) -> None:
    _assert_frontmatter(repo_root / "agents/revisor-historia.md")


def test_all_agents_have_description(repo_root: Path) -> None:
    agent_files = list((repo_root / "agents").glob("*.md"))
    missing = [
        agent
        for agent in agent_files
        if not any(
            line.startswith("description:")
            for line in agent.read_text(encoding="utf-8").splitlines()
        )
    ]

    if not agent_files:
        missing.append(repo_root / "agents/*.md")
    assert not missing, f"description ausente em: {missing[0]}"


def _strip_jsonc_line_comments(source: str) -> str:
    result: list[str] = []
    in_string = False
    index = 0
    while index < len(source):
        character = source[index]
        if not in_string and character == '"':
            in_string = True
            result.append(character)
            index += 1
            continue
        if in_string and character == "\\":
            result.append(character)
            if index + 1 < len(source):
                result.append(source[index + 1])
            index += 2
            continue
        if in_string and character == '"':
            in_string = False
            result.append(character)
            index += 1
            continue
        if (
            not in_string
            and character == "/"
            and index + 1 < len(source)
            and source[index + 1] == "/"
        ):
            while index < len(source) and source[index] != "\n":
                index += 1
            continue
        result.append(character)
        index += 1
    return "".join(result)


def _jsonc_validation_output(path: Path) -> tuple[bool, str]:
    try:
        json.loads(
            _strip_jsonc_line_comments(path.read_text(encoding="utf-8"))
        )
    except (OSError, ValueError):
        return False, ""
    return True, "valid"


def test_opencode_json_is_valid_jsonc(repo_root: Path) -> None:
    success, output = _jsonc_validation_output(repo_root / "opencode.json")

    assert success
    assert output == "valid"


def test_bootstrap_script_is_executable(repo_root: Path) -> None:
    path = repo_root / "scripts/bootstrap_repo/configurar-repo.sh"
    assert path.is_file() and os.access(path, os.X_OK)


def test_opencode_python_adapter_exists(repo_root: Path) -> None:
    assert (repo_root / "src/opencode_config/adapters/opencode.py").is_file()


def test_legacy_dependency_script_is_removed(repo_root: Path) -> None:
    assert not (repo_root / "scripts/bootstrap_repo/wsl-install-deps.sh").exists()


def test_powershell_bootstrap_script_exists(repo_root: Path) -> None:
    assert (repo_root / "scripts/bootstrap_repo/configurar-repo.ps1").is_file()


def test_copilot_python_adapter_exists(repo_root: Path) -> None:
    assert (repo_root / "src/opencode_config/adapters/copilot.py").is_file()


def test_code_explorer_priority_skill_exists(repo_root: Path) -> None:
    assert (
        repo_root / "skills/code-explorer-priority/SKILL.md"
    ).is_file()


def test_code_explorer_priority_skill_has_frontmatter(
    repo_root: Path,
) -> None:
    _assert_frontmatter(
        repo_root / "skills/code-explorer-priority/SKILL.md"
    )


def test_agents_mentions_code_discovery_documentation(repo_root: Path) -> None:
    count = _count_matching_lines(
        repo_root / "AGENTS.md",
        "Descoberta de Código e Documentação",
    )
    assert count >= 1
    assert count >= 1


def test_agents_mentions_codebase_memory_cli(repo_root: Path) -> None:
    count = _count_matching_lines(
        repo_root / "AGENTS.md",
        "codebase-memory CLI (CÓDIGO)",
    )
    assert count >= 1
    assert count >= 1


def test_agents_mentions_client_access(repo_root: Path) -> None:
    count = _count_matching_lines(repo_root / "AGENTS.md", "Acesso por cliente")
    assert count >= 1
    assert count >= 1


def test_agents_mentions_required_recovery(repo_root: Path) -> None:
    count = _count_matching_lines(repo_root / "AGENTS.md", "Recovery obrigatório")
    assert count >= 1
    assert count >= 1
