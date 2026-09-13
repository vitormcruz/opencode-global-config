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
    "'{\"project\":\"<nome-exato>\",\"name_pattern\":\".*Foo.*\"}'",
    "codebase-memory-mcp cli trace_path "
    "'{\"project\":\"<nome-exato>\",\"function_name\":\"Foo\",\"direction\":\"inbound\"}'",
    "codebase-memory-mcp cli get_code_snippet "
    "'{\"project\":\"<nome-exato>\",\"qualified_name\":\"pkg.Foo\"}'",
    "codebase-memory-mcp cli query_graph "
    "'{\"project\":\"<nome-exato>\",\"query\":\"MATCH ...\"}'",
    "codebase-memory-mcp cli search_code "
    "'{\"project\":\"<nome-exato>\",\"pattern\":\"termo\"}'",
    "codebase-memory-mcp cli get_architecture '{\"project\":\"<nome-exato>\"}'",
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
def test_description_uses_global_detection_and_discovery_triggers(
    skill_content: str,
):
    """A ativação ocorre por pedido de descoberta, não por configuração local."""

    frontmatter = skill_content.split("---", 2)[1]

    assert "APENAS quando o AGENTS.md" not in frontmatter
    assert "não a aplique" not in frontmatter
    assert "list_projects" in frontmatter
    for trigger in (
        "pesquisar",
        "procurar",
        "localizar",
        "onde está",
        "quem chama",
        "como funciona",
        "code discovery",
    ):
        assert trigger in frontmatter


@pytest.mark.unit
def test_code_explorer_keeps_operational_sections(skill_content: str):
    for section in (
        "Papel de cada ferramenta",
        "Invocação do CLI",
        "Ordem das ferramentas",
        "Passo 0",
        "Receita anti-erro",
        "Busca em documentação",
        "Fallback estrito",
    ):
        assert section in skill_content


@pytest.mark.unit
def test_skill_detects_indexed_repository_before_tool_order(skill_content: str):
    step_zero = skill_content.index("## Passo 0")
    list_projects = skill_content.index("list_projects", step_zero)

    assert list_projects > step_zero
    assert "repo atual" in skill_content
    assert "não está indexado" in skill_content
    assert "use grep/glob normalmente" in skill_content


@pytest.mark.unit
def test_skill_documents_correct_parameters_for_each_cli_tool(
    skill_content: str,
):
    assert '"name_pattern":".*Foo.*"' in skill_content
    assert '"direction":"inbound"' in skill_content
    assert '"direction":"outbound"' in skill_content
    assert '"query":"MATCH' in skill_content
    assert '"pattern":"termo"' in skill_content


@pytest.mark.unit
def test_skill_documents_shell_and_json_quote_rules(skill_content: str):
    normalized = " ".join(skill_content.split()).lower()

    assert "aspas simples" in normalized
    assert "aspas duplas" in normalized
    assert "não use aspas simples" in normalized


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
    order_section = skill_content.split("## Ordem das ferramentas", 1)[1].split(
        "## Passo 0", 1
    )[0]
    order = (
        "search_graph",
        "trace_path",
        "get_code_snippet",
        "query_graph",
        "get_architecture",
    )
    positions = [order_section.index(f"`{tool}`") for tool in order]

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
def test_index_command_keeps_optional_local_instruction_check(
    repo_root: Path,
):
    """A indicação local deixou de ser requisito para a indexação."""

    command = (repo_root / "harness-conf/commands/index-codebase.md").read_text(
        encoding="utf-8"
    )

    assert "copilot-specific" not in command
    assert "verificação opcional" in command
    assert "não é requisito" in command
    assert "AGENTS.md" in command


@pytest.mark.unit
def test_index_command_steps_1_and_2_are_single_flow(
    repo_root: Path,
):
    """Etapas 1-2 sem bifurcacao por cliente; diferenca de ambiente e
    nota curta."""

    command = (repo_root / "harness-conf/commands/index-codebase.md").read_text(
        encoding="utf-8"
    )
    steps_1_2 = command.split("## Etapa 3", 1)[0]

    assert "No **GitHub Copilot**" not in steps_1_2
    assert "No **OpenCode**" not in steps_1_2
    # Nota curta de ambiente no lugar da bifurcacao.
    assert "Nota de ambiente" in steps_1_2
    assert "sem prefixo `wsl`" in steps_1_2
    # repo_path relativo saiu: sempre absoluto.
    assert '\'"repo_path": "."\' ' not in steps_1_2
