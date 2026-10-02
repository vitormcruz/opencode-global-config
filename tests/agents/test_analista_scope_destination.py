"""Valida o contrato de destino do escopo no agente analista."""

from pathlib import Path

import pytest


def analista_content(repo_root: Path) -> str:
    return (repo_root / "harness-conf/agents/analista.md").read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_analista_uses_product_map_scope_section_for_destination(
    repo_root: Path,
) -> None:
    content = analista_content(repo_root)
    normalized = " ".join(content.split())

    assert "seção **Definição de Escopo** do Mapa do Produto" in content
    assert "não pergunte ao humano onde escrever" in normalized
    assert "BACKLOG.md" not in content
    assert "Arquivo de Planejamento" not in content


@pytest.mark.unit
def test_analista_combines_destination_with_human_when_map_has_no_destination(
    repo_root: Path,
) -> None:
    normalized = " ".join(analista_content(repo_root).split())

    assert "Se a seção não existir ou não indicar o destino" in normalized
    assert "combine com o humano onde" in normalized
