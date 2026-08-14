"""Behavioral tests for skill activation through OpenCode prompts."""

import pytest


pytestmark = pytest.mark.opencode


def test_prompt_mentions_doc_extract_with_coherent_response(opencode):
    session = opencode.create_session().stdout
    assert session, "Não foi possível criar sessão OpenCode — verifique se o serviço está ativo"

    result = opencode.send_message(
        session,
        "Existe uma skill chamada doc-extract? Responda apenas sim ou nao.",
    )
    assert result.returncode == 0
    assert "sim" in result.stdout.lower()


def test_prompt_mentions_md_export_with_coherent_response(opencode):
    session = opencode.create_session().stdout
    assert session, "Não foi possível criar sessão OpenCode — verifique se o serviço está ativo"

    result = opencode.send_message(
        session,
        "Existe uma skill chamada md-export? Responda apenas sim ou nao.",
    )
    assert result.returncode == 0
    assert "sim" in result.stdout.lower()


def test_svg_to_image_skill_can_be_mentioned_without_error(opencode):
    session = opencode.create_session().stdout
    assert session, "Não foi possível criar sessão OpenCode — verifique se o serviço está ativo"

    result = opencode.send_message(
        session,
        "Existe uma skill chamada svg-to-image? Responda sim ou não.",
    )
    assert result.returncode == 0
    assert "sim" in result.stdout.lower()


def test_test_driven_development_skill_has_tdd_trigger(opencode):
    session = opencode.create_session().stdout
    assert session, "Não foi possível criar sessão OpenCode — verifique se o serviço está ativo"

    result = opencode.send_message(
        session,
        "Existe uma skill chamada test-driven-development? Responda apenas sim ou nao.",
    )
    assert result.returncode == 0
    assert "sim" in result.stdout.lower()


def test_accessibility_audit_skill_can_be_mentioned(opencode):
    session = opencode.create_session().stdout
    assert session, "Não foi possível criar sessão OpenCode — verifique se o serviço está ativo"

    result = opencode.send_message(
        session,
        "Existe uma skill chamada accessibility-audit? Responda apenas sim ou nao.",
    )
    assert result.returncode == 0
    assert "sim" in result.stdout.lower()
