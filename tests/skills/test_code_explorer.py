from pathlib import Path

import pytest


DISCOVERY_DOCS = (
    "AGENTS.md",
    "harness-conf/skills/code-explorer-priority/SKILL.md",
    "harness-conf/commands/index-codebase.md",
    "harness-conf/commands/bench-indexing.md",
)

CLI_COMMANDS = (
    "codebase-memory-mcp cli list_projects '{}'",
    "codebase-memory-mcp cli index_repository "
    "'{\"repo_path\":\"/caminho/absoluto/do/repo\"}'",
    "codebase-memory-mcp cli search_graph "
    "'{\"project\":\"<nome>\",\"query\":\"descrição\"}'",
    "codebase-memory-mcp cli trace_path "
    "'{\"project\":\"<nome>\",\"function_name\":\"Foo\"}'",
    "codebase-memory-mcp cli get_code_snippet "
    "'{\"project\":\"<nome>\",\"qualified_name\":\"pkg.Foo\"}'",
    "codebase-memory-mcp cli query_graph "
    "'{\"project\":\"<nome>\",\"query\":\"MATCH ...\"}'",
    "codebase-memory-mcp cli search_code "
    "'{\"project\":\"<nome>\",\"pattern\":\"termo\"}'",
    "codebase-memory-mcp cli get_architecture '{\"project\":\"<nome>\"}'",
)


@pytest.fixture
def skill_content(repo_root: Path) -> str:
    return (
        repo_root / "harness-conf" / "skills/code-explorer-priority/SKILL.md"
    ).read_text(encoding="utf-8")


@pytest.fixture
def discovery_content(repo_root: Path) -> str:
    return "\n".join(
        (repo_root / relative_path).read_text(encoding="utf-8")
        for relative_path in DISCOVERY_DOCS
    )


@pytest.mark.unit
def test_code_explorer_skill_exists(repo_root: Path):
    assert (
        repo_root / "harness-conf/skills/code-explorer-priority/SKILL.md"
    ).is_file()


@pytest.mark.unit
def test_code_explorer_frontmatter_has_name_and_description(
    skill_content: str,
):
    frontmatter = skill_content.split("---", 2)[1]

    assert "name: code-explorer-priority" in frontmatter
    assert "description:" in frontmatter
    assert "codebase-memory" in frontmatter


@pytest.mark.unit
def test_description_is_conditioned_on_agents_md(skill_content: str):
    """Ativação só quando o AGENTS.md do repo indicar codebase-memory."""

    frontmatter = skill_content.split("---", 2)[1]

    assert "APENAS quando o AGENTS.md" in frontmatter
    assert "não a aplique" in frontmatter


@pytest.mark.unit
def test_code_explorer_keeps_operational_sections(skill_content: str):
    for section in (
        "Papel de cada ferramenta",
        "Invocação do CLI",
        "Ordem das ferramentas",
        "Passo 0",
        "Busca em documentação",
        "Fallback estrito",
    ):
        assert section in skill_content


@pytest.mark.unit
def test_client_matrix_was_removed(skill_content: str):
    """Tabela 'Acesso por Cliente' saiu: comando idêntico nos ambientes."""

    normalized = " ".join(skill_content.split())

    assert "Acesso por Cliente" not in skill_content
    # O comando único nos dois ambientes segue documentado.
    assert "mesmo no WSL e no Windows" in normalized
    assert "sem prefixo `wsl`" in normalized


@pytest.mark.unit
def test_skill_documents_all_cli_commands_with_positional_json(
    skill_content: str,
):
    for command in CLI_COMMANDS:
        assert command in skill_content, f"comando ausente: {command}"


@pytest.mark.unit
def test_skill_documents_tool_order(skill_content: str):
    order = (
        "search_graph",
        "trace_path",
        "get_code_snippet",
        "query_graph",
        "get_architecture",
    )
    positions = [skill_content.index(f"`{tool}`") for tool in order]

    assert positions == sorted(positions), (
        "Ordem documentada das ferramentas diverge do padrão aprovado"
    )
    assert "Ordem das ferramentas" in skill_content


@pytest.mark.unit
def test_search_code_uses_pattern_not_query(skill_content: str):
    assert "use `pattern`, não `query`" in skill_content


@pytest.mark.unit
def test_index_repository_requires_absolute_repo_path(skill_content: str):
    assert "`repo_path` absoluto" in skill_content


@pytest.mark.unit
def test_doc_search_uses_section_nodes_with_cypher(skill_content: str):
    assert "`Section`" in skill_content
    assert "MATCH (s:Section)" in skill_content


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
def test_index_command_has_no_linux_path_for_copilot(repo_root: Path):
    command = (repo_root / "harness-conf/commands/index-codebase.md").read_text(
        encoding="utf-8"
    )

    assert "/mnt/c" not in command


@pytest.mark.unit
def test_index_command_no_longer_references_copilot_specific(
    repo_root: Path,
):
    """O copilot-specific foi extinto: nenhuma referencia sobra."""

    command = (repo_root / "harness-conf/commands/index-codebase.md").read_text(
        encoding="utf-8"
    )

    assert "copilot-specific" not in command
    # Etapa 3 agora verifica instrucoes no AGENTS.md do repo.
    assert "AGENTS.md" in command
