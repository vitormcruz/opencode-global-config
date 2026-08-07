from pathlib import Path

import pytest


@pytest.fixture
def skill_content(repo_root: Path) -> str:
    return (
        repo_root / "skills/web-research-exa-crawl4ai/SKILL.md"
    ).read_text(encoding="utf-8")


@pytest.mark.unit
def test_skill_file_exists(repo_root: Path):
    assert (repo_root / "skills/web-research-exa-crawl4ai/SKILL.md").is_file()


@pytest.mark.unit
def test_skill_frontmatter_has_name_and_description(skill_content: str):
    frontmatter = skill_content.split("---", 2)[1]

    assert "name: web-research-exa-crawl4ai" in frontmatter
    assert "description:" in frontmatter


@pytest.mark.unit
def test_skill_description_keeps_activation_triggers(skill_content: str):
    frontmatter = skill_content.split("---", 2)[1].lower()

    assert "pesquisa web" in frontmatter
    assert "url" in frontmatter
    assert "documentos binários" in frontmatter
    assert "doc-extract" in frontmatter


@pytest.mark.unit
def test_skill_keeps_legacy_behavioral_sections(skill_content: str):
    assert "websearch" in skill_content
    assert "crawl4ai" in skill_content
    assert "Regras principais" in skill_content
    assert "Resiliencia a rate limits" in skill_content
    assert "NUNCA desista da pesquisa" in skill_content
    assert "backoff progressivo" in skill_content
    assert "429" in skill_content
    assert "Reduza a carga" in skill_content
    assert "sequenciais" in skill_content
    assert "## Fallback" in skill_content
    assert "doc-extract" in skill_content


@pytest.mark.unit
def test_skill_has_no_legacy_mcp_tool_names(skill_content: str):
    legacy_tools = (
        "crawl4ai_md",
        "crawl4ai_html",
        "crawl4ai_execute_js",
        "crawl4ai_screenshot",
        "crawl4ai_pdf",
    )

    for tool in legacy_tools:
        assert tool not in skill_content


@pytest.mark.unit
def test_skill_declares_websearch_preference_chain(skill_content: str):
    exa = skill_content.index("web_search_exa")
    native = skill_content.index("websearch")
    environment = skill_content.index("busca padrão do ambiente")

    assert exa < native < environment


@pytest.mark.unit
def test_skill_has_executable_crwl_example_for_each_operation(skill_content: str):
    examples = (
        "crwl https://example.com -o md-fit",
        "crwl https://example.com -o json",
        "crwl https://example.com -c 'js_code=document.title' -o md-fit",
        "crwl https://example.com -c screenshot=true -O saida.json",
        "crwl https://example.com -c pdf=true -O saida.json",
        "crwl https://example.com --deep-crawl bfs --max-pages",
    )

    for example in examples:
        assert example in skill_content


@pytest.mark.unit
def test_skill_preserves_binary_document_fallback(skill_content: str):
    assert "doc-extract" in skill_content
    assert "PDF" in skill_content
    assert "DOCX" in skill_content
    assert "XLSX" in skill_content


@pytest.mark.unit
def test_skill_describes_cli_failure_recovery(skill_content: str):
    assert "exit code" in skill_content
    assert "timeout" in skill_content
    assert "bloqueio" in skill_content
