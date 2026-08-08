"""Valida a estrutura dos agentes curador-produto e curador-produto-editor."""

import re
from pathlib import Path

import pytest


def agent_file(repo_root: Path, name: str) -> Path:
    """Retorna o arquivo de agente solicitado."""

    return repo_root / "agents" / f"{name}.md"


@pytest.mark.unit
def test_curador_produto_editor_file_exists(repo_root: Path) -> None:
    assert agent_file(repo_root, "curador-produto-editor").is_file()


@pytest.mark.unit
def test_curador_produto_editor_has_description_frontmatter(
    repo_root: Path,
) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )
    assert sum(line.startswith("description:") for line in content.splitlines()) >= 1


@pytest.mark.unit
def test_curador_produto_editor_does_not_reference_requirement_validation(
    repo_root: Path,
) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )
    assert re.search(r"validar requisitos", content, re.IGNORECASE) is None


@pytest.mark.unit
def test_curador_produto_editor_contains_readme_template_heading(
    repo_root: Path,
) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )
    assert "Elementos de Especificação" in content


@pytest.mark.unit
def test_curador_produto_editor_contains_json_harness_interface(
    repo_root: Path,
) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )
    assert '"status"' in content


@pytest.mark.unit
def test_curador_produto_editor_has_limits_section(repo_root: Path) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )
    assert any(line.startswith("## Limites") for line in content.splitlines())


@pytest.mark.unit
def test_curador_produto_editor_contains_scope_definition(repo_root: Path) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )
    assert "Definição de Escopo" in content


@pytest.mark.unit
def test_curador_produto_editor_contains_indexing_strategies(repo_root: Path) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )
    assert "Estratégias de Indexação" in content


@pytest.mark.unit
def test_curador_produto_does_not_contain_requirement_validation(
    repo_root: Path,
) -> None:
    content = agent_file(repo_root, "curador-produto").read_text(encoding="utf-8")
    assert re.search(r"Validar requisitos", content, re.IGNORECASE) is None


@pytest.mark.unit
def test_curador_produto_references_editor(repo_root: Path) -> None:
    content = agent_file(repo_root, "curador-produto").read_text(encoding="utf-8")
    assert "curador-produto-editor" in content


@pytest.mark.unit
def test_curador_produto_does_not_contain_product_map(repo_root: Path) -> None:
    content = agent_file(repo_root, "curador-produto").read_text(encoding="utf-8")
    assert "Mapa do Produto" not in content


@pytest.mark.unit
def test_editor_contains_phase_1_bootstrap(repo_root: Path) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )
    assert re.search(r"Fase 1.*Bootstrap", content) is not None


@pytest.mark.unit
def test_editor_contains_phase_2_readme_review(repo_root: Path) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )
    assert re.search(r"Fase 2.*Revisão do docs/README.md", content) is not None


@pytest.mark.unit
def test_editor_contains_phase_3_harness_review(repo_root: Path) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )
    assert re.search(r"Fase 3.*Revisão do Harness", content) is not None


@pytest.mark.unit
def test_editor_contains_phase_4_implementation(repo_root: Path) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )
    assert re.search(r"Fase 4.*Implementação", content) is not None


@pytest.mark.unit
def test_editor_prohibits_harness_scripts_before_phase_3(repo_root: Path) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )
    flattened = content.replace("\n", " ")
    assert "PROIBIDO** criar qualquer script de harness antes da" in flattened


@pytest.mark.unit
def test_editor_prohibits_batch_readme_edits(repo_root: Path) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )
    assert re.search(r"PROIBIDO.*editar.*docs/README.md.*em lote", content) is not None


@pytest.mark.unit
def test_editor_prohibits_ignoring_default_artifacts(repo_root: Path) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )
    assert re.search(r"PROIBIDO.*ignorar os default-artifacts", content) is not None


@pytest.mark.unit
def test_editor_prohibits_file_search_for_default_artifacts(
    repo_root: Path,
) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )
    assert re.search(r"PROIBIDO.*usar file_search", content) is not None


@pytest.mark.unit
def test_editor_references_default_artifacts_as_relative_path(
    repo_root: Path,
) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )
    assert re.search(r"default-artifacts/.*mesmo diretório", content) is not None


@pytest.mark.unit
def test_editor_does_not_reference_legacy_default_artifacts_path(
    repo_root: Path,
) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )
    assert "agents/default-artifacts" not in content
