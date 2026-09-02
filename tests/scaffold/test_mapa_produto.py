from io import StringIO
from pathlib import Path
import re

import pytest

from opencode_config.cli import scaffold_mapa


def run_scaffold(*arguments: str) -> tuple[int, str, str]:
    output = StringIO()
    error = StringIO()
    status = scaffold_mapa.run(
        list(arguments),
        output=output,
        error=error,
    )
    return status, output.getvalue(), error.getvalue()


@pytest.mark.unit
def test_scaffold_entrypoint_is_registered(repo_root: Path) -> None:
    pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8")

    assert (
        'opencode-scaffold-mapa = "opencode_config.cli.scaffold_mapa:main"'
        in pyproject
    )


@pytest.mark.unit
def test_scaffold_fails_without_arguments() -> None:
    status, _, _ = run_scaffold()

    assert status == 1


@pytest.mark.unit
def test_scaffold_fails_when_doc_value_is_missing() -> None:
    status, _, _ = run_scaffold("--doc")

    assert status == 1


@pytest.mark.unit
def test_scaffold_fails_when_testes_produto_value_is_missing() -> None:
    status, _, _ = run_scaffold("--testes-produto")

    assert status == 1


@pytest.mark.unit
def test_scaffold_fails_for_unknown_flag() -> None:
    status, _, _ = run_scaffold("--invalida")

    assert status == 1


@pytest.mark.unit
def test_doc_scaffold_creates_required_sections(tmp_path: Path) -> None:
    destination = tmp_path / "test-doc.md"
    destination.touch()

    status, _, _ = run_scaffold("--doc", str(destination))
    content = destination.read_text(encoding="utf-8")

    assert status == 0
    assert "## Definição de Escopo" in content
    assert "## Elementos de Especificação" in content
    assert "### Regras de Documentação" in content
    assert "#### Regras Gerais" in content
    assert "## Estratégias de Indexação de Código" in content


@pytest.mark.unit
def test_doc_scaffold_is_idempotent(tmp_path: Path) -> None:
    destination = tmp_path / "test-doc.md"

    first_status, _, _ = run_scaffold("--doc", str(destination))
    second_status, _, _ = run_scaffold("--doc", str(destination))
    content = destination.read_text(encoding="utf-8")

    assert first_status == 0
    assert second_status == 0
    assert content.count("## Definição de Escopo") == 1


@pytest.mark.unit
def test_scaffold_preserves_existing_content(tmp_path: Path) -> None:
    destination = tmp_path / "existing.md"
    destination.write_text("# Conteúdo existente\n", encoding="utf-8")

    status, _, _ = run_scaffold("--doc", str(destination))

    assert status == 0
    content = destination.read_text(encoding="utf-8")
    assert content.startswith("# Conteúdo existente\n")
    assert "## Definição de Escopo" in content


