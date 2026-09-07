"""Contrato do sec: roteiro manual, suíte automática fora."""

from pathlib import Path

import pytest


@pytest.fixture
def sec_content(repo_root: Path) -> str:
    return (repo_root / "harness-conf" / "agents/sec.md").read_text(encoding="utf-8")


@pytest.mark.unit
def test_sec_records_manual_script_during_planning(sec_content: str) -> None:
    lower = sec_content.lower()
    assert "roteiro" in lower
    assert "manual" in lower
    assert "planejamento" in lower


@pytest.mark.unit
def test_sec_executes_only_manual_script_in_test_phase(sec_content: str) -> None:
    lower = sec_content.lower()
    assert "fase testes" in lower or "fase de testes" in lower
    assert "só o roteiro" in lower or "somente o roteiro" in lower or (
        "apenas o roteiro" in lower
    )


@pytest.mark.unit
def test_sec_does_not_own_automatic_security_suite(sec_content: str) -> None:
    assert "harness do `sec`" not in sec_content
    assert "testes-produto/seguranca" not in sec_content
    lower = sec_content.lower()
    assert "suíte automática" in lower or "suite automatica" in lower
