"""Contrato do eng-software: TDD, normalização e commit."""

from pathlib import Path

import pytest


@pytest.fixture
def eng_content(repo_root: Path) -> str:
    return (repo_root / "agents/eng-software.md").read_text(encoding="utf-8")


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
