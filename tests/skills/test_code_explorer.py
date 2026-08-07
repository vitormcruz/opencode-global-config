from pathlib import Path

import pytest


DISCOVERY_DOCS = (
    "AGENTS.md",
    ".github/copilot-specific.instructions.md",
    "skills/code-explorer-priority/SKILL.md",
    "commands/index-codebase.md",
    "commands/bench-indexing.md",
)


@pytest.fixture
def skill_content(repo_root: Path) -> str:
    return (
        repo_root / "skills/code-explorer-priority/SKILL.md"
    ).read_text(encoding="utf-8")


@pytest.fixture
def discovery_content(repo_root: Path) -> str:
    return "\n".join(
        (repo_root / relative_path).read_text(encoding="utf-8")
        for relative_path in DISCOVERY_DOCS
    )


@pytest.mark.unit
def test_code_explorer_skill_exists(repo_root: Path):
    assert (repo_root / "skills/code-explorer-priority/SKILL.md").is_file()


@pytest.mark.unit
def test_code_explorer_frontmatter_has_name_and_description(skill_content: str):
    frontmatter = skill_content.split("---", 2)[1]

    assert "name: code-explorer-priority" in frontmatter
    assert "description:" in frontmatter
    assert "codebase-memory" in frontmatter


@pytest.mark.unit
def test_code_explorer_keeps_operational_sections(skill_content: str):
    for section in (
        "Acesso por Cliente",
        "OpenCode",
        "GitHub Copilot",
        "Passo 0",
        "Passo 1",
        "Passo 2",
        "Passo 3",
    ):
        assert section in skill_content


@pytest.mark.unit
def test_discovery_docs_use_native_cli_without_mcp_wrapper(
    discovery_content: str,
):
    forbidden = (
        "mcp " + "--list",
        "mcp " + "codebase-memory",
        "mcp " + "crawl4ai",
        "mcp " + "<servidor>",
    )

    for pattern in forbidden:
        assert pattern not in discovery_content


@pytest.mark.unit
def test_discovery_docs_document_cli_syntax(discovery_content: str):
    assert "codebase-memory-mcp cli list_projects '{}'" in discovery_content


@pytest.mark.unit
def test_discovery_rule_is_cli_first_and_imperative(discovery_content: str):
    assert "REGRA ABSOLUTA" in discovery_content
    assert "codebase-memory-mcp cli" in discovery_content
    assert "NUNCA" in discovery_content
    assert "grep/glob" in discovery_content


@pytest.mark.unit
def test_project_not_found_recovery_is_preserved(discovery_content: str):
    normalized = discovery_content.lower()

    assert "project not found" in normalized
    assert "list_projects" in normalized
    assert "retent" in normalized


@pytest.mark.unit
def test_client_matrix_uses_same_cli_on_wsl_and_windows(repo_root: Path):
    agents = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    instructions = (
        repo_root / ".github/copilot-specific.instructions.md"
    ).read_text(encoding="utf-8")
    combined = f"{agents}\n{instructions}"

    assert "OpenCode" in combined
    assert "WSL" in combined
    assert "GitHub Copilot" in combined
    assert "Windows" in combined
    assert combined.count("codebase-memory-mcp cli") >= 2
