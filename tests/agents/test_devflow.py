"""Valida o conteúdo do agente devflow."""

import re
from pathlib import Path

import pytest


def devflow_content(repo_root: Path) -> str:
    """Lê o agente devflow como texto UTF-8."""

    return (repo_root / "harness-conf/agents/devflow.md").read_text(
        encoding="utf-8"
    )


def question_protocol_content(repo_root: Path) -> str:
    """Lê o protocolo compartilhado de perguntas."""

    return (repo_root / "harness-conf/skills/question-orchestration/SKILL.md").read_text(
        encoding="utf-8"
    )


def framework_content(repo_root: Path) -> str:
    """Lê o Framework commitado, fonte de verdade do desenvolvimento."""

    return (
        repo_root / "docs/framework-desenvolvimento-agentico.md"
    ).read_text(encoding="utf-8")


@pytest.mark.unit
def test_devflow_has_mediation_section(repo_root: Path) -> None:
    assert "Função de mediação" in devflow_content(repo_root)


@pytest.mark.unit
def test_framework_agnosticism_does_not_name_devflow_in_specialists(
    repo_root: Path,
) -> None:
    content = framework_content(repo_root)

    assert "Apenas o `devflow` conhece o Fluxo." in content
    assert "não o mencionam e não encaminham pergunta nem falha a ele" in content
    assert "No Fluxo, o `devflow` sempre medeia." in content
    assert "o agente responde a quem o acionou e segue utilizável" in content


@pytest.mark.unit
def test_question_protocol_adapts_presentation_without_grill_me(
    repo_root: Path,
) -> None:
    content = question_protocol_content(repo_root)

    assert "Pergunta curta e objetiva" in content
    assert "Pergunta elaborada, múltipla ou volumosa" in content
    assert "grill-me" not in content


@pytest.mark.unit
def test_devflow_delegates_question_protocol_to_skill(
    repo_root: Path,
) -> None:
    content = devflow_content(repo_root)

    assert "question-orchestration" in content
    assert "fonte única" in content
    assert "no máximo 4 perguntas por rodada" not in content


@pytest.mark.unit
def test_devflow_keeps_its_operational_mediation_controls(
    repo_root: Path,
) -> None:
    content = devflow_content(repo_root)

    assert "grill-me" not in content
    assert "Checklist estrutural" in content
    assert "Máximo 2 rodadas" in content
    assert "Continuidade da mediação" in content
    assert re.search(
        r"Nunca encerre a mediação\s+por conta própria",
        content,
    ) is not None
    assert "`prompt-improver`" in content
    assert "autonomamente" in content
    assert "insumo original" in content
    assert "Não invente decisões" in content


@pytest.mark.unit
def test_devflow_does_not_reference_smart_planner(repo_root: Path) -> None:
    assert "smart-planner" not in devflow_content(repo_root)


@pytest.mark.unit
def test_framework_references_question_protocol_skill(
    repo_root: Path,
) -> None:
    framework = framework_content(repo_root)

    assert "question-orchestration" in framework
    assert "Perguntas dos agentes passam pelo `devflow`." in framework
    assert "grill-me" not in framework.lower()


@pytest.mark.unit
def test_devflow_mediates_curator_ownership(repo_root: Path) -> None:
    content = devflow_content(repo_root)
    normalized = " ".join(content.lower().split())

    assert "aciona e medeia a definição das diretrizes e regras de produto" in (
        normalized
    )
    assert "curador-produto" in content
    assert "não edita nem valida os artefatos das diretrizes e regras de produto" in (
        normalized
    )


@pytest.mark.unit
def test_devflow_mediates_product_rules_definition_without_editing_docs(
    repo_root: Path,
) -> None:
    content = devflow_content(repo_root)
    normalized = " ".join(content.lower().split())

    assert "aciona e medeia a definição das diretrizes e regras de produto" in (
        normalized
    )
    assert "não edita nem valida os artefatos das diretrizes e regras de produto" in (
        normalized
    )
    assert "AGENTS.md" in content
    assert "docs/README.md" not in content
    assert "curador-produto: allow" in content


@pytest.mark.unit
def test_devflow_contract_has_item_six(repo_root: Path) -> None:
    content = devflow_content(repo_root)
    assert re.search(r"^6\.", content, re.MULTILINE) is not None
    assert "Não precisa concluir a tarefa" in content


@pytest.mark.unit
def test_devflow_informs_spawned_agents_of_evidence_phase(
    repo_root: Path,
) -> None:
    content = devflow_content(repo_root)
    normalized = " ".join(content.lower().split())

    assert (
        "informar a cada agente acionado o valor de `<fase>` do título "
        "`## evidências de testes — <fase>`, conforme definido pelo framework"
        in normalized
    )


