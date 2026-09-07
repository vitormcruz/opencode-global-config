"""Valida adoção da skill spec-executavel pelos agentes do workflow."""

from pathlib import Path

import pytest


MANDATORY_CONSUMERS = ("analista", "eng-software", "qa", "sec")
INTERVIEW_CONSUMERS = ("curador-produto",)


def agent_content(repo_root: Path, name: str) -> str:
    return (repo_root / "harness-conf/agents" / f"{name}.md").read_text(
        encoding="utf-8"
    )


def mandatory_skills_section(content: str) -> str:
    """Extrai o bloco de skills obrigatórias até o próximo subheading."""

    lines = content.replace("\r", "").splitlines()
    try:
        start = lines.index(
            "### Obrigatórias (carregar ANTES da capacidade indicada)"
        )
    except ValueError:
        return ""

    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("### "):
            end = index
            break

    return "\n".join(lines[start:end])


@pytest.mark.unit
def test_mandatory_consumers_reference_skill_in_mandatory_table(
    repo_root: Path,
) -> None:
    for name in MANDATORY_CONSUMERS:
        section = mandatory_skills_section(agent_content(repo_root, name))

        assert section, f"{name}.md: sem bloco de skills obrigatórias"
        assert "spec-executavel" in section, (
            f"{name}.md: spec-executavel não está na tabela de obrigatórias"
        )


@pytest.mark.unit
def test_interview_consumers_reference_skill(repo_root: Path) -> None:
    for name in INTERVIEW_CONSUMERS:
        content = agent_content(repo_root, name)

        assert "spec-executavel" in content, (
            f"{name}.md: não referencia spec-executavel"
        )


@pytest.mark.unit
def test_analista_closes_gherkin_with_exception_clause(
    repo_root: Path,
) -> None:
    content = agent_content(repo_root, "analista")

    assert "Fechamento para Gherkin" in content
    assert "cláusula de exceção" in content
    # Desvio do formato sempre passa pelo humano.
    assert "discutindo o" in content and "humano" in content


@pytest.mark.unit
def test_analista_keeps_own_rules_in_body(repo_root: Path) -> None:
    """INVEST, RF/RNF e regra de rejeição/casos limite ficam no analista."""

    content = agent_content(repo_root, "analista")

    assert "INVEST" in content
    assert "RF" in content and "RNF" in content
    assert "Rejeição/erro" in content
    assert "Casos limite" in content


@pytest.mark.unit
def test_skill_exists_for_agent_references(repo_root: Path) -> None:
    skill = repo_root / "harness-conf" / "skills" / "spec-executavel"
    assert (skill / "SKILL.md").is_file()
