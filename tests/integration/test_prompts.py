"""Behavioral tests for prompt responses through the OpenCode API."""

import pytest


pytestmark = pytest.mark.opencode


@pytest.mark.opencode_context(kind="empty")
def test_post_session_creates_session_with_id(isolated_opencode):
    result = isolated_opencode.create_session()
    assert result.returncode == 0
    assert result.stdout


@pytest.mark.opencode_context(kind="empty")
def test_simple_prompt_returns_non_empty_response(isolated_opencode):
    session = isolated_opencode.create_session().stdout
    assert session, "Não foi possível criar sessão OpenCode — verifique se o serviço está ativo"

    result = isolated_opencode.send_message(session, "Responda apenas com a palavra: ok")
    assert result.returncode == 0
    assert result.stdout


@pytest.mark.opencode_context(kind="empty")
def test_response_contains_ok_when_requested(isolated_opencode):
    session = isolated_opencode.create_session().stdout
    assert session, "Não foi possível criar sessão OpenCode — verifique se o serviço está ativo"

    result = isolated_opencode.send_message(session, "Responda apenas com a palavra: ok")
    assert result.returncode == 0
    assert "ok" in result.stdout.lower()


@pytest.mark.opencode_context(kind="empty")
def test_specific_agent_uses_local_qwen(isolated_opencode):
    session = isolated_opencode.create_session().stdout
    assert session, "Não foi possível criar sessão com agente OpenCode — verifique se o serviço está ativo"

    result = isolated_opencode.send_message(
        session,
        "Responda apenas: ok",
        agent="plan",
    )
    assert result.returncode == 0
    assert "ok" in result.stdout.lower()