@pytest.mark.unit
def test_devflow_contract_does_not_instruct_agents_to_use_grill_me(
    repo_root: Path,
) -> None:
    lines = devflow_content(repo_root).splitlines()
    try:
        start = next(
            index
            for index, line in enumerate(lines)
            if "Contrato com agentes spawnados" in line
        )
    except StopIteration:
        start = len(lines)

    contract_window = "\n".join(lines[start : start + 21])
    assert "grill-me" not in contract_window


@pytest.mark.unit
def test_devflow_construction_routes_product_rules_when_in_scope(
    repo_root: Path,
) -> None:
    content = devflow_content(repo_root)
    lower = " ".join(content.lower().split())

    assert "evidências de harness" not in lower or "fase testes" in lower
    assert "sem modificações — harness não executado" not in content
    assert "`curador-produto`" in content
    assert "4.1" in content
    assert "`dba`" in content
    assert "`front`" in content
    assert "normaliza" in lower
    assert "se esse for o escopo" not in lower


@pytest.mark.unit
def test_devflow_validates_product_rules_before_scope_confirmation(
    repo_root: Path,
) -> None:
    content = devflow_content(repo_root)

    assert "Verificação inicial das Diretrizes e Regras de Produto" in content
    assert "Ao receber uma solicitação e antes de confirmar ou completar o" in content
    assert (
        "Deseja transformar o escopo deste ciclo na definição das"
        in content
    )
    assert "Status: PLANEJAMENTO" in content
    assert "Se a resposta for sim" in content
    assert "curador-produto" in content
    assert "docs/README.md" not in content
    assert "Especificação do Produto" in content
    assert "Diretrizes e Regras de Produto" in content
    assert "### 1. INICIALIZAÇÃO" in content
    assert "### 2. PLANEJAMENTO" in content
    assert content.index("Verificação inicial das Diretrizes") < content.index(
        "### Definição de escopo antes do plano"
    )


@pytest.mark.unit
def test_devflow_defines_scope_before_creating_plan(repo_root: Path) -> None:
    content = devflow_content(repo_root)

    assert "## Definição de escopo antes do plano" in content
    assert "Só depois que o humano confirmar que o escopo está definido" in content
    assert "crie o Arquivo de Planejamento com" in content
    assert "`Status: PLANEJAMENTO`" in content
    assert "registre nele o escopo recebido, a verificação das Diretrizes" in content


@pytest.mark.unit
def test_devflow_requires_human_confirmation_before_rereview(
    repo_root: Path,
) -> None:
    content = devflow_content(repo_root)
    normalized = " ".join(content.split())

    assert normalized.count('**"Resubmeter para revisão?"**') >= 2
    assert normalized.count("Somente uma resposta afirmativa") >= 2
    assert "não aciona uma nova revisão automaticamente" in normalized
    assert "Humano controla re-revisões" in content


@pytest.mark.unit
def test_devflow_requires_deterministic_retries_and_blocks_finalization(
    repo_root: Path,
) -> None:
    content = devflow_content(repo_root)
    normalized = " ".join(content.lower().split())

    assert "reexecução obrigatória dos testes automáticos determinísticos" in (
        normalized
    )
    assert "não pode avançar para `status: finalização` enquanto houver falha" in (
        normalized
    )
    assert "três falhas consecutivas" in normalized
    assert "análise diagnóstica adicional" in normalized
    assert "sem aprovação dos testes" in normalized


@pytest.mark.unit
def test_devflow_mediates_the_three_option_refactoring_gate(
    repo_root: Path,
) -> None:
    content = devflow_content(repo_root)
    normalized = " ".join(content.lower().split())

    assert "gate de refatoração" in normalized
    assert "manter o plano e ajustar apenas a implementação" in normalized
    assert "aprovar um ajuste mínimo do plano e registrá-lo" in normalized
    assert "retornar ao planejamento" in normalized
    assert "medeia a decisão" in normalized
    assert "executor não escolhe" in normalized
    assert "só prossegue depois da resposta humana" in normalized


@pytest.mark.unit
def test_devflow_does_not_silently_skip_agent_failures(
    repo_root: Path,
) -> None:
    content = devflow_content(repo_root)
    normalized = " ".join(content.lower().split())

    assert "falha de agente" in normalized
    assert "não pode ser pulada silenciosamente" in normalized
    assert "corrigir e retentar" in normalized
    assert "encaminhe o trabalho a outro agente" in normalized
    assert "pular com registro" not in normalized


