"""Behavioral tests for skill activation through OpenCode prompts."""

import pytest


pytestmark = pytest.mark.opencode


@pytest.mark.opencode_context(kind="empty")
def test_effective_provider_disables_thinking(isolated_opencode):
    session = isolated_opencode.create_session().stdout
    assert session, "Não foi possível criar sessão OpenCode — verifique se o serviço está ativo"

    result = isolated_opencode.send_message(
        session,
        "Responda apenas sim.",
    )

    assert result.returncode == 0
    assert result.stdout.strip(), (
        "O raciocínio provavelmente não está desligado no caminho efetivo dos "
        "testes. Verifique o repasse de "
        "`chat_template_kwargs.enable_thinking=false` do OpenCode ao provider "
        "bonsai-local."
    )


@pytest.mark.opencode_context(kind="skill", name="doc-extract")
def test_prompt_mentions_doc_extract_with_coherent_response(isolated_opencode):
    session = isolated_opencode.create_session().stdout
    assert session, "Não foi possível criar sessão OpenCode — verifique se o serviço está ativo"

    result = isolated_opencode.send_message(
        session,
        "Existe uma skill chamada doc-extract? Responda apenas sim ou nao.",
    )
    assert result.returncode == 0
    assert "sim" in result.stdout.lower()


@pytest.mark.opencode_context(kind="skill", name="md-export")
def test_prompt_mentions_md_export_with_coherent_response(isolated_opencode):
    session = isolated_opencode.create_session().stdout
    assert session, "Não foi possível criar sessão OpenCode — verifique se o serviço está ativo"

    result = isolated_opencode.send_message(
        session,
        "Existe uma skill chamada md-export? Responda apenas sim ou nao.",
    )
    assert result.returncode == 0
    assert "sim" in result.stdout.lower()


@pytest.mark.opencode_context(kind="skill", name="svg-to-image")
def test_svg_to_image_skill_can_be_mentioned_without_error(isolated_opencode):
    session = isolated_opencode.create_session().stdout
    assert session, "Não foi possível criar sessão OpenCode — verifique se o serviço está ativo"

    result = isolated_opencode.send_message(
        session,
        "Existe uma skill chamada svg-to-image? Responda sim ou não.",
    )
    assert result.returncode == 0
    assert "sim" in result.stdout.lower()


@pytest.mark.opencode_context(kind="skill", name="test-driven-development")
def test_test_driven_development_skill_has_tdd_trigger(isolated_opencode):
    session = isolated_opencode.create_session().stdout
    assert session, "Não foi possível criar sessão OpenCode — verifique se o serviço está ativo"

    result = isolated_opencode.send_message(
        session,
        "Existe uma skill chamada test-driven-development? Responda apenas sim ou nao.",
    )
    assert result.returncode == 0
    assert "sim" in result.stdout.lower()


@pytest.mark.opencode_context(kind="skill", name="accessibility-audit")
def test_accessibility_audit_skill_can_be_mentioned(isolated_opencode):
    session = isolated_opencode.create_session().stdout
    assert session, "Não foi possível criar sessão OpenCode — verifique se o serviço está ativo"

    result = isolated_opencode.send_message(
        session,
        "Existe uma skill chamada accessibility-audit? Responda apenas sim ou nao.",
    )
    assert result.returncode == 0
    assert "sim" in result.stdout.lower()
