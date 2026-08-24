"""Valida a skill local clean-code."""

from pathlib import Path

import pytest


@pytest.fixture
def skill_content(repo_root: Path) -> str:
    return (repo_root / "skills/clean-code/SKILL.md").read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_clean_code_skill_exists(repo_root: Path) -> None:
    assert (repo_root / "skills/clean-code/SKILL.md").is_file()


@pytest.mark.unit
def test_clean_code_frontmatter_has_activation(skill_content: str) -> None:
    frontmatter = skill_content.split("---", 2)[1]

    assert "name: clean-code" in frontmatter
    assert "construir" in frontmatter
    assert "dependência temporal" in frontmatter
    assert "CQS" in frontmatter
    assert "Law of Demeter" in frontmatter
    assert "code-simplification" in frontmatter


@pytest.mark.unit
def test_clean_code_covers_core_rules(skill_content: str) -> None:
    for section in (
        "Nomes",
        "Funções",
        "Efeitos e CQS",
        "Dependência temporal",
        "Law of Demeter",
        "SOLID",
        "Checklist antes de concluir código",
    ):
        assert section in skill_content


@pytest.mark.unit
def test_clean_code_does_not_replace_simplification(
    skill_content: str,
) -> None:
    assert "Não substitui code-simplification" in skill_content or (
        "não substitui code-simplification" in skill_content.lower()
    )
    assert "`code-simplification`" in skill_content
