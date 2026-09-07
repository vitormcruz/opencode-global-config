"""Valida a proibição de timeouts absorvida pela skill
reliable-async-operations."""

from pathlib import Path

import pytest


@pytest.fixture
def skill_path(repo_root: Path) -> Path:
    return (
        repo_root
        / "harness-conf"
        / "skills"
        / "reliable-async-operations"
        / "SKILL.md"
    )


@pytest.fixture
def skill_content(skill_path: Path) -> str:
    return skill_path.read_text(encoding="utf-8")


@pytest.mark.unit
def test_skill_file_exists(skill_path: Path) -> None:
    assert skill_path.is_file()


@pytest.mark.unit
def test_forbidden_timeouts_section_exists(skill_content: str) -> None:
    assert "Proibição de definir ou ajustar timeouts" in skill_content


def _prohibition_section(skill_content: str) -> str:
    """Extrai a seção da proibição com whitespace normalizado."""

    section = skill_content.split(
        "Proibição de definir ou ajustar timeouts", 1
    )[1].split("## ", 1)[0]
    return " ".join(section.split())


@pytest.mark.unit
def test_generic_or_convenience_timeouts_are_forbidden(
    skill_content: str,
) -> None:
    section = _prohibition_section(skill_content)

    # Bullet 1: proibição e suas razões.
    assert "PROIBIDO" in section
    assert "timeouts genéricos ou por conveniência" in section
    assert "não mascara travamento" in section
    assert "não impõe desempenho" in section
    assert "não vira critério de falha" in section


@pytest.mark.unit
def test_timeout_exceptions_are_exhaustive(skill_content: str) -> None:
    section = _prohibition_section(skill_content)

    # Bullet 2: exceções com justificativa do recurso e do valor.
    assert "recurso contínuo com inatividade já comprovada" in section
    assert "confirmação explícita prévia do humano" in section
    assert "justificativa do recurso e do valor" in section


@pytest.mark.unit
def test_high_value_is_not_a_loophole(skill_content: str) -> None:
    section = _prohibition_section(skill_content)

    # Bullet 3: valor alto não substitui remoção; timeout existente é
    # informado, nunca alterado em silêncio.
    assert "valor alto" in section
    assert "remova o timeout ou consulte o humano" in section
    assert "informe ao humano" in section
    assert "não altere silenciosamente" in section


@pytest.mark.unit
def test_description_covers_timeout_trigger(skill_content: str) -> None:
    frontmatter = skill_content.split("---", 2)[1]

    for trigger in (
        "definir timeout",
        "ajustar timeout",
        "aumentar timeout",
        "timeout genérico",
    ):
        assert trigger in frontmatter, f"trigger ausente: {trigger}"


@pytest.mark.unit
def test_base_does_not_duplicate_the_prohibition(repo_root: Path) -> None:
    base = (repo_root / "harness-conf" / "AGENTS.base.md").read_text(
        encoding="utf-8"
    )

    assert "timeouts genéricos" not in base
    assert "não mascara travamento" not in base
