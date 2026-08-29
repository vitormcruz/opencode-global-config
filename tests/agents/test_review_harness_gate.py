"""Valida que harness na revisão só roda após modificação."""

from pathlib import Path

import pytest


@pytest.mark.unit
def test_workflow_review_harness_only_if_modified(repo_root: Path) -> None:
    workflow = (repo_root / "docs/workflow-agentes-dev.md").read_text(
        encoding="utf-8"
    )

    assert "Obrigatório na construção" in workflow
    assert "na revisão, só se modificou" in workflow
    assert "artefato" in workflow
    assert "construção executa; revisão só se modificou" in workflow
    assert "sem modificações — harness não executado" in workflow


@pytest.mark.unit
def test_curador_produto_accepts_unmodified_skip(repo_root: Path) -> None:
    content = (repo_root / "agents/curador-produto.md").read_text(
        encoding="utf-8"
    )

    assert "sem modificações — harness não executado" in content
    assert "Ausente ou incompleta = FALHA" in content


@pytest.mark.unit
def test_curador_produto_review_harness_respects_unmodified(
    repo_root: Path,
) -> None:
    content = (repo_root / "agents/curador-produto.md").read_text(
        encoding="utf-8"
    )

    assert "Para cada agente que atuou na fase" in content
    assert "sem modificações — harness não executado" in content
    assert "agente executou seu script? Evidência JSON" not in content
