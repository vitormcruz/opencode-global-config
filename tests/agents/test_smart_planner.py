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
def test_smart_planner_delegates_question_protocol_to_skill(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")

    assert "question-orchestration" in content
    assert "fonte única" in content
    assert "## Modo de Operação" not in content
    assert "## Triagem de Contexto Inicial" not in content


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
def test_smart_planner_auto_commits_after_confirmed_modification(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "commita automaticamente" in content
    assert "posso commitar" in content


@pytest.mark.unit
def test_smart_planner_creates_skeleton_before_first_question(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "Antes da primeira pergunta" in content
    assert "skeleton" in content


@pytest.mark.unit
def test_smart_planner_commits_are_automatic_not_optional(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "automáticos, não opcionais" in content


@pytest.mark.unit
def test_smart_planner_keeps_its_commit_gate_after_delegating_questions(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "### Commits automáticos após confirmação" in content
    assert "commita automaticamente" in content


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
def test_smart_planner_uses_adaptive_question_blocks(repo_root: Path) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "question-orchestration" in content
    assert "entre 1 e 4 perguntas" not in content


@pytest.mark.unit
def test_smart_planner_references_planning_skill(repo_root: Path) -> None:
    assert "planning-and-task-breakdown" in smart_planner_file(repo_root).read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_smart_planner_uses_question_orchestration(
    repo_root: Path,
) -> None:
    assert "question-orchestration" in smart_planner_file(repo_root).read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_smart_planner_uses_concise_commits_without_caveman(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "caveman" not in content
    assert "concisa" in content


@pytest.mark.unit
def test_smart_planner_references_prompt_improver_skill(repo_root: Path) -> None:
    assert "prompt-improver" in smart_planner_file(repo_root).read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_smart_planner_groups_commits_by_coherence_without_amend(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "coerência narrativa" in content
    assert "--amend" in content
    assert "Nunca use" in content


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


@pytest.mark.unit
def test_smart_planner_has_central_premise_capable_for_cheap(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "Premissa Central" in content
    assert "modelo mais capaz" in content
    assert "modelo barato" in content


@pytest.mark.unit
def test_smart_planner_has_detail_calibration_self_question(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "Calibração de Detalhe" in content
    assert "agente menos capaz" in content


@pytest.mark.unit
def test_smart_planner_delegates_initial_context_triage(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")

    assert "question-orchestration" in content
    assert "prompt inicial fraco" not in content


@pytest.mark.unit
def test_smart_planner_handoff_requires_autonomous_local_commits(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    handoff = re.sub(r"\s+", " ", content.split("## Handoff", maxsplit=1)[1])

    assert "commits locais autonomamente" in handoff
    assert "unidades logicamente coesas" in handoff
    assert "`git push`" in handoff
    assert "confirmação explícita do humano" in handoff


@pytest.mark.unit
def test_agents_md_allows_local_commits_and_requires_push_confirmation(
    repo_root: Path,
) -> None:
    content = (repo_root / "AGENTS.md").read_text(encoding="utf-8")

    assert "`git push` exige confirmação explícita do humano" in content
    assert "NUNCA realize o commit independentemente." not in content
    assert "SÓ realize o commit quando o humano autorizar" not in content
    assert "Exceção — smart-planner" not in content
