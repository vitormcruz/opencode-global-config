"""Valida o contrato do agente agregador e validador de harness."""

from pathlib import Path

import pytest


@pytest.mark.unit
def test_val_harness_runs_only_registered_aggregator_before_validation(
    repo_root: Path,
) -> None:
    content = (repo_root / "agents/val-harness.md").read_text(encoding="utf-8")
    normalized = " ".join(content.split()).lower()

    assert "seção `## agregador de harness`" in normalized
    assert "comando registrado" in normalized
    assert "execute-o" in normalized
    assert "antes de cruzar evidências" in normalized
    assert "harness por agente" in normalized
    assert "não execute comandos de harness por agente" in normalized


@pytest.mark.unit
def test_val_harness_keeps_no_spawn_and_reports_missing_aggregator(
    repo_root: Path,
) -> None:
    content = (repo_root / "agents/val-harness.md").read_text(encoding="utf-8")
    normalized = " ".join(content.split()).lower()

    assert "não spawna agentes" in normalized
    assert "agregador" in normalized
    assert "lacuna" in normalized
