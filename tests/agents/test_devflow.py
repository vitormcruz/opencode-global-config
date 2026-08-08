"""Valida o conteúdo do agente devflow."""

import re
from pathlib import Path

import pytest


def devflow_content(repo_root: Path) -> str:
    """Lê o agente devflow como texto UTF-8."""

    return (repo_root / "agents" / "devflow.md").read_text(encoding="utf-8")


@pytest.mark.unit
def test_devflow_has_mediation_section(repo_root: Path) -> None:
    assert "Função de mediação" in devflow_content(repo_root)


@pytest.mark.unit
def test_devflow_uses_grill_me_on_demand_for_mediation(repo_root: Path) -> None:
    content = devflow_content(repo_root)
    assert "grill-me" in content
    assert re.search(
        r"avalia.*qualidade|conforme a complexidade",
        content,
        re.IGNORECASE,
    ) is not None


@pytest.mark.unit
def test_devflow_contract_has_item_six(repo_root: Path) -> None:
    content = devflow_content(repo_root)
    assert re.search(r"^6\.", content, re.MULTILINE) is not None
    assert "Não precisa concluir a tarefa" in content


@pytest.mark.unit
def test_devflow_contract_does_not_instruct_agents_to_use_grill_me(
    repo_root: Path,
) -> None:
    lines = devflow_content(repo_root).splitlines()
    try:
        start = next(
            index
            for index, line in enumerate(lines)
            if "Contrato com agentes spawnados" in line
        )
    except StopIteration:
        start = len(lines)

    contract_window = "\n".join(lines[start : start + 21])
    assert "grill-me" not in contract_window
