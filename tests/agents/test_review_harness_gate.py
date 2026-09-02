"""Valida que suítes por especialidade não rodam na Construção."""

from pathlib import Path

import pytest


@pytest.mark.unit
def test_workflow_does_not_run_specialty_suites_in_construction(
    repo_root: Path,
) -> None:
    workflow = (repo_root / "docs/workflow-agentes-dev.md").read_text(
        encoding="utf-8"
    )

    assert "Obrigatório na construção" not in workflow
    assert "construção executa; revisão só se modificou" not in workflow
    assert "harness/testes" in workflow


@pytest.mark.unit
def test_curador_produto_validates_orchestrator_at_test_phase(
    repo_root: Path,
) -> None:
    content = (repo_root / "agents/curador-produto.md").read_text(
        encoding="utf-8"
    )
    lower = " ".join(content.lower().split())

    assert "harness/testes" in content
    assert "fase testes" in lower
    assert "após as fases de construção e revisão da construção" not in lower
    assert "sem modificações — harness não executado" not in content
