"""Avalia a aderência do agente à descoberta via codebase-memory CLI."""

import pytest


pytestmark = pytest.mark.agent_eval


DISCOVERY_PROMPTS = (
    (
        "função",
        "Preciso descobrir onde a função `prepare_test_context` está definida "
        "neste repositório e entender sua implementação. Faça a descoberta "
        "de código CLI-first antes de responder, sem usar grep/glob antes da "
        "detecção, e informe a primeira ferramenta usada e a sequência de "
        "investigação.",
    ),
    (
        "chamadores",
        "Preciso saber quem chama `OpenCodeClient.send_message` neste "
        "repositório. Use descoberta CLI-first, sem grep/glob antes de "
        "detectar o projeto. Explique a sequência usada para localizar os "
        "chamadores antes de responder.",
    ),
    (
        "documentação",
        "Preciso localizar na documentação deste repositório a regra que "
        "define o fallback para grep/glob. Faça a descoberta CLI-first, sem "
        "usar grep/glob antes da detecção, e explique qual ferramenta usaria "
        "primeiro.",
    ),
)

CLI_MARKERS = (
    "codebase-memory",
    "search_graph",
    "trace_path",
    "query_graph",
    "search_code",
    "list_projects",
)


@pytest.mark.parametrize(
    ("prompt_name", "prompt"),
    DISCOVERY_PROMPTS,
    ids=[prompt_name for prompt_name, _ in DISCOVERY_PROMPTS],
)
@pytest.mark.agent_eval_context(kind="skill", name="code-explorer-priority")
def test_code_discovery_response_indicates_cli_first(
    isolated_opencode,
    prompt_name: str,
    prompt: str,
):
    session = isolated_opencode.create_session().stdout
    assert session, (
        "Não foi possível criar sessão OpenCode para o prompt "
        f"{prompt_name} — verifique se o serviço está ativo"
    )

    result = isolated_opencode.send_message(session, prompt)
    assert result.returncode == 0, result.stderr

    response = result.stdout.lower()
    assert any(marker in response for marker in CLI_MARKERS), (
        f"A resposta para o prompt {prompt_name!r} não indicou uso do "
        "codebase-memory CLI antes de uma busca alternativa. "
        f"Resposta observada: {result.stdout!r}"
    )