@pytest.mark.unit
def test_doc_scaffold_contains_defaults_without_empty_placeholders(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "test-doc.md"

    status, _, _ = run_scaffold("--doc", str(destination))
    content = destination.read_text(encoding="utf-8")

    assert status == 0
    assert "(preencher)" not in content
    assert (
        "|----------|-------------------|-------------------|---------|"
        in content
    )
    for element in (
        "Critérios de Aceite + Requisitos",
        "Regras de Produto",
        "Modelo de Dados",
        "Threat Model",
        "Plano de Testes",
        "Identidade Visual",
        "ADR (Arquitetura)",
    ):
        assert f"| {element} " in content
    for expected in (
        "Concordion",
        "DBML",
        "docs/specs/",
        "docs/modelo.dbml",
        "docs/threat-model.md",
        "plan/ui/",
        "docs/adr/",
    ):
        assert expected in content


@pytest.mark.unit
def test_doc_scaffold_contains_general_rules(tmp_path: Path) -> None:
    destination = tmp_path / "test-doc.md"

    status, _, _ = run_scaffold("--doc", str(destination))
    content = destination.read_text(encoding="utf-8")

    assert status == 0
    assert "#### Regras Gerais" in content
    assert "Documentação complementa o código" in content
    assert "Doc derivável do código não se armazena" in content
    assert "Doc desatualizada é pior que ausência" in content


@pytest.mark.unit
def test_doc_scaffold_contains_rules_for_each_element(tmp_path: Path) -> None:
    destination = tmp_path / "test-doc.md"

    status, _, _ = run_scaffold("--doc", str(destination))
    content = destination.read_text(encoding="utf-8")

    assert status == 0
    for section in (
        "Critérios de Aceite + Requisitos",
        "Regras de Produto",
        "Modelo de Dados",
        "Threat Model",
        "Plano de Testes",
        "Identidade Visual",
        "ADR (Arquitetura)",
    ):
        assert f"#### {section}" in content
    assert "arquivo Concordion" in content
    assert "Seguir template ADR" in content
    assert "schema diff a cada alteração" in content


@pytest.mark.unit
def test_positional_argument_acts_as_doc_destination(tmp_path: Path) -> None:
    destination = tmp_path / "test-doc-legacy.md"

    status, _, _ = run_scaffold(str(destination))
    content = destination.read_text(encoding="utf-8")

    assert status == 0
    assert "## Definição de Escopo" in content
    assert "### Regras de Documentação" in content


@pytest.mark.unit
def test_positional_doc_scaffold_is_idempotent(tmp_path: Path) -> None:
    destination = tmp_path / "test-doc-legacy.md"

    first_status, _, _ = run_scaffold(str(destination))
    second_status, _, _ = run_scaffold(str(destination))
    content = destination.read_text(encoding="utf-8")

    assert first_status == 0
    assert second_status == 0
    assert content.count("## Definição de Escopo") == 1


SPECIALTIES = ("backend", "dados", "segurança", "frontend")
SPECIALTY_SCRIPTS = (
    "testes-produto/backend",
    "testes-produto/dados",
    "testes-produto/seguranca",
    "testes-produto/frontend",
)
WORKFLOW_AGENTS = (
    "eng-software",
    "dba",
    "front",
    "sec",
    "qa",
    "rev",
    "curador-produto",
)


@pytest.mark.unit
def test_testes_produto_scaffold_creates_section(tmp_path: Path) -> None:
    destination = tmp_path / "AGENTS.md"
    destination.touch()

    status, _, _ = run_scaffold("--testes-produto", str(destination))

    assert status == 0
    content = destination.read_text(encoding="utf-8")
    assert "## Testes por Especialidade" in content
    assert "## Harness por Agente" not in content


@pytest.mark.unit
def test_testes_produto_scaffold_lists_specialties_and_orchestrator(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "AGENTS.md"

    status, _, _ = run_scaffold("--testes-produto", str(destination))
    content = destination.read_text(encoding="utf-8")

    assert status == 0
    for specialty in SPECIALTIES:
        assert f"| {specialty} " in content
    assert "testes-produto" in content
    for script in SPECIALTY_SCRIPTS:
        assert script in content


@pytest.mark.unit
def test_testes_produto_scaffold_does_not_list_agents_as_suite_owners(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "AGENTS.md"

    status, _, _ = run_scaffold("--testes-produto", str(destination))
    content = destination.read_text(encoding="utf-8")

    assert status == 0
    for agent in ("eng-software", "dba", "sec", "qa", "front"):
        assert f"| {agent} " not in content
    assert "SEM HARNESS A PEDIDO DO HUMANO" not in content


@pytest.mark.unit
def test_testes_produto_scaffold_is_idempotent(tmp_path: Path) -> None:
    destination = tmp_path / "AGENTS.md"
    destination.touch()

    first_status, _, _ = run_scaffold("--testes-produto", str(destination))
    second_status, _, _ = run_scaffold("--testes-produto", str(destination))
    content = destination.read_text(encoding="utf-8")

    assert first_status == 0
    assert second_status == 0
    assert content.count("## Testes por Especialidade") == 1


@pytest.mark.unit
def test_testes_produto_scaffold_is_short_snippet_with_spec_link(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "AGENTS.md"

    status, _, _ = run_scaffold("--testes-produto", str(destination))
    content = destination.read_text(encoding="utf-8")

    assert status == 0
    assert "docs/testes-produto.md" in content
    assert "harness/agregar" not in content
    assert "## Agregador de Harness" not in content
    assert "### Especificação dos Scripts de Harness" not in content
    assert "O que deve conter" not in content
    assert '"prompt"' not in content


@pytest.mark.unit
def test_doc_and_testes_produto_flags_create_both_scaffolds(tmp_path: Path) -> None:
    doc = tmp_path / "doc.md"
    agents = tmp_path / "AGENTS.md"

    status, _, _ = run_scaffold(
        "--doc",
        str(doc),
        "--testes-produto",
        str(agents),
    )

    assert status == 0
    assert "## Definição de Escopo" in doc.read_text(encoding="utf-8")
    assert "## Testes por Especialidade" in agents.read_text(encoding="utf-8")


@pytest.mark.unit
def test_curador_produto_contains_three_doc_template_sections(
    repo_root: Path,
) -> None:
    content = (repo_root / "agents/curador-produto.md").read_text(
        encoding="utf-8"
    )

    assert "Definição de Escopo" in content
    assert "Elementos de Especificação" in content
    assert "Estratégias de Indexação de Código" in content


@pytest.mark.unit
def test_default_artifacts_contains_key_elements(
    repo_root: Path,
) -> None:
    template = (
        repo_root / "agents/default-artifacts/doc-readme.md"
    ).read_text(encoding="utf-8")

    for element in (
        "Modelo de Dados",
        "Threat Model",
        "Plano de Testes",
        "ADR (Arquitetura)",
    ):
        assert element in template


@pytest.mark.unit
def test_default_artifacts_contains_specs_destination(
    repo_root: Path,
) -> None:
    content = (
        repo_root / "agents/default-artifacts/doc-readme.md"
    ).read_text(encoding="utf-8")

    assert "docs/specs/" in content


@pytest.mark.unit
def test_testes_produto_snippet_lists_specialties_orchestrator_and_spec_link(
    repo_root: Path,
) -> None:
    content = (
        repo_root / "agents/default-artifacts/testes-por-especialidade.md"
    ).read_text(encoding="utf-8")

    assert "## Testes por Especialidade" in content
    for specialty in SPECIALTIES:
        assert f"| {specialty} " in content
    for script in SPECIALTY_SCRIPTS:
        assert script in content
    assert "testes-produto" in content
    assert "docs/testes-produto.md" in content
    assert "harness/agregar" not in content
    assert '"prompt"' not in content
    assert "O que deve conter" not in content


@pytest.mark.unit
def test_testes_produto_spec_template_has_specialty_subsections(
    repo_root: Path,
) -> None:
    content = (
        repo_root / "agents/default-artifacts/testes-produto.md"
    ).read_text(encoding="utf-8")

    for specialty in SPECIALTIES:
        assert f"## {specialty}" in content
    for heading in (
        "Ferramentas",
        "Critérios",
        "Orçamento",
        "O que deve conter",
    ):
        assert heading in content
    assert "testes-produto" in content
    assert "harness/agregar" not in content
    assert "pa11y" in content
    assert "axe-core" in content


@pytest.mark.unit
def test_instructions_template_covers_workflow_agents(
    repo_root: Path,
) -> None:
    content = (
        repo_root / "agents/default-artifacts/instrucoes-por-agente.md"
    ).read_text(encoding="utf-8")

    assert "## Instruções por Agente" in content
    for agent in WORKFLOW_AGENTS:
        assert f"### {agent}" in content
    assert "SEM INSTRUÇÕES A PEDIDO DO HUMANO" in content
    assert "testes-produto" not in content
    assert "testes-produto/backend" not in content
    assert "harness/agregar" not in content


@pytest.mark.unit
def test_curador_produto_does_not_contain_old_suite_interface(
    repo_root: Path,
) -> None:
    content = (repo_root / "agents/curador-produto.md").read_text(
        encoding="utf-8"
    )

    assert "harness/<agente>/<fase>" not in content


@pytest.mark.unit
def test_interface_testes_produto_describes_standard_json_interface(
    repo_root: Path,
) -> None:
    content = (
        repo_root / "agents/references/interface-testes-produto.md"
    ).read_text(encoding="utf-8")

    assert '"status"' in content
    assert '"findings"' in content
    assert '"prompt"' not in content
    assert "harness/agregar" not in content
    assert "testes-produto" in content


@pytest.mark.unit
def test_default_testes_produto_artifacts_do_not_cite_plan_ids(
    repo_root: Path,
) -> None:
    plan_id_pattern = re.compile(r"\bD(?:[1-9]|1[0-2])\b")
    artifact_paths = (
        "agents/default-artifacts/testes-por-especialidade.md",
        "agents/default-artifacts/testes-produto.md",
        "agents/default-artifacts/instrucoes-por-agente.md",
        "agents/references/interface-testes-produto.md",
    )
    for relative_path in artifact_paths:
        content = (repo_root / relative_path).read_text(encoding="utf-8")
        assert plan_id_pattern.search(content) is None, relative_path
