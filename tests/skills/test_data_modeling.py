"""Valida a skill local data-modeling."""

from pathlib import Path

import pytest


@pytest.fixture
def skill_content(repo_root: Path) -> str:
    return (repo_root / "skills/data-modeling/SKILL.md").read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_data_modeling_skill_exists(repo_root: Path) -> None:
    assert (repo_root / "skills/data-modeling/SKILL.md").is_file()


@pytest.mark.unit
def test_data_modeling_frontmatter_has_activation(
    skill_content: str,
) -> None:
    frontmatter = skill_content.split("---", 2)[1]

    assert "name: data-modeling" in frontmatter
    for trigger in (
        "modelagem",
        "schema",
        "migration",
        "migração",
        "normalização",
        "índice",
        "FK",
        "zero-downtime",
        "DBML",
    ):
        assert trigger in frontmatter, f"gatilho ausente: {trigger}"


@pytest.mark.unit
def test_data_modeling_covers_core_sections(
    skill_content: str,
) -> None:
    for section in (
        "Modelagem Conceitual e Lógica",
        "Normalização",
        "Tipos e Constraints",
        "Migrações Seguras",
        "Indexação",
        "Checklist de Revisão de Modelo",
    ):
        assert section in skill_content, f"seção ausente: {section}"


@pytest.mark.unit
def test_data_modeling_has_review_checklist(
    skill_content: str,
) -> None:
    assert "Checklist de Revisão de Modelo" in skill_content
    for item in (
        "Migration é reversível",
        "Backward-compatible",
        "CREATE INDEX CONCURRENTLY",
        "Dados sensíveis",
    ):
        assert item in skill_content, f"item de checklist ausente: {item}"


@pytest.mark.unit
def test_data_modeling_covers_expand_migrate_contract(
    skill_content: str,
) -> None:
    normalized = " ".join(skill_content.split()).lower()

    assert "expand" in normalized
    assert "migrate" in normalized
    assert "contract" in normalized


@pytest.mark.unit
def test_data_modeling_under_400_lines(repo_root: Path) -> None:
    lines = (repo_root / "skills/data-modeling/SKILL.md").read_text(
        encoding="utf-8"
    ).splitlines()
    assert len(lines) <= 400


@pytest.mark.unit
def test_data_modeling_is_ptbr(skill_content: str) -> None:
    body = skill_content.split("---", 2)[2]
    for word in (
        "modelagem",
        "migração",
        "normalização",
        "índice",
        "reversível",
    ):
        assert word in body, f"palavra PT-BR ausente: {word}"
