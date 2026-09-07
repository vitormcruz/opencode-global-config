"""Valida o acesso à busca (websearch) nos agentes de planejamento."""

import pytest


PLANNING_AGENTS = (
    "eng-software",
    "front",
    "dba",
    "sec",
    "qa",
    "smart-planner",
)

REVIEWER_AGENTS = (
    "rev",
    "curador-produto",
)


def frontmatter(repo_root: pytest.FixtureRequest, agent: str) -> str:
    content = (repo_root / "harness-conf/agents" / f"{agent}.md").read_text(
        encoding="utf-8"
    )
    return content.split("---", 2)[1]


@pytest.mark.unit
@pytest.mark.parametrize("agent", PLANNING_AGENTS)
def test_planning_agent_allows_websearch(repo_root, agent: str) -> None:
    content = frontmatter(repo_root, agent)
    assert "websearch: deny" not in content


@pytest.mark.unit
@pytest.mark.parametrize("agent", PLANNING_AGENTS)
def test_planning_agent_still_denies_webfetch(repo_root, agent: str) -> None:
    content = frontmatter(repo_root, agent)
    assert "webfetch: deny" in content


@pytest.mark.unit
@pytest.mark.parametrize("agent", REVIEWER_AGENTS)
def test_reviewer_agents_still_deny_websearch(repo_root, agent: str) -> None:
    content = frontmatter(repo_root, agent)
    assert "websearch: deny" in content