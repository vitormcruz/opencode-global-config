"""Contrato do eng-software: TDD, normalização e commit."""

from pathlib import Path

import pytest


@pytest.fixture
def eng_content(repo_root: Path) -> str:
    return (repo_root / "harness-conf/agents/eng-software.md").read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_eng_software_normalizes_specialist_batch_after_own_tdd(
    eng_content: str,
) -> None:
    lower = " ".join(eng_content.lower().split())
    assert "normaliza" in lower
    assert "dba" in lower
    assert "front" in lower
    assert "tdd" in lower
    assert "domínio" in lower
    assert "devolver" in lower or "devolve" in lower
    assert "entre especialistas" in lower


@pytest.mark.unit
def test_eng_software_remains_unique_committer(eng_content: str) -> None:
    assert "Committer único" in eng_content
    assert "git-workflow-and-versioning" in eng_content


@pytest.mark.unit
def test_eng_software_keeps_internal_tdd_smoke(eng_content: str) -> None:
    assert "Smoke tests" in eng_content
    assert "test-driven-development" in eng_content


def _refactoring_section(content: str) -> str:
    """Extrai a regra de acomodação do código novo."""

    lines = content.replace("\r", "").splitlines()
    start = lines.index("#### Etapa 3 — Acomodação do código novo")
    end = next(
        index
        for index in range(start + 1, len(lines))
        if lines[index].startswith("**ANTES** de escrever testes")
    )
    return "\n".join(lines[start:end])


@pytest.mark.unit
def test_code_accommodation_returns_possible_plan_change_to_caller(
    eng_content: str,
) -> None:
    section = _refactoring_section(eng_content)
    normalized = " ".join(section.lower().split())

    assert "o plano pode mudar" in normalized
    assert "não ajuste a implementação" in normalized
    assert "não registre decisão" in normalized
    assert "não escolha o desfecho" in normalized
    assert (
        "devolva o fato a quem o acionou e aguarde a resposta de quem o acionou antes de prosseguir"
        in normalized
    )
    assert "|" not in section
    assert not any(
        term in normalized
        for term in ("gate", "fase", "fluxo", "workflow", "devflow")
    )
