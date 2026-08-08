"""Behavioral tests for agents exposed by OpenCode."""

import json

import pytest


pytestmark = pytest.mark.opencode


def test_get_agent_returns_status_200(opencode):
    result = opencode.get_status("/agent")
    assert result.returncode == 0
    assert result.stdout == "200"


def test_get_agent_lists_dba(opencode):
    result = opencode.get("/agent")
    assert result.returncode == 0
    assert "dba" in result.stdout


def test_get_agent_lists_revisor_historia(opencode):
    result = opencode.get("/agent")
    assert result.returncode == 0
    assert "revisor-historia" in result.stdout


def test_get_agent_lists_analista(opencode):
    result = opencode.get("/agent")
    assert result.returncode == 0
    assert "analista" in result.stdout


def test_get_agent_lists_aws_analista(opencode):
    result = opencode.get("/agent")
    assert result.returncode == 0
    assert "aws-analista" in result.stdout


def test_get_agent_lists_curador_produto(opencode):
    result = opencode.get("/agent")
    assert result.returncode == 0
    assert "curador-produto" in result.stdout


def test_get_agent_lists_eng_software(opencode):
    result = opencode.get("/agent")
    assert result.returncode == 0
    assert "eng-software" in result.stdout


def test_get_agent_lists_sec(opencode):
    result = opencode.get("/agent")
    assert result.returncode == 0
    assert "sec" in result.stdout


def test_get_agent_lists_devflow(opencode):
    result = opencode.get("/agent")
    assert result.returncode == 0
    assert "devflow" in result.stdout


def test_each_returned_agent_has_name_field(opencode):
    result = opencode.get("/agent")
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