@pytest.mark.unit
def test_devflow_has_human_stop_gate_for_finalization_revalidation(
    repo_root: Path,
) -> None:
    content = devflow_content(repo_root)
    normalized = " ".join(content.split())

    assert '"Continuar a revalidação?"' in normalized
    assert "interromper o Fluxo" in normalized
    assert "registrar as lacunas restantes" in normalized
    assert "preservar o Arquivo de Planejamento" in normalized


@pytest.mark.unit
def test_devflow_applies_instance_policy(repo_root: Path) -> None:
    content = devflow_content(repo_root)
    normalized = " ".join(content.split())

    assert "unidade de trabalho coerente" in content
    assert (
        "**Criar** para toda revisão, sem reutilizar a instância do executor"
        in normalized
    )
    assert (
        "Quando houver dúvida entre reutilizar e criar, crie uma instância nova"
        in normalized
    )
    assert "Só faça o spawn ou a retomada depois" in content


@pytest.mark.unit
def test_scope_workflow_is_independent_and_has_no_plan_contract(
    repo_root: Path,
) -> None:
    content = (
        repo_root / "docs" / "workflow-definicao-escopo.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(content.split())

    assert "devflow" not in content
    assert "Arquivo de Planejamento" not in content
    assert "seção Definição de Escopo da Especificação do Produto" in content
    assert "nenhum arquivo é criado" in normalized


@pytest.mark.unit
def test_framework_links_scope_workflow_from_ideation(
    repo_root: Path,
) -> None:
    content = framework_content(repo_root)
    normalized = " ".join(content.split())

    assert "[Consultar o Fluxo de Definição de Escopo]" in content
    assert "./workflow-definicao-escopo.md" in content
    assert "O plano só nasce depois dessa definição." in normalized


@pytest.mark.unit
def test_devflow_findings_flow_rev_to_specialist(repo_root: Path) -> None:
    content = devflow_content(repo_root)

    assert "rev" in content
    assert "especialista" in content
    assert "achado" in content.lower()
    assert "nova instância" in content


@pytest.mark.unit
def test_devflow_no_debug_mode_or_legacy_references(repo_root: Path) -> None:
    content = devflow_content(repo_root)

    assert "Modo Debug" not in content
    assert "DevFlowNotes" not in content
    assert "val-harness" not in content
    assert "curador-produto-editor" not in content


@pytest.mark.unit
def test_devflow_evidence_validated_at_end_of_test_phase(
    repo_root: Path,
) -> None:
    content = devflow_content(repo_root)
    lower = " ".join(content.lower().split())

    assert "curador-produto" in content
    assert "testes-produto" in content
    assert "roteador stateless" in lower
    assert "val-harness" not in content
    assert "re-executar" in lower


@pytest.mark.unit
def test_devflow_routes_suite_failure_by_specialty(repo_root: Path) -> None:
    content = devflow_content(repo_root)
    lower = " ".join(content.lower().split())

    assert "backend" in lower and "eng-software" in lower
    assert "dados" in lower and "dba" in lower
    assert "segurança" in lower and "sec" in lower
    assert "frontend" in lower and "front" in lower


def model_selection_window(repo_root: Path) -> str:
    """Extrai a janela da seção 'Seleção de modelo por fase'."""

    lines = devflow_content(repo_root).splitlines()
    try:
        start = next(
            index
            for index, line in enumerate(lines)
            if "Seleção de modelo por fase" in line
        )
    except StopIteration:
        pytest.fail("seção 'Seleção de modelo por fase' ausente no devflow")
    return "\n".join(lines[start : start + 30])


@pytest.mark.unit
def test_devflow_model_selection_suggests_pattern_and_allows_choice(
    repo_root: Path,
) -> None:
    window = model_selection_window(repo_root)
    lower = " ".join(window.lower().split())

    assert "sugere um padrão" in lower
    assert "planejamento, execução, testes e revisão" in lower
    assert "define como preferir" in lower
    assert "arranjo próprio" in lower
    assert "mapa combinado" in lower


@pytest.mark.unit
def test_devflow_model_selection_has_no_rigid_numbered_menu(
    repo_root: Path,
) -> None:
    window = model_selection_window(repo_root)

    assert "1-VALIDAÇÃO" not in window
    assert "7-FINALIZAÇÃO" not in window
    assert "Modelo atual para todas as fases" not in window
    assert re.search(r"^1\. ", window, re.MULTILINE) is None


@pytest.mark.unit
def test_devflow_model_selection_keeps_pause_before_model_change(
    repo_root: Path,
) -> None:
    window = model_selection_window(repo_root)
    lower = " ".join(window.lower().split())

    assert "pausa antes de fases" in lower
    assert "`/model`" in window
    assert "`model`" in window
    assert "solicite a troca ao humano" in lower
