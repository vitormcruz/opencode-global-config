"""Valida a estrutura do agente unificado curador-produto."""

import re
from pathlib import Path

import pytest


def agent_file(repo_root: Path, name: str) -> Path:
    """Retorna o arquivo de agente solicitado."""

    return repo_root / "harness-conf" / "agents" / f"{name}.md"


@pytest.fixture
def curador_content(repo_root: Path) -> str:
    return agent_file(repo_root, "curador-produto").read_text(
        encoding="utf-8"
    )


@pytest.fixture
def curador_normalized(curador_content: str) -> str:
    return " ".join(curador_content.split()).lower()


# --- Existência e estrutura básica ---


@pytest.mark.unit
def test_curador_produto_file_exists(repo_root: Path) -> None:
    assert agent_file(repo_root, "curador-produto").is_file()


@pytest.mark.unit
def test_curador_produto_has_description_frontmatter(
    curador_content: str,
) -> None:
    assert sum(
        line.startswith("description:")
        for line in curador_content.splitlines()
    ) >= 1


@pytest.mark.unit
def test_curador_produto_is_primary(curador_content: str) -> None:
    assert "mode: primary" in curador_content


@pytest.mark.unit
def test_curador_produto_has_limits_section(
    curador_content: str,
) -> None:
    assert any(
        line.startswith("## Limites")
        for line in curador_content.splitlines()
    )


@pytest.mark.unit
def test_curador_produto_under_350_lines(repo_root: Path) -> None:
    lines = agent_file(repo_root, "curador-produto").read_text(
        encoding="utf-8"
    ).splitlines()
    assert len(lines) <= 350


# --- Capacidades absorvidas do editor ---


@pytest.mark.unit
def test_curador_produto_contains_readme_template(
    curador_content: str,
) -> None:
    assert "Elementos de Especificação" in curador_content


@pytest.mark.unit
def test_curador_produto_contains_scope_definition(
    curador_content: str,
) -> None:
    assert "Definição de Escopo" in curador_content


@pytest.mark.unit
def test_curador_produto_contains_indexing_strategies(
    curador_content: str,
) -> None:
    assert "Estratégias de Indexação" in curador_content


@pytest.mark.unit
def test_curador_produto_references_testes_produto_interface(
    curador_content: str,
) -> None:
    assert "interface-testes-produto.md" in curador_content


@pytest.mark.unit
def test_curador_produto_references_default_artifacts(
    repo_root: Path,
    curador_content: str,
) -> None:
    assert "default-artifacts/doc-readme.md" in curador_content
    assert "default-artifacts/testes-por-especialidade.md" in curador_content
    assert "default-artifacts/instrucoes-por-agente.md" in curador_content
    spec = (
        repo_root / "harness-conf/agents/default-artifacts/doc-readme.md"
    ).read_text(
        encoding="utf-8"
    )
    assert "testes-produto/target/" in spec
    assert "harness/target/" not in spec
    assert not (
        repo_root / "harness-conf/agents/default-artifacts/testes-produto.md"
    ).exists()


@pytest.mark.unit
def test_curador_produto_prohibits_batch_readme_edits(
    curador_normalized: str,
) -> None:
    assert "não edita em lote sem aprovação" in curador_normalized


@pytest.mark.unit
def test_curador_produto_prohibits_inventing_suite_checks(
    curador_normalized: str,
) -> None:
    assert "não inventa check" in curador_normalized


@pytest.mark.unit
def test_curador_produto_prohibits_cutting_checks(
    curador_normalized: str,
) -> None:
    assert "não corta verificação" in curador_normalized


@pytest.mark.unit
def test_curador_produto_prohibits_ignoring_default_artifacts(
    curador_normalized: str,
) -> None:
    assert "proibido ignorar os default-artifacts" in curador_normalized


@pytest.mark.unit
def test_curador_produto_prohibits_file_search_for_default_artifacts(
    curador_normalized: str,
) -> None:
    assert "proibido usar file_search" in curador_normalized


