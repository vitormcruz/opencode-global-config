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


@pytest.mark.unit
def test_editor_allows_only_harness_specialists(repo_root: Path) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )

    for agent in ("eng-software", "dba", "sec", "qa", "front", "rev"):
        assert f"    {agent}: allow" in content
    assert '    "*": deny' in content


@pytest.mark.unit
def test_editor_requires_five_questions_per_harness_check(repo_root: Path) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(content.split()).lower()

    for question in (
        "outro check aprovado não pega",
        "toolchain",
        "tempo esperado",
        "bloqueante ou melhoria",
        "fingerprint SHA-256",
    ):
        assert question.lower() in normalized
    assert "uma de cada vez" in normalized
    assert "acumula" in normalized
    assert "sem criar arquivo" in normalized


@pytest.mark.unit
def test_editor_documents_harness_time_budgets(repo_root: Path) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )

    for ceiling in ("< 15s", "< 30s", "< 3 min", "< 10 min"):
        assert ceiling in content


@pytest.mark.unit
def test_editor_spawns_specialist_before_implementing_check(repo_root: Path) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(content.split()).lower()

    assert "não escreve o check sozinho" in normalized
    assert "spawn" in normalized
    for briefing_item in (
        "interface JSON",
        "checks aprovados",
        "orçamento",
        "bloqueante vs melhoria",
        "afrouxar o gate",
    ):
        assert briefing_item.lower() in normalized


@pytest.mark.unit
def test_editor_documents_harness_interface_safety_contract(repo_root: Path) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(content.split()).lower()

    for requirement in (
        "UTF-8",
        "stderr",
        "retry",
        "até 3",
        "failOnViolation=false",
        "excluir teste",
        "fail-open",
        "cache sem fallback",
    ):
        assert requirement.lower() in normalized


@pytest.mark.unit
def test_editor_measures_before_recording_harness(repo_root: Path) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(content.split()).lower()

    assert "mede o tempo de parede" in normalized
    assert "só então grava" in normalized
    assert "tabela tempo × status" in normalized
    assert "fingerprint, retry ou retirada" in normalized


@pytest.mark.unit
def test_editor_requires_static_analysis_to_cover_test_code(repo_root: Path) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(content.split()).lower()

    assert "código de teste entra no mesmo scan" in normalized
    assert "mesmo nível de qualidade que produção" in normalized


@pytest.mark.unit
def test_editor_keeps_harness_catalog_as_reference(repo_root: Path) -> None:
    content = agent_file(repo_root, "curador-produto-editor").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(content.split()).lower()

    assert "catálogo é só como referência" in normalized
    assert "catálogo não grava check sozinho" in normalized
    assert "agents.md" in normalized
