"""Contratos dos gates mediados pelo agente devflow."""

from pathlib import Path

import pytest


def _devflow(repo_root: Path) -> str:
    """Lê o contrato operacional do devflow."""

    return (repo_root / "harness-conf/agents/devflow.md").read_text(
        encoding="utf-8"
    )


def _section(content: str, start: str, end: str) -> str:
    """Extrai uma seção delimitada por headings estáveis."""

    start_index = content.index(start)
    end_index = content.index(end, start_index + len(start))
    return content[start_index:end_index]


@pytest.mark.unit
def test_devflow_routes_test_execution_in_the_defined_order(
    repo_root: Path,
) -> None:
    content = _devflow(repo_root)
    tests = _section(
        content,
        "### 6. TESTES",
        "## Fluxo posterior — FINALIZAÇÃO",
    )

    steps = (
        "| 6.1 | `qa` |",
        "| 6.2 | `sec` |",
        "| 6.3 | `curador-produto` |",
    )
    positions = [tests.index(step) for step in steps]

    assert positions == sorted(positions)
    normalized = " ".join(tests.lower().split())
    assert "testes-produto" in normalized
    assert "validar a evidência do agregador" in normalized


@pytest.mark.unit
def test_curador_is_called_for_aggregator_evidence_only_when_requested(
    repo_root: Path,
) -> None:
    content = (
        repo_root / "harness-conf/agents/curador-produto.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(content.lower().split())

    assert "evidência do agregador" in normalized
    assert "quando solicitado" in normalized
    assert "não inicia revalidação" in normalized
    assert "não exclui arquivos por conta própria" in normalized
    assert "ao fim de um ciclo de desenvolvimento" not in normalized
    assert "### 6. revisão final de documentação" not in normalized


@pytest.mark.unit
def test_plan_review_refusal_still_requires_plan_approval_before_construction(
    repo_root: Path,
) -> None:
    content = _devflow(repo_root)
    plan_review = _section(
        content,
        "### 3. REVISÃO DO PLANO",
        "### 4. CONSTRUÇÃO",
    )

    step_positions = [
        plan_review.index(f"| 3.{step} |")
        for step in ("1", "2", "3", "4")
    ]
    assert step_positions == sorted(step_positions)

    normalized = " ".join(plan_review.lower().split())
    refusal = (
        "se o humano recusar, o fluxo segue para a apresentação e aprovação "
        "do plano"
    )
    assert refusal in normalized
    assert "sem essa resposta, mantém `status: revisão do plano`" not in (
        normalized
    )
    assert "sem aprovação, o status permanece `revisão do plano`." in (
        normalized
    )

    refusal_position = normalized.index(refusal)
    approval_position = normalized.index("a aprovação humana é obrigatória")
    construction_position = normalized.index("status: construção")
    assert refusal_position < approval_position < construction_position


@pytest.mark.unit
def test_plan_review_requires_affirmative_rereview_but_does_not_skip_approval(
    repo_root: Path,
) -> None:
    content = _devflow(repo_root)
    plan_review = _section(
        content,
        "### 3. REVISÃO DO PLANO",
        "### 4. CONSTRUÇÃO",
    )
    normalized = " ".join(plan_review.split())

    assert '**"Resubmeter para revisão?"**' in normalized
    assert "Somente uma resposta afirmativa permite nova instância" in (
        normalized
    )
    assert "apresenta o plano consolidado ao humano" in normalized
    assert "A aprovação humana é obrigatória antes de `Status: CONSTRUÇÃO`" in (
        normalized
    )


@pytest.mark.unit
def test_refactoring_gate_is_mediated_and_has_three_outcomes(
    repo_root: Path,
) -> None:
    content = _devflow(repo_root)
    gate = _section(
        content,
        "#### Gate de refatoração",
        "#### Re-revisão",
    )
    normalized = " ".join(gate.split())

    options = (
        "1. manter o plano e ajustar apenas a implementação;",
        "2. aprovar um ajuste mínimo do plano e registrá-lo no Arquivo de",
        "3. retornar ao Planejamento para revisar premissas, comportamento ou",
    )
    positions = [normalized.index(option) for option in options]

    assert positions == sorted(positions)
    assert normalized.index("o `devflow` medeia") < positions[0]
    assert normalized.index("O executor não escolhe") > positions[-1]
    assert "só prossegue depois da resposta humana" in normalized


@pytest.mark.unit
def test_deterministic_failure_retries_block_finalization(
    repo_root: Path,
) -> None:
    content = _devflow(repo_root)
    tests = _section(
        content,
        "### 6. TESTES",
        "## Fluxo posterior — FINALIZAÇÃO",
    )
    normalized = " ".join(tests.lower().split())

    retry_position = normalized.index(
        "reexecução obrigatória dos testes automáticos determinísticos"
    )
    failure_position = normalized.index(
        "uma falha não pode ser aceita ou contornada"
    )
    blocked_position = normalized.index(
        "não atualiza o status para `status: finalização` enquanto houver falha"
    )
    diagnostic_position = normalized.index("três falhas consecutivas")
    approved_position = normalized.index("com testes aprovados e evidência completa")
    finalization_position = normalized.rindex("`status: finalização`")

    assert retry_position < failure_position < blocked_position
    assert blocked_position < diagnostic_position < approved_position
    assert approved_position < finalization_position
    assert "sem aprovação dos testes" in normalized


@pytest.mark.unit
def test_revalidation_refusal_preserves_lacunas_without_completion(
    repo_root: Path,
) -> None:
    content = _devflow(repo_root)
    finalization = content.split(
        "## Fluxo posterior — FINALIZAÇÃO",
        1,
    )[1]
    stop_branch = _section(
        finalization,
        "4. Se o humano recusar",
        "5. Quando o curador retornar OK",
    )

    assert finalization.index('"Continuar a revalidação?"') < finalization.index(
        "4. Se o humano recusar"
    )
    assert "registrar as lacunas restantes" in stop_branch
    assert "preservar o Arquivo de Planejamento" in stop_branch
    assert "sem declarar conclusão" in stop_branch
    assert "exclu" not in stop_branch.lower()