@pytest.mark.unit
def test_curador_produto_persists_and_returns_after_approval(
    curador_normalized: str,
    curador_content: str,
) -> None:
    assert "persista o resultado" in curador_normalized
    assert "retorne o resumo ao solicitante" in curador_normalized
    assert "docs/README.md#testes-por-especialidade" in curador_content
    assert "docs/testes-produto.md" not in curador_content.split(
        "PROIBIDO gravar spec de suíte em arquivo separado"
    )[0]


@pytest.mark.unit
def test_curador_produto_documents_two_test_levels(
    curador_normalized: str,
) -> None:
    assert "dois níveis de teste" in curador_normalized
    assert "testes da aplicação" in curador_normalized
    assert "testes dos scripts de teste" in curador_normalized
    assert "especificação executável" in curador_normalized
    assert "somente quando os scripts mudam" in curador_normalized
    assert "nunca no ciclo normal" in curador_normalized


@pytest.mark.unit
def test_curador_produto_forbids_separate_spec_file(
    curador_content: str,
) -> None:
    assert "PROIBIDO gravar spec de suíte em arquivo separado" in (
        curador_content
    )
    assert "único spec" in curador_content


@pytest.mark.unit
def test_curador_produto_requires_static_analysis_to_cover_test_code(
    repo_root: Path,
) -> None:
    content = (
        repo_root / "harness-conf" / "agents/references/interface-testes-produto.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(content.split()).lower()
    assert "código de teste entra no mesmo scan" in normalized
    assert "mesmo nível de qualidade que produção" in normalized
    assert "testes-produto/target/" in content
    assert "harness/target/" not in content


@pytest.mark.unit
def test_curador_produto_requires_approval_per_section(
    curador_normalized: str,
) -> None:
    assert (
        "aprovação explícita" in curador_normalized
        and "seção" in curador_normalized
    )


@pytest.mark.unit
def test_curador_produto_documents_suite_interview(
    curador_normalized: str,
) -> None:
    for item in (
        "ferramenta",
        "toolchain",
        "tempo",
        "bloqueante",
        "fingerprint",
    ):
        assert item in curador_normalized


@pytest.mark.unit
def test_curador_produto_documents_time_budgets(
    curador_content: str,
) -> None:
    assert "agents/references/interface-testes-produto.md" in curador_content


@pytest.mark.unit
def test_curador_produto_does_not_spawn_agents(
    curador_normalized: str,
) -> None:
    assert "persista o resultado" in curador_normalized
    assert "retorne o resumo" in curador_normalized


@pytest.mark.unit
def test_curador_produto_catalog_as_reference(
    curador_normalized: str,
) -> None:
    assert "catálogo" in curador_normalized
    assert "testes-produto-catalog" in curador_normalized


# --- Valida??o de evid?ncia ---


@pytest.mark.unit
def test_curador_produto_validates_orchestrator_evidence(
    curador_normalized: str,
) -> None:
    assert "orquestrador" in curador_normalized
    assert "testes-produto" in curador_normalized
    assert "fase testes" in curador_normalized


@pytest.mark.unit
def test_curador_produto_runs_aggregator_before_validation(
    curador_normalized: str,
) -> None:
    assert "testes-produto" in curador_normalized
    assert "evidência" in curador_normalized


@pytest.mark.unit
def test_curador_produto_reports_lacuna(
    curador_normalized: str,
) -> None:
    assert "lacuna" in curador_normalized


@pytest.mark.unit
def test_curador_produto_has_validation_format(
    curador_content: str,
) -> None:
    assert "Validação de Testes" in curador_content
    assert "Validação de Harness" not in curador_content
    assert "Harness no" not in curador_content
    assert "`testes-produto/`" in curador_content
    assert "Veredicto" in curador_content


# --- Regras de segurança e contrato ---


@pytest.mark.unit
def test_curador_produto_does_not_validate_merit_of_own_edits(
    curador_normalized: str,
) -> None:
    assert "não valida mérito do que editou" in curador_normalized


@pytest.mark.unit
def test_curador_produto_never_commits(
    curador_normalized: str,
) -> None:
    assert "nunca commita" in curador_normalized


@pytest.mark.unit
def test_curador_produto_does_not_reference_requirement_validation(
    curador_content: str,
) -> None:
    assert (
        re.search(r"validar requisitos", curador_content, re.IGNORECASE)
        is None
    )


@pytest.mark.unit
def test_curador_produto_does_not_contain_product_map(
    curador_content: str,
) -> None:
    assert "Mapa do Produto" not in curador_content


@pytest.mark.unit
def test_curador_produto_has_documentation_skill(
    curador_content: str,
) -> None:
    assert "documentation-and-adrs" in curador_content


@pytest.mark.unit
def test_curador_produto_has_catalog_conditional(
    curador_content: str,
) -> None:
    assert "testes-produto-catalog" in curador_content


@pytest.mark.unit
def test_curador_produto_does_not_validate_after_construction(
    curador_normalized: str,
) -> None:
    assert "fase testes" in curador_normalized
    assert "não valida evidências na construção" in curador_normalized or (
        "não valida" in curador_normalized
        and "construção" in curador_normalized
    )


@pytest.mark.unit
def test_curador_produto_interviews_spec_then_instructions(
    curador_content: str,
) -> None:
    assert "Instruções por Agente" in curador_content
    assert "pasta" in curador_content.lower()
    assert "docs/" in curador_content
    assert "pa11y" in curador_content
    assert "axe-core" in curador_content
    assert "o harness efetivo fica no" not in curador_content.lower()
    assert "não é copiada para o" in curador_content.lower()


# --- Remoção dos agentes antigos ---


@pytest.mark.unit
def test_curador_produto_editor_removed(repo_root: Path) -> None:
    assert not agent_file(repo_root, "curador-produto-editor").exists()


@pytest.mark.unit
def test_val_harness_removed(repo_root: Path) -> None:
    assert not agent_file(repo_root, "val-harness").exists()


# --- Referências e consistência ---


@pytest.mark.unit
def test_curador_produto_does_not_reference_old_agents(
    curador_content: str,
) -> None:
    assert "curador-produto-editor" not in curador_content
    assert "val-harness" not in curador_content


@pytest.mark.unit
def test_mensagens_curadoria_references_curador_produto(
    repo_root: Path,
) -> None:
    content = (
        repo_root / "harness-conf/agents/references/mensagens-curadoria.md"
    ).read_text(encoding="utf-8")
    assert "curador-produto" in content
    assert "curador-produto-editor" not in content


@pytest.mark.unit
def test_mensagens_curadoria_documents_single_artifact(
    repo_root: Path,
) -> None:
    content = (
        repo_root / "harness-conf/agents/references/mensagens-curadoria.md"
    ).read_text(encoding="utf-8")

    assert "4 seções obrigatórias" in content
    assert "Testes por Especialidade" in content
    assert "tabela índice" in content
    assert "docs/testes-produto.md" not in content


@pytest.mark.unit
def test_interface_testes_produto_reference_exists(repo_root: Path) -> None:
    assert (
        repo_root / "harness-conf" / "agents/references/interface-testes-produto.md"
    ).is_file()


@pytest.mark.unit
def test_testes_produto_artifacts_do_not_expose_plan_ids(
    repo_root: Path,
) -> None:
    artifact_paths = (
        "harness-conf/agents/curador-produto.md",
        "harness-conf/skills/testes-produto-catalog/SKILL.md",
    )
    plan_id_pattern = re.compile(r"\bD(?:[1-9]|1[0-2])\b", re.IGNORECASE)

    for relative_path in artifact_paths:
        content = (repo_root / relative_path).read_text(encoding="utf-8")
        assert plan_id_pattern.search(content) is None, relative_path
        assert (
            re.search(r"ver o plano", content, re.IGNORECASE) is None
        ), relative_path
