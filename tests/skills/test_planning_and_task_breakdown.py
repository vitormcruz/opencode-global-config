"""Valida a skill local planning-and-task-breakdown."""

from pathlib import Path

import pytest


@pytest.fixture
def skill_content(repo_root: Path) -> str:
    return (
        repo_root
        / "skills/planning-and-task-breakdown/SKILL.md"
    ).read_text(encoding="utf-8")


@pytest.mark.unit
def test_planning_skill_exists(repo_root: Path) -> None:
    assert (
        repo_root
        / "skills/planning-and-task-breakdown/SKILL.md"
    ).is_file()


@pytest.mark.unit
def test_planning_has_separacao_plano_artefato(
    skill_content: str,
) -> None:
    """Garante a seção que separa plano de artefato de
    produção."""
    assert "Separação plano" in skill_content


@pytest.mark.unit
def test_planning_separacao_proibe_identificadores(
    skill_content: str,
) -> None:
    """A regra deve citar explicitamente os identificadores
    proibidos nos artefatos de produção."""
    normalized = skill_content.lower()

    assert "códigos de decisão" in normalized
    assert "autocontido" in normalized
    assert "plano" in normalized


@pytest.mark.unit
def test_planning_checklist_menciona_identificadores(
    skill_content: str,
) -> None:
    """O checklist de verificação deve incluir item sobre
    não citar identificadores do plano."""
    assert (
        "Nenhum artefato de produção cita identificadores do plano"
        in skill_content
    )
