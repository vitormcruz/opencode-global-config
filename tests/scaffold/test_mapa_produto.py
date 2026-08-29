from io import StringIO
from pathlib import Path

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
def test_scaffold_fails_when_harness_value_is_missing() -> None:
    status, _, _ = run_scaffold("--harness")

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


@pytest.mark.unit
def test_harness_scaffold_creates_section(tmp_path: Path) -> None:
    destination = tmp_path / "AGENTS.md"
    destination.touch()

    status, _, _ = run_scaffold("--harness", str(destination))

    assert status == 0
    assert "## Harness por Agente" in destination.read_text(encoding="utf-8")


@pytest.mark.unit
def test_harness_scaffold_lists_all_required_agents(tmp_path: Path) -> None:
    destination = tmp_path / "AGENTS.md"

    status, _, _ = run_scaffold("--harness", str(destination))
    content = destination.read_text(encoding="utf-8")

    assert status == 0
    for agent in (
        "eng-software",
        "dba",
        "sec",
        "qa",
        "front",
        "rev",
        "curador-produto",
    ):
        assert f"| {agent} " in content


@pytest.mark.unit
def test_harness_scaffold_marks_non_executors_without_harness(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "AGENTS.md"

    status, _, _ = run_scaffold("--harness", str(destination))
    content = destination.read_text(encoding="utf-8")

    assert status == 0
    for agent in ("rev", "curador-produto"):
        assert (
            f"| {agent} | (sem harness) | SEM HARNESS A PEDIDO DO HUMANO"
            in content
        )


@pytest.mark.unit
def test_harness_scaffold_contains_default_executor_commands(tmp_path: Path) -> None:
    destination = tmp_path / "AGENTS.md"

    status, _, _ = run_scaffold("--harness", str(destination))
    content = destination.read_text(encoding="utf-8")

    assert status == 0
    for row in (
        "| eng-software | harness/eng-software | Testes, análise estática",
        "| dba | harness/dba | Validação de schema",
        "| sec | harness/sec | OWASP checks, secrets",
        "| qa | harness/qa | Cobertura, aceitação",
        "| front | harness/front | Linting, a11y",
    ):
        assert row in content


@pytest.mark.unit
def test_harness_scaffold_is_idempotent(tmp_path: Path) -> None:
    destination = tmp_path / "AGENTS.md"
    destination.touch()

    first_status, _, _ = run_scaffold("--harness", str(destination))
    second_status, _, _ = run_scaffold("--harness", str(destination))
    content = destination.read_text(encoding="utf-8")

    assert first_status == 0
    assert second_status == 0
    assert content.count("## Harness por Agente") == 1


@pytest.mark.unit
def test_harness_scaffold_contains_script_specification(tmp_path: Path) -> None:
    destination = tmp_path / "AGENTS.md"

    status, _, _ = run_scaffold("--harness", str(destination))
    content = destination.read_text(encoding="utf-8")

    assert status == 0
    assert "### Especificação dos Scripts de Harness" in content
    assert "## Agregador de Harness" in content
    assert "harness/agregar" in content
    assert "docs/harness-report/harness-report.md" in content
    assert "docs/" + "harness.md" not in content


@pytest.mark.unit
def test_harness_scaffold_describes_each_executor_script(tmp_path: Path) -> None:
    destination = tmp_path / "AGENTS.md"

    status, _, _ = run_scaffold("--harness", str(destination))
    content = destination.read_text(encoding="utf-8")

    assert status == 0
    for section in (
        "harness/eng-software",
        "harness/dba",
        "harness/sec",
        "harness/qa",
        "harness/front",
    ):
        assert f"#### {section}" in content


@pytest.mark.unit
def test_harness_scaffold_describes_standard_json_interface(tmp_path: Path) -> None:
    destination = tmp_path / "AGENTS.md"

    status, _, _ = run_scaffold("--harness", str(destination))
    content = destination.read_text(encoding="utf-8")

    assert status == 0
    assert "sem argumentos" in content
    assert "saída JSON" in content
    assert "exit code" in content


@pytest.mark.unit
def test_doc_and_harness_flags_create_both_scaffolds(tmp_path: Path) -> None:
    doc = tmp_path / "doc.md"
    agents = tmp_path / "AGENTS.md"

    status, _, _ = run_scaffold(
        "--doc",
        str(doc),
        "--harness",
        str(agents),
    )

    assert status == 0
    assert "## Definição de Escopo" in doc.read_text(encoding="utf-8")
    assert "## Harness por Agente" in agents.read_text(encoding="utf-8")


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
def test_harness_template_lists_required_agents(repo_root: Path) -> None:
    content = (
        repo_root / "agents/default-artifacts/harness-section.md"
    ).read_text(encoding="utf-8")

    for agent in (
        "eng-software",
        "dba",
        "sec",
        "qa",
        "front",
        "rev",
        "curador-produto",
    ):
        assert f"| {agent} " in content


@pytest.mark.unit
def test_curador_produto_does_not_contain_old_harness_interface(
    repo_root: Path,
) -> None:
    content = (repo_root / "agents/curador-produto.md").read_text(
        encoding="utf-8"
    )

    assert "harness/<agente>/<fase>" not in content


@pytest.mark.unit
def test_interface_harness_describes_standard_json_interface(
    repo_root: Path,
) -> None:
    content = (
        repo_root / "agents/references/interface-harness.md"
    ).read_text(encoding="utf-8")

    assert '"status"' in content
    assert '"findings"' in content
