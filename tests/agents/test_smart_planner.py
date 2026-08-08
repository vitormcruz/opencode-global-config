"""Valida o conteúdo do agente smart-planner e sua restrição no AGENTS.md."""

import re
from pathlib import Path

import pytest


def smart_planner_file(repo_root: Path) -> Path:
    """Retorna o arquivo do agente smart-planner."""

    return repo_root / "agents" / "smart-planner.md"


@pytest.mark.unit
def test_smart_planner_file_exists(repo_root: Path) -> None:
    assert smart_planner_file(repo_root).is_file()


@pytest.mark.unit
def test_smart_planner_frontmatter_has_description(repo_root: Path) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert re.search(r"^description:", content, re.MULTILINE) is not None


@pytest.mark.unit
def test_smart_planner_frontmatter_has_primary_mode(repo_root: Path) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert re.search(r"^mode: primary", content, re.MULTILINE) is not None


@pytest.mark.unit
def test_smart_planner_frontmatter_has_temperature(repo_root: Path) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert re.search(r"^temperature:", content, re.MULTILINE) is not None


@pytest.mark.unit
def test_smart_planner_frontmatter_allows_edit_permission(repo_root: Path) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert re.search(r"edit: allow", content) is not None


@pytest.mark.unit
def test_smart_planner_frontmatter_allows_bash_permission(repo_root: Path) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert re.search(r"bash: allow", content) is not None


@pytest.mark.unit
def test_smart_planner_frontmatter_denies_webfetch_permission(repo_root: Path) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert re.search(r"webfetch: deny", content) is not None


@pytest.mark.unit
def test_smart_planner_frontmatter_denies_task_permission(repo_root: Path) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert re.search(r'"\*": deny', content) is not None


@pytest.mark.unit
def test_smart_planner_has_mode_section(repo_root: Path) -> None:
    assert "## Modo de Opera" in smart_planner_file(repo_root).read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_smart_planner_has_behavioral_restriction_section(
    repo_root: Path,
) -> None:
    assert "## Restri" in smart_planner_file(repo_root).read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_smart_planner_has_incremental_saving_section(repo_root: Path) -> None:
    assert "## Salvamento Incremental" in smart_planner_file(repo_root).read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_smart_planner_has_decision_and_commit_gate(repo_root: Path) -> None:
    assert "## Gate de Decis" in smart_planner_file(repo_root).read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_smart_planner_requires_commit_after_each_approved_decision(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "Após CADA decisão aprovada" in content
    assert "SÓ ENTÃO faça a próxima pergunta" in content


@pytest.mark.unit
def test_smart_planner_creates_skeleton_before_first_question(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "Antes da primeira pergunta" in content
    assert "skeleton" in content


@pytest.mark.unit
def test_smart_planner_requires_intermediate_commits(repo_root: Path) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "commit intermediário é obrigatório, não opcional" in content


@pytest.mark.unit
def test_smart_planner_requires_explicit_counterproposal_approval(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "contra-proposta" in content
    assert "Posso registrar assim?" in content


@pytest.mark.unit
def test_smart_planner_does_not_skip_obvious_branches(repo_root: Path) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "NUNCA pule um ramo independente" in content


@pytest.mark.unit
def test_smart_planner_has_stopping_conditions_section(repo_root: Path) -> None:
    assert "## Stopping Conditions" in smart_planner_file(repo_root).read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_smart_planner_has_handoff_section(repo_root: Path) -> None:
    assert "## Handoff" in smart_planner_file(repo_root).read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_smart_planner_has_limits_section(repo_root: Path) -> None:
    assert "## Limites" in smart_planner_file(repo_root).read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_smart_planner_has_replan_protocol_section(repo_root: Path) -> None:
    assert "## Protocolo de Replan" in smart_planner_file(repo_root).read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_smart_planner_has_executor_review_section(repo_root: Path) -> None:
    assert "## Revis" in smart_planner_file(repo_root).read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_smart_planner_references_grill_me_skill(repo_root: Path) -> None:
    assert "grill-me" in smart_planner_file(repo_root).read_text(encoding="utf-8")


@pytest.mark.unit
def test_smart_planner_references_planning_skill(repo_root: Path) -> None:
    assert "planning-and-task-breakdown" in smart_planner_file(repo_root).read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_smart_planner_references_caveman_skill(repo_root: Path) -> None:
    assert "caveman" in smart_planner_file(repo_root).read_text(encoding="utf-8")


@pytest.mark.unit
def test_smart_planner_references_prompt_improver_skill(repo_root: Path) -> None:
    assert "prompt-improver" in smart_planner_file(repo_root).read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_smart_planner_uses_distinct_commits_for_distinct_decisions(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "Decisões diferentes" in content
    assert "commits diferentes" in content


@pytest.mark.unit
def test_smart_planner_never_edits_application_code(repo_root: Path) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert re.search(r"NUNCA.*edita", content) is not None


@pytest.mark.unit
def test_smart_planner_uses_accented_portuguese(repo_root: Path) -> None:
    assert "PT-BR" in smart_planner_file(repo_root).read_text(encoding="utf-8")


@pytest.mark.unit
def test_agents_md_contains_smart_planner_behavioral_restriction(
    repo_root: Path,
) -> None:
    content = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    pattern = r"smart-planner.*nunca.*edita codigo|SmartPlanner.*Restricao"
    assert re.search(pattern, content, re.IGNORECASE) is not None
