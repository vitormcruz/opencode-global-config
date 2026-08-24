"""Valida que harness na revisão só roda após modificação."""

from pathlib import Path

import pytest


@pytest.mark.unit
def test_workflow_review_harness_only_if_modified(repo_root: Path) -> None:
    workflow = (repo_root / "docs/workflow-agentes-dev.md").read_text(
        encoding="utf-8"
    )

    assert "Harness é **obrigatório" in workflow
    assert "na construção** para agentes" in workflow
    assert "só é obrigatório" in workflow
    assert "**modificou** algum artefato" in workflow
    assert "sem modificações — harness não executado" in workflow
    assert "executa somente se modificar" in workflow
    assert "na construção e na revisão da construção** para agentes" not in (
        workflow
    )


@pytest.mark.unit
def test_val_harness_accepts_unmodified_skip(repo_root: Path) -> None:
    content = (repo_root / "agents/val-harness.md").read_text(encoding="utf-8")

    assert "sem modificações — harness não executado" in content
    assert "Evidência ausente ou incompleta = FALHA" in content


@pytest.mark.unit
def test_curador_produto_review_harness_respects_unmodified(
    repo_root: Path,
) -> None:
    content = (repo_root / "agents/curador-produto.md").read_text(
        encoding="utf-8"
    )

    assert "se o agente modificou artefatos" in content
    assert "sem modificações — harness não executado" in content
    assert "agente executou seu script? Evidência JSON" not in content
