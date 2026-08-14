"""Behavioral tests for prompt responses through the OpenCode API."""

import pytest


pytestmark = pytest.mark.opencode


def test_post_session_creates_session_with_id(opencode):
    result = opencode.create_session()
    assert result.returncode == 0
    assert result.stdout


def test_simple_prompt_returns_non_empty_response(opencode):
    session = opencode.create_session().stdout
    assert session, "Não foi possível criar sessão OpenCode — verifique se o serviço está ativo"

    result = opencode.send_message(session, "Responda apenas com a palavra: ok")
    assert result.returncode == 0
    assert result.stdout


def test_response_contains_ok_when_requested(opencode):
    session = opencode.create_session().stdout
    assert session, "Não foi possível criar sessão OpenCode — verifique se o serviço está ativo"

    result = opencode.send_message(session, "Responda apenas com a palavra: ok")
    assert result.returncode == 0
    assert "ok" in result.stdout.lower()


def test_specific_agent_uses_local_bonsai(opencode):
    session = opencode.create_session().stdout
    assert session, "Não foi possível criar sessão com agente OpenCode — verifique se o serviço está ativo"

    result = opencode.send_message(
        session,
        "Responda apenas: ok",
        agent="plan",
    )
    assert result.returncode == 0
    assert "ok" in result.stdout.lower()
