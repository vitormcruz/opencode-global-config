"""Valida o conteúdo do agente smart-planner e sua restrição no AGENTS.md."""

import re
from pathlib import Path

import pytest


def smart_planner_file(repo_root: Path) -> Path:
    """Retorna o arquivo do agente smart-planner."""

    return repo_root / "agents" / "smart-planner.md"


def collapsed(text: str) -> str:
    """Junta quebras de linha para comparar frases do contrato."""

    return re.sub(r"\s+", " ", text)


@pytest.mark.unit
def test_smart_planner_file_exists(repo_root: Path) -> None:
    assert smart_planner_file(repo_root).is_file()


@pytest.mark.unit
def test_smart_planner_frontmatter_has_description(repo_root: Path) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert re.search(r"^description:", content, re.MULTILINE) is not None


@pytest.mark.unit
def test_smart_planner_frontmatter_has_primary_mode(repo_root: Path) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert re.search(r"^mode: primary", content, re.MULTILINE) is not None


@pytest.mark.unit
def test_smart_planner_frontmatter_has_temperature(repo_root: Path) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert re.search(r"^temperature:", content, re.MULTILINE) is not None


@pytest.mark.unit
def test_smart_planner_frontmatter_allows_edit_permission(repo_root: Path) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert re.search(r"edit: allow", content) is not None


@pytest.mark.unit
def test_smart_planner_frontmatter_allows_bash_permission(repo_root: Path) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert re.search(r"bash: allow", content) is not None


@pytest.mark.unit
def test_smart_planner_frontmatter_denies_webfetch_permission(repo_root: Path) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert re.search(r"webfetch: deny", content) is not None


