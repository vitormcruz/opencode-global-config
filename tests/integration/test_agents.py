"""Behavioral tests for agents exposed by OpenCode."""

import json

import pytest


pytestmark = pytest.mark.opencode


@pytest.mark.opencode_context(kind="agent", name="dba")
def test_get_agent_returns_status_200(isolated_opencode):
    result = isolated_opencode.get_status("/agent")
    assert result.returncode == 0
    assert result.stdout == "200"


@pytest.mark.opencode_context(kind="agent", name="dba")
def test_get_agent_lists_dba(isolated_opencode):
    result = isolated_opencode.get("/agent")
    assert result.returncode == 0
    assert "dba" in result.stdout


@pytest.mark.opencode_context(kind="agent", name="revisor-historia")
def test_get_agent_lists_revisor_historia(isolated_opencode):
    result = isolated_opencode.get("/agent")
    assert result.returncode == 0
    assert "revisor-historia" in result.stdout


@pytest.mark.opencode_context(kind="agent", name="analista")
def test_get_agent_lists_analista(isolated_opencode):
    result = isolated_opencode.get("/agent")
    assert result.returncode == 0
    assert "analista" in result.stdout


@pytest.mark.opencode_context(kind="agent", name="aws-analista")
def test_get_agent_lists_aws_analista(isolated_opencode):
    result = isolated_opencode.get("/agent")
    assert result.returncode == 0
    assert "aws-analista" in result.stdout


@pytest.mark.opencode_context(kind="agent", name="curador-produto")
def test_get_agent_lists_curador_produto(isolated_opencode):
    result = isolated_opencode.get("/agent")
    assert result.returncode == 0
    assert "curador-produto" in result.stdout


@pytest.mark.opencode_context(kind="agent", name="eng-software")
def test_get_agent_lists_eng_software(isolated_opencode):
    result = isolated_opencode.get("/agent")
    assert result.returncode == 0
    assert "eng-software" in result.stdout


@pytest.mark.opencode_context(kind="agent", name="sec")
def test_get_agent_lists_sec(isolated_opencode):
    result = isolated_opencode.get("/agent")
    assert result.returncode == 0
    assert "sec" in result.stdout


@pytest.mark.opencode_context(kind="agent", name="devflow")
def test_get_agent_lists_devflow(isolated_opencode):
    result = isolated_opencode.get("/agent")
    assert result.returncode == 0
    assert "devflow" in result.stdout


@pytest.mark.opencode_context(kind="agent", name="dba")
def test_each_returned_agent_has_name_field(isolated_opencode):
    result = isolated_opencode.get("/agent")
    if result.returncode == 0:
        data = json.loads(result.stdout)
        if isinstance(data, list):
            has_names = all(
                isinstance(agent, dict) and "name" in agent for agent in data
            )
        else:
            has_names = isinstance(data, dict) and "name" in data
    else:
        has_names = False
    assert result.returncode == 0 and has_names
