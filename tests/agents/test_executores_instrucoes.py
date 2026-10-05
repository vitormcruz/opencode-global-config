"""Contrato dos executores: instruções e suítes por especialidade."""

from pathlib import Path

import pytest

EXECUTORS = ("dba", "front", "rev", "eng-software", "qa", "sec")
INSTRUCTION_AGENTS = (*EXECUTORS, "curador-produto")


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
def test_agents_consult_own_instructions_when_used(
    repo_root: Path,
) -> None:
    for name in INSTRUCTION_AGENTS:
        content = _flat(_agent_text(repo_root, name))
        assert "instruções por agente" in content, name
        assert "sempre que" in content and "for utilizado" in content, name
        assert "antes de executar a tarefa" in content, name
        assert "procure instruções específicas" in content, name
        assert "sem instruções a pedido do humano" in content, name


@pytest.mark.unit
def test_workflow_defines_per_use_instruction_lookup(repo_root: Path) -> None:
    workflow = _flat(
        (repo_root / "docs/workflow-agentes-dev.md").read_text(
            encoding="utf-8"
        )
    )

    assert "### 6. instruções por agente" in workflow
    assert "toda vez que esse agente for utilizado" in workflow
    assert "antes de executar a tarefa" in workflow
    assert "procura instruções para aquela utilização" in workflow
    assert "independentemente da fase" in workflow


@pytest.mark.unit
def test_executors_resolve_suite_spec_via_agents_link(
    repo_root: Path,
) -> None:
    for name in EXECUTORS:
        content = _agent_text(repo_root, name)
        lower = _flat(content)
        assert "Testes por Especialidade" in content, name
        assert "docs/README.md" in content, name
        assert "docs/testes-produto.md" not in content, name
        assert "path hardcoded" in lower, name
        assert "o que deve conter" in lower, name


@pytest.mark.unit
def test_key_agents_declare_two_test_levels(repo_root: Path) -> None:
    for name in ("devflow", "qa", "eng-software", "curador-produto"):
        lower = _flat(_agent_text(repo_root, name))
        assert "dois níveis de teste" in lower, name
        assert "testes da aplicação" in lower, name
        assert "testes dos scripts" in lower, name
        assert "somente quando os scripts mudam" in lower, name
