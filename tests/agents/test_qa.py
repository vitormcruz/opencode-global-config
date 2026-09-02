"""Contrato do qa na fase Testes."""

from pathlib import Path

import pytest


@pytest.fixture
def qa_content(repo_root: Path) -> str:
    return (repo_root / "agents/qa.md").read_text(encoding="utf-8")


@pytest.mark.unit
def test_qa_runs_only_orchestrator_and_manuals(qa_content: str) -> None:
    assert "harness/testes" in qa_content
    assert "manuais" in qa_content.lower()
    assert "um a um" in qa_content.lower()


@pytest.mark.unit
def test_qa_does_not_call_specialty_scripts_directly(qa_content: str) -> None:
    assert "harness/backend" not in qa_content
    assert "harness/dados" not in qa_content
    assert "harness/seguranca" not in qa_content
    assert "harness/frontend" not in qa_content
