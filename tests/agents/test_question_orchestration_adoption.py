from pathlib import Path

import pytest


DIRECT_CONSUMERS = ("analista",)
FORMER_GRILL_ME_CONSUMERS = ("dba", "eng-software", "front", "qa", "sec")


def agent_content(repo_root: Path, name: str) -> str:
    return (repo_root / "harness-conf/agents" / f"{name}.md").read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_direct_consumers_use_question_orchestration(
    repo_root: Path,
) -> None:
    for name in DIRECT_CONSUMERS:
        content = agent_content(repo_root, name)

        assert "question-orchestration" in content
        assert "modo direto" in content.lower()
        assert "grill-me" not in content


@pytest.mark.unit
def test_analista_delegates_question_limits_to_shared_protocol(
    repo_root: Path,
) -> None:
    content = agent_content(repo_root, "analista")

    assert "máx 5 por rodada" not in content
    assert "question-orchestration" in content


@pytest.mark.unit
def test_domain_agents_no_longer_reference_grill_me(
    repo_root: Path,
) -> None:
    for name in FORMER_GRILL_ME_CONSUMERS:
        assert "grill-me" not in agent_content(repo_root, name)


@pytest.mark.unit
def test_dev_workflow_matches_question_orchestration_adoption(
    repo_root: Path,
) -> None:
    workflow = (repo_root / "docs/workflow-agentes-dev.md").read_text(
        encoding="utf-8"
    )

    assert "question-orchestration" in workflow
    assert "grill-me" not in workflow
    assert "Pergunta skill para analista" not in workflow


@pytest.mark.unit
def test_scope_definition_workflow_references_question_orchestration(
    repo_root: Path,
) -> None:
    workflow = (repo_root / "docs/workflow-definicao-escopo.md").read_text(
        encoding="utf-8"
    )

    assert "question-orchestration" in workflow
