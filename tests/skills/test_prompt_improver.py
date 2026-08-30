from pathlib import Path

import pytest


@pytest.fixture
def skill_content(repo_root: Path) -> str:
    return (repo_root / "skills/prompt-improver/SKILL.md").read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_prompt_improver_allows_narrow_orchestrator_handoff_exception(
    skill_content: str,
) -> None:
    assert (
        "Exceção: briefing interno do agente orquestrador" in skill_content
    )
    assert "autonomamente" in skill_content
    assert "Preserve o insumo original" in skill_content
    assert "Não invente nem resolva decisões" in skill_content


@pytest.mark.unit
def test_prompt_improver_keeps_human_approval_outside_devflow_exception(
    skill_content: str,
) -> None:
    assert "Fora dessa exceção" in skill_content
    assert "aprovação explícita do humano" in skill_content
