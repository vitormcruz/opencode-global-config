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
