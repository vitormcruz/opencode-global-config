"""Contrato dos executores: instruções e suítes por especialidade."""

from pathlib import Path

import pytest

EXECUTORS = ("dba", "front", "rev", "eng-software", "qa", "sec")
INSTRUCTION_AGENTS = (*EXECUTORS, "curador-produto")
SPEC_AGENTS = INSTRUCTION_AGENTS


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
def test_devflow_does_not_require_own_instruction_lookup(
    repo_root: Path,
) -> None:
    content = _flat(_agent_text(repo_root, "devflow"))

    assert "## instruções por agente" not in content
    assert "procure instruções específicas para o devflow" not in content


@pytest.mark.unit
def test_specialists_return_to_caller_without_naming_devflow(
    repo_root: Path,
) -> None:
    specialists = (*EXECUTORS, "curador-produto")
    for name in specialists:
        content = _agent_text(repo_root, name)
        assert "devflow" not in content.lower(), name
        assert "quem o acionou" in content.lower(), name

    silent = (
        repo_root / "AGENTS.md",
        repo_root
        / "harness-conf/agents/default-artifacts"
        / "diretrizes-regras-produto-agents-md-template.md",
        repo_root
        / "harness-conf/agents/default-artifacts"
        / "doc-readme-template.md",
    )
    for path in silent:
        assert "devflow" not in path.read_text(encoding="utf-8").lower(), path.name


@pytest.mark.unit
def test_executors_resolve_suite_spec_via_agents_link(
    repo_root: Path,
) -> None:
    for name in SPEC_AGENTS:
        content = _agent_text(repo_root, name)
        lower = _flat(content)
        assert "Testes por Especialidade" in content, name
        assert "AGENTS.md" in content, name
        assert "Diretrizes e Regras de Produto" in content, name
        assert "subseção" in lower, name
        assert "referenciado" in lower or "referência" in lower, name
        assert "docs/README.md" not in content, name
        assert "docs/testes-por-especialidade.md" not in content, name


@pytest.mark.unit
def test_key_agents_declare_two_test_levels(repo_root: Path) -> None:
    for name in ("devflow", "qa", "eng-software", "curador-produto"):
        lower = _flat(_agent_text(repo_root, name))
        assert lower.count("dois níveis de teste") == 1, name
        assert "testes da aplicação" in lower, name
        assert "testes dos scripts" in lower, name
        assert "somente quando os scripts mudam" in lower, name