@pytest.mark.unit
def test_smart_planner_frontmatter_allows_subagent_permission(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert re.search(r'"\*": allow', content) is not None


@pytest.mark.unit
def test_smart_planner_delegates_question_protocol_to_skill(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")

    assert "question-orchestration" in content
    assert "fonte única" in content
    assert "## Modo de Operação" not in content
    assert "## Triagem de Contexto Inicial" not in content


@pytest.mark.unit
def test_smart_planner_has_behavioral_restriction_section(
    repo_root: Path,
) -> None:
    assert "## Restri" in smart_planner_file(repo_root).read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_smart_planner_has_incremental_saving_section(repo_root: Path) -> None:
    assert "## Salvamento Incremental" in smart_planner_file(repo_root).read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_smart_planner_has_decision_and_commit_gate(repo_root: Path) -> None:
    assert "## Gate de Decis" in smart_planner_file(repo_root).read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_smart_planner_leaves_commit_checkpoints_contextual(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "### Checkpoints de commit" in content
    assert "não há quantidade fixa" in content.lower()
    assert "obrigação de criar um commit após" in content
    assert "git-workflow-and-versioning" in content


@pytest.mark.unit
def test_smart_planner_creates_skeleton_before_first_question(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "Antes da primeira pergunta" in content
    assert "skeleton" in content


@pytest.mark.unit
def test_smart_planner_does_not_require_automatic_commits(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "commita automaticamente" not in content
    assert "commits são automáticos" not in content


@pytest.mark.unit
def test_smart_planner_keeps_its_checkpoint_guidance_after_delegating_questions(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "### Checkpoints de commit" in content
    assert "git-workflow-and-versioning" in content


@pytest.mark.unit
def test_smart_planner_has_stopping_conditions_section(repo_root: Path) -> None:
    assert "## Stopping Conditions" in smart_planner_file(repo_root).read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_smart_planner_has_execution_orchestration_section(repo_root: Path) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")

    assert "## Orquestração de Execução e Revisão" in content
    assert "## Handoff" not in content


@pytest.mark.unit
def test_smart_planner_has_limits_section(repo_root: Path) -> None:
    assert "## Limites" in smart_planner_file(repo_root).read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_smart_planner_has_replan_protocol_section(repo_root: Path) -> None:
    assert "## Protocolo de Replan" in smart_planner_file(repo_root).read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_smart_planner_has_independent_review_section(repo_root: Path) -> None:
    assert "## Revisão Independente" in smart_planner_file(repo_root).read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_smart_planner_uses_adaptive_question_blocks(repo_root: Path) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "question-orchestration" in content
    assert "entre 1 e 4 perguntas" not in content


@pytest.mark.unit
def test_smart_planner_references_planning_skill(repo_root: Path) -> None:
    assert "planning-and-task-breakdown" in smart_planner_file(repo_root).read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_smart_planner_references_git_workflow_skill(repo_root: Path) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "git-workflow-and-versioning" in content


@pytest.mark.unit
def test_smart_planner_allows_commit_checkpoints_to_group_tasks(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "duas ou três" in content
    assert "não\n  reorganize tasks para forçar commits" in content


@pytest.mark.unit
def test_smart_planner_uses_question_orchestration(
    repo_root: Path,
) -> None:
    assert "question-orchestration" in smart_planner_file(repo_root).read_text(
        encoding="utf-8"
    )


@pytest.mark.unit
def test_smart_planner_uses_concise_commits_without_caveman(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "caveman" not in content
    assert "resumo conciso" in collapsed(content)


@pytest.mark.unit
def test_smart_planner_does_not_generate_handoff_prompts(repo_root: Path) -> None:
    content = collapsed(
        smart_planner_file(repo_root).read_text(encoding="utf-8")
    )

    assert "prompt-improver" not in content
    assert "não gere prompts ou arquivos de handoff" in content
    assert "Não cria prompts nem arquivos de handoff" in content


@pytest.mark.unit
def test_smart_planner_uses_git_skill_for_commit_checkpoints(
    repo_root: Path,
) -> None:
    content = collapsed(
        smart_planner_file(repo_root).read_text(encoding="utf-8")
    )
    assert "git-workflow-and-versioning" in content
    assert "Não há quantidade fixa de decisões por checkpoint" in content
    assert "Nunca inclua alterações alheias da worktree" in content
    assert "coerência narrativa" not in content
    assert "--amend" not in content


@pytest.mark.unit
def test_smart_planner_never_edits_application_code(repo_root: Path) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert re.search(r"NUNCA.*edita", content) is not None


@pytest.mark.unit
def test_smart_planner_uses_accented_portuguese(repo_root: Path) -> None:
    assert "PT-BR" in smart_planner_file(repo_root).read_text(encoding="utf-8")


@pytest.mark.unit
def test_agents_md_contains_smart_planner_behavioral_restriction(
    repo_root: Path,
) -> None:
    content = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    pattern = r"smart-planner.*nunca.*edita codigo|SmartPlanner.*Restricao"
    assert re.search(pattern, content, re.IGNORECASE) is not None


@pytest.mark.unit
def test_smart_planner_has_central_premise_capable_for_cheap(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "Premissa Central" in content
    assert "modelo mais capaz" in content
    assert "modelo barato" in content


@pytest.mark.unit
def test_smart_planner_has_detail_calibration_self_question(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    assert "Calibração de Detalhe" in content
    assert "agente menos capaz" in content


@pytest.mark.unit
def test_smart_planner_delegates_initial_context_triage(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")

    assert "question-orchestration" in content
    assert "prompt inicial fraco" not in content


@pytest.mark.unit
def test_smart_planner_orchestrates_independent_executor_and_reviewer(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")

    assert "Pergunte ao humano se pode iniciar a execução" in content
    assert "**executor** e o do **revisor**" in content
    assert "instância nova do executor" in content
    assert "nova instância independente do revisor" in content
    assert "ela nunca corrige diretamente" in content


@pytest.mark.unit
def test_smart_planner_has_capability_and_manual_model_fallbacks(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")

    assert "Detecte a capacidade nativa de subagentes" in content
    assert "no OpenCode" in content
    assert "no Copilot CLI" in content
    assert "troca manual" in content
    assert "aguarde a confirmação humana antes do spawn" in content


@pytest.mark.unit
def test_smart_planner_replans_through_human_mediation(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")

    assert "## Protocolo de Replanejamento e Mediação" in content
    assert "Não invente decisão, requisito" in content
    assert "Inicie uma nova instância no estado correto" in content


@pytest.mark.unit
def test_smart_planner_requires_explicit_independent_review_approval(
    repo_root: Path,
) -> None:
    content = collapsed(
        smart_planner_file(repo_root).read_text(encoding="utf-8")
    )

    assert "## Condição Técnica de Término" in content
    assert "aprovar explicitamente" in content
    assert (
        "O planejamento aprovado sozinho nunca é condição de término"
        in content
    )


@pytest.mark.unit
def test_smart_planner_finalizes_commit_only_after_human_confirmation(
    repo_root: Path,
) -> None:
    content = collapsed(
        smart_planner_file(repo_root).read_text(encoding="utf-8")
    )

    assert "## Finalização Opcional do Commit Local" in content
    assert "resumo conciso da implementação" in content
    assert "os arquivos da unidade lógica aprovada" in content
    assert "mensagem Conventional Commit sugerida" in content
    assert "aguarde confirmação explícita" in content
    assert "Não prepare arquivos, adicione ao stage nem crie o commit" in content
    assert "prepare somente os arquivos da unidade lógica" in content
    assert "remova o arquivo de planejamento com `git rm`" in content
    assert "mesmo commit local" in content
    assert "`git diff --staged`" in content
    assert "informe o SHA" in content
    assert "Nunca execute `git push` sem nova confirmação explícita" in content


@pytest.mark.unit
def test_smart_planner_keeps_technical_conclusion_when_commit_is_deferred(
    repo_root: Path,
) -> None:
    content = smart_planner_file(repo_root).read_text(encoding="utf-8")
    normalized = re.sub(r"\s+", " ", content)

    assert "Se o humano recusar ou adiar" in content
    assert "conclusão técnica válida" in content
    assert "arquivo de planejamento e as mudanças sem commit" in normalized
    assert "mudanças sem commit" in content
    assert "Não reabra a revisão por essa decisão" in content


@pytest.mark.unit
def test_simple_agentic_workflow_documents_the_same_contract(
    repo_root: Path,
) -> None:
    workflow = collapsed(
        (repo_root / "docs" / "workflow-agentico-simples.md").read_text(
            encoding="utf-8"
        )
    )

    assert "## Máquina de Estados" in workflow
    assert "Seleção por Capacidade e Plataforma" in workflow
    assert "modelos separados" in workflow
    assert "instâncias independentes" in workflow
    assert "aprovação explícita do revisor" in workflow
    assert "## Finalização Opcional do Commit Local" in workflow
    assert "resumo conciso" in workflow
    assert "os arquivos da unidade lógica aprovada" in workflow
    assert "mensagem Conventional Commit sugerida" in workflow
    assert "aguarda confirmação explícita" in workflow
    assert "somente os arquivos da unidade lógica" in workflow
    assert "remove o arquivo de planejamento com `git rm`" in workflow
    assert "mesmo commit local" in workflow
    assert "`git diff --staged`" in workflow
    assert "Nunca executa `git push` sem nova confirmação explícita" in workflow
    assert "recusar ou adiar" in workflow
    assert "conclusão técnica permanece válida" in workflow
    assert "plano e as mudanças ficam sem commit" in workflow


@pytest.mark.unit
def test_agents_md_allows_local_commits_and_requires_push_confirmation(
    repo_root: Path,
) -> None:
    content = (repo_root / "AGENTS.md").read_text(encoding="utf-8")

    assert "`git push` exige confirmação explícita do humano" in content
    assert "NUNCA realize o commit independentemente." not in content
    assert "SÓ realize o commit quando o humano autorizar" not in content
    assert "Exceção — smart-planner" not in content
