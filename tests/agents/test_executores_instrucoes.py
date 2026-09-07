"""Contrato dos executores: instruções e suítes por especialidade."""

from pathlib import Path

import pytest

EXECUTORS = ("dba", "front", "rev", "eng-software", "qa", "sec")


def _agent_text(repo_root: Path, name: str) -> str:
    return (repo_root / "harness-conf/agents" / f"{name}.md").read_text(
        encoding="utf-8"
    )


def _flat(text: str) -> str:
    return " ".join(text.lower().split())


@pytest.mark.unit
def test_executors_do_not_run_suites_in_construction_or_review(
    repo_root: Path,
) -> None:
    forbidden = (
        "localize o harness no agents.md",
        "leia o prompt e execute",
        "execute o script indicado no agents.md",
        "na construção e na revisão da",
    )
    for name in EXECUTORS:
        lower = _agent_text(repo_root, name).lower()
        for phrase in forbidden:
            assert phrase not in lower, f"{name}.md ainda cita: {phrase}"


@pytest.mark.unit
def test_executors_read_own_instructions_at_task_start(
    repo_root: Path,
) -> None:
    for name in EXECUTORS:
        content = _agent_text(repo_root, name)
        assert "Instruções por Agente" in content, name
        assert "SEM INSTRUÇÕES A PEDIDO DO HUMANO" in content, name
        assert "início de qualquer tarefa" in content, name


@pytest.mark.unit
def test_executors_resolve_suite_spec_via_agents_link(
    repo_root: Path,
) -> None:
    for name in EXECUTORS:
        content = _agent_text(repo_root, name)
        lower = _flat(content)
        assert "Testes por Especialidade" in content, name
        assert "docs/testes-produto.md" in content, name
        assert "path hardcoded" in lower, name
        assert "o que deve conter" in lower, name
