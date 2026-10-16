"""Contrato do qa na fase Testes."""

from pathlib import Path

import pytest


@pytest.fixture
def qa_content(repo_root: Path) -> str:
    return (repo_root / "harness-conf" / "agents/qa.md").read_text(encoding="utf-8")


@pytest.mark.unit
def test_qa_runs_only_orchestrator_and_manuals(qa_content: str) -> None:
    assert "testes-produto" in qa_content
    assert "manuais" in qa_content.lower()
    assert "um a um" in qa_content.lower()


@pytest.mark.unit
def test_qa_does_not_call_specialty_scripts_directly(qa_content: str) -> None:
    assert "testes-produto/backend" not in qa_content
    assert "testes-produto/dados" not in qa_content
    assert "testes-produto/seguranca" not in qa_content
    assert "testes-produto/frontend" not in qa_content


def _non_testable_criterion_step(content: str) -> str:
    """Extrai o passo que define o destino de critérios não testáveis."""

    lines = content.replace("\r", "").splitlines()
    start = next(
        index
        for index, line in enumerate(lines)
        if line.startswith("5. Avaliar se critérios de aceitação são testáveis.")
    )
    end = next(
        index
        for index in range(start + 1, len(lines))
        if lines[index].startswith("6.")
    )
    return "\n".join(lines[start:end])


@pytest.mark.unit
def test_qa_returns_non_testable_criteria_to_caller(
    qa_content: str,
) -> None:
    step = " ".join(_non_testable_criterion_step(qa_content).lower().split())

    assert "devolver o achado a quem o acionou" in step
    assert "devflow" not in step
    assert "solicitante" not in step
    assert "humano" not in step
