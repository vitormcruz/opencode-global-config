"""Valida o conteúdo do agente devflow."""

import re
from pathlib import Path

import pytest


def devflow_content(repo_root: Path) -> str:
    """Lê o agente devflow como texto UTF-8."""

    return (repo_root / "agents" / "devflow.md").read_text(encoding="utf-8")


def question_protocol_content(repo_root: Path) -> str:
    """Lê o protocolo compartilhado de perguntas."""

    return (repo_root / "skills/question-orchestration/SKILL.md").read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_devflow_has_mediation_section(repo_root: Path) -> None:
    assert "Função de mediação" in devflow_content(repo_root)


@pytest.mark.unit
def test_question_protocol_adapts_presentation_without_grill_me(
    repo_root: Path,
) -> None:
    content = question_protocol_content(repo_root)

    assert "Pergunta curta e objetiva" in content
    assert "Pergunta elaborada, múltipla ou volumosa" in content
    assert "grill-me" not in content


@pytest.mark.unit
def test_devflow_delegates_question_protocol_to_skill(
    repo_root: Path,
) -> None:
    content = devflow_content(repo_root)

    assert "question-orchestration" in content
    assert "fonte única" in content
    assert "no máximo 4 perguntas por rodada" not in content


@pytest.mark.unit
def test_devflow_keeps_its_operational_mediation_controls(
    repo_root: Path,
) -> None:
    content = devflow_content(repo_root)

    assert "grill-me" not in content
    assert "Checklist estrutural" in content
    assert "Máximo 2 rodadas" in content
    assert "Continuidade da mediação" in content
    assert re.search(
        r"Nunca encerre a mediação\s+por conta própria",
        content,
    ) is not None
    assert "`prompt-improver`" in content
    assert "autonomamente" in content
    assert "insumo original" in content
    assert "Não invente decisões" in content


@pytest.mark.unit
def test_devflow_does_not_reference_smart_planner(repo_root: Path) -> None:
    assert "smart-planner" not in devflow_content(repo_root)


@pytest.mark.unit
def test_development_workflow_references_question_protocol_skill(
    repo_root: Path,
) -> None:
    workflow = (repo_root / "docs/workflow-agentes-dev.md").read_text(
        encoding="utf-8"
    )

    assert "question-orchestration" in workflow
    assert "no máximo 4 perguntas por rodada" not in workflow
    assert "Checklist estrutural" in workflow
    assert "Continuidade da mediação" in workflow
    assert "Prompt-improver para handoff" in workflow
    assert "Grill-me sob demanda" not in workflow


@pytest.mark.unit
def test_devflow_contract_has_item_six(repo_root: Path) -> None:
    content = devflow_content(repo_root)
    assert re.search(r"^6\.", content, re.MULTILINE) is not None
    assert "Não precisa concluir a tarefa" in content


@pytest.mark.unit
def test_devflow_contract_does_not_instruct_agents_to_use_grill_me(
    repo_root: Path,
) -> None:
    lines = devflow_content(repo_root).splitlines()
    try:
        start = next(
            index
            for index, line in enumerate(lines)
            if "Contrato com agentes spawnados" in line
        )
    except StopIteration:
        start = len(lines)

    contract_window = "\n".join(lines[start : start + 21])
    assert "grill-me" not in contract_window


@pytest.mark.unit
def test_devflow_skips_review_harness_without_modification(
    repo_root: Path,
) -> None:
    content = devflow_content(repo_root)

    assert "sem modificações — harness não executado" in content
    assert "não modificou" in content
