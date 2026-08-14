import re
from pathlib import Path

import pytest


@pytest.fixture
def skill_content(repo_root: Path) -> str:
    return (
        repo_root / "skills/question-orchestration/SKILL.md"
    ).read_text(encoding="utf-8")


@pytest.mark.unit
def test_question_orchestration_skill_exists(repo_root: Path) -> None:
    assert (repo_root / "skills/question-orchestration/SKILL.md").is_file()


@pytest.mark.unit
def test_question_orchestration_frontmatter_has_activation_triggers(
    skill_content: str,
) -> None:
    frontmatter = skill_content.split("---", 2)[1].lower()

    assert "name: question-orchestration" in frontmatter
    assert "description:" in frontmatter
    assert "mediação" in frontmatter
    assert "perguntas" in frontmatter
    assert "analista" in frontmatter
    assert "curador-produto-editor" in frontmatter


@pytest.mark.unit
def test_question_orchestration_contains_shared_conversational_protocol(
    skill_content: str,
) -> None:
    normalized = re.sub(r"\s+", " ", skill_content)

    assert "Modo direto" in normalized
    assert "Modo mediado" in normalized
    assert "prompt inicial fraco" in normalized
    assert "carga cognitiva" in normalized
    assert "não seja cansativa" in normalized
    assert "no máximo 4 perguntas por rodada" in normalized
    assert "uma pergunta por vez" in normalized
    assert "recomendação com justificativa" in normalized
    assert "contra-proposta" in normalized
    assert "Posso registrar assim?" in normalized
    assert "NUNCA pule um ramo independente" in normalized
    assert "Não repita decisão" in normalized
    assert "grill-me" not in normalized
    assert "prompt-improver" in normalized
    assert "mediador organiza e apresenta" in normalized
    assert "Checklist estrutural" not in normalized
    assert "Máximo 2 rodadas" not in normalized
    assert "mediador organiza e qualifica" not in normalized
    assert "Preserve a continuidade da mediação" not in normalized
    assert "melhorar o input do humano antes de rotear ao agente" not in normalized


@pytest.mark.unit
def test_question_orchestration_stays_outside_planning_and_git_policy(
    skill_content: str,
) -> None:
    normalized = re.sub(r"\s+", " ", skill_content)

    assert "Não define a estrutura do plano" in normalized
    assert "política de Git" in normalized
