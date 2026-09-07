from pathlib import Path

import re

import pytest


@pytest.fixture
def skill_path(repo_root: Path) -> Path:
    return repo_root / "harness-conf" / "skills" / "spec-executavel" / "SKILL.md"


@pytest.fixture
def skill_content(skill_path: Path) -> str:
    return skill_path.read_text(encoding="utf-8")


@pytest.mark.unit
def test_skill_file_exists(skill_path: Path) -> None:
    assert skill_path.is_file()


@pytest.mark.unit
def test_frontmatter_has_name_and_rich_description(
    skill_content: str,
) -> None:
    frontmatter = skill_content.split("---", 2)[1]

    assert "name: spec-executavel" in frontmatter
    assert "description:" in frontmatter

    # A description é o único mecanismo de ativação: precisa de triggers.
    for trigger in (
        "spec executável",
        "critérios de aceitação",
        "Gherkin",
        "BDD",
        "Esquema do Cenário",
        "Concordion",
        "specification by example",
    ):
        assert trigger in frontmatter, f"trigger ausente: {trigger}"


@pytest.mark.unit
def test_central_principle_links_text_and_test(skill_content: str) -> None:
    assert "Princípio central" in skill_content
    assert "mexe no texto e o teste quebra" in skill_content
    assert "linke ao máximo os valores" in skill_content.lower()


@pytest.mark.unit
def test_canonical_checklist_has_ten_items(skill_content: str) -> None:
    section = skill_content.split("Checklist de qualidade", 1)[1]

    numbered = [
        line
        for line in section.splitlines()
        if re.match(r"^\s*\d+\.\s+\S", line)
    ]
    assert len(numbered) == 10, (
        f"Checklist tem {len(numbered)} itens numerados; esperado 10"
    )


@pytest.mark.unit
def test_gherkin_is_strong_default_with_exception_clause(
    skill_content: str,
) -> None:
    assert "recomendação forte" in skill_content.lower()
    assert "Cláusula de exceção" in skill_content
    assert "proponha" in skill_content and "humano" in skill_content
    assert "permissionamento" in skill_content


@pytest.mark.unit
def test_canonical_scenario_structure_is_documented(
    skill_content: str,
) -> None:
    for token in (
        "Cenário:",
        "Dado que",
        "Quando tento",
        "Então",
        "Esquema do Cenário",
        "Exemplos",
    ):
        assert token in skill_content, f"token ausente: {token}"


@pytest.mark.unit
def test_tool_agnostic_with_concordion_as_example_only(
    skill_content: str,
) -> None:
    assert "Agnóstica de ferramenta" in skill_content
    assert "exemplo de ferramenta" in skill_content
    # Concordion aparece como exemplo, não como requisito.
    assert "requer Concordion" not in skill_content
    assert "use Concordion" not in skill_content


@pytest.mark.unit
def test_markdown_is_favored_medium(skill_content: str) -> None:
    assert "Markdown" in skill_content
    assert "favorecid" in skill_content


@pytest.mark.unit
def test_traceability_links_to_origin(skill_content: str) -> None:
    assert "Rastreabilidade" in skill_content
    assert "origem" in skill_content
    assert "requisito" in skill_content


@pytest.mark.unit
def test_out_of_scope_content_stays_out(skill_content: str) -> None:
    """Fronteiras que moram em outros lugares não vazam para a skill."""

    # INVEST e escrita/classificação de RF/RNF não são conteúdo da skill.
    assert "INVEST" not in skill_content
    assert "Requisito Funcional" not in skill_content
    assert "Requisito Não Funcional" not in skill_content

    # Regra de rejeição/casos limite (decisão de cobertura) fica fora.
    assert "casos limite" not in skill_content
    assert "rejeição" not in skill_content


@pytest.mark.unit
def test_skill_is_self_contained(skill_content: str) -> None:
    """Skill não cita plano, decisões ou vocabulário interno de planejamento."""

    for term in ("plano", "Task", "Anexo", "D8", "D10", "D11", "fase"):
        assert term not in skill_content, f"termo interno presente: {term}"


@pytest.mark.unit
def test_lines_respect_120_columns(skill_content: str) -> None:
    long_lines = [
        f"{index}: {line}"
        for index, line in enumerate(skill_content.splitlines(), start=1)
        if len(line) > 120
    ]
    assert long_lines == [], "linhas acima de 120 colunas:\n" + "\n".join(
        long_lines
    )
