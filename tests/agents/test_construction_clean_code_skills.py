"""Garante skills de Clean Code obrigatórias na construção."""

from pathlib import Path

import pytest


def _section_until(content: str, heading: str, end: str) -> str:
    lines = content.replace("\r", "").splitlines()
    start = lines.index(heading)
    stop = next(
        index
        for index in range(start + 1, len(lines))
        if lines[index] == end
    )
    return "\n".join(lines[start:stop])


@pytest.mark.unit
def test_eng_software_requires_clean_code_skills_on_build(
    repo_root: Path,
) -> None:
    content = (repo_root / "harness-conf" / "agents/eng-software.md").read_text(
        encoding="utf-8"
    )
    required = _section_until(
        content,
        "### Obrigatórias (carregar ANTES da capacidade indicada)",
        "### Condicionais (carregar quando a condição se aplicar)",
    )
    optional = _section_until(
        content,
        "### Condicionais (carregar quando a condição se aplicar)",
        "### Transversais (úteis em qualquer capacidade)",
    )

    assert "| clean-code |" in required
    assert "| code-simplification |" in required
    assert "Sempre que escrever código produtivo" in required
    assert "| code-simplification |" not in optional
    assert "obrigatórias em toda construção" in content


@pytest.mark.unit
def test_front_requires_clean_code_skills_on_build(repo_root: Path) -> None:
    content = (repo_root / "harness-conf/agents/front.md").read_text(
        encoding="utf-8"
    )
    required = _section_until(
        content,
        "### Obrigatórias (carregar ANTES da capacidade indicada)",
        "### Condicionais (carregar quando a condição se aplicar)",
    )
    optional = _section_until(
        content,
        "### Condicionais (carregar quando a condição se aplicar)",
        "### Transversais (úteis em qualquer capacidade)",
    )

    assert "| clean-code |" in required
    assert "| code-simplification |" in required
    assert "| code-simplification |" not in optional
    assert "Carregue `clean-code` e `code-simplification`" in content


@pytest.mark.unit
def test_simplification_description_activates_on_construction(
    repo_root: Path,
) -> None:
    content = (repo_root / "harness-conf/skills/code-simplification/SKILL.md").read_text(
        encoding="utf-8"
    )
    frontmatter = content.split("---", 2)[1]

    assert "during construction" in frontmatter
    assert "construir" in frontmatter
