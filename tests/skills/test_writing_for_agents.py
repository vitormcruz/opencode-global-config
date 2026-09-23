"""Guardas da skill writing-for-agents importada do upstream mattpocock/skills."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from opencode_config.cli.skills_sync import list_updatable

SKILL_DIR = Path("harness-conf/skills/writing-for-agents")

# Termos que denunciam vazamento do plano interno dentro de artefato de
# producao: artefatos devem ser autocontidos.
_PLAN_LEAK_RE = re.compile(r"\bD\d{1,2}\b")
_PLAN_FILE_TOKEN = "otimizacao-custo-contexto"


def _skill_text(repo_root: Path, name: str) -> str:
    return (repo_root / SKILL_DIR / name).read_text(encoding="utf-8")


def _assert_self_contained(content: str) -> None:
    assert not _PLAN_LEAK_RE.search(content), (
        "artefato cita codigo de decisao do plano interno"
    )
    assert _PLAN_FILE_TOKEN not in content, (
        "artefato cita o nome do plano interno"
    )


@pytest.mark.unit
def test_skill_importada_tem_artefatos(repo_root: Path) -> None:
    """A pasta da skill tem SKILL.md, referencia e metadados de upstream."""

    for name in ("SKILL.md", "SKILL-MECHANICS.md", "UPSTREAM.md"):
        path = repo_root / SKILL_DIR / name
        assert path.is_file(), f"{path} nao existe"


@pytest.mark.unit
def test_skill_md_frontmatter_valido(repo_root: Path) -> None:
    """O frontmatter declara name e description."""

    content = _skill_text(repo_root, "SKILL.md")
    assert content.startswith("---\n"), "SKILL.md sem frontmatter"
    frontmatter = content.split("---", 2)[1]
    assert re.search(r"^name:\s*writing-for-agents\s*$", frontmatter, re.M)
    assert re.search(r"^description:\s*>?$", frontmatter, re.M) or (
        "description:" in frontmatter
    )


@pytest.mark.unit
def test_description_em_pt_br_com_triggers(repo_root: Path) -> None:
    """A description foi convertida para PT-BR e enriquecida com triggers."""

    frontmatter = _skill_text(repo_root, "SKILL.md").split("---", 2)[1]
    assert "Use ao" in frontmatter, "description sem padrao 'Use ao' de ativacao"
    assert "Triggers:" in frontmatter, "description sem triggers"
    assert "context pointer" in frontmatter or "AGENTS.md" in frontmatter


@pytest.mark.unit
def test_upstream_metadados_completos(repo_root: Path) -> None:
    """UPSTREAM.md registra origem, commit, data, sync, licenca e decisoes."""

    upstream = _skill_text(repo_root, "UPSTREAM.md")
    for field in (
        "repositorio: https://github.com/mattpocock/skills",
        "commit: ",
        "data_commit: ",
        "sincronizado_em: ",
        "description_lang: pt-br",
        "description_note: ",
        "## Como atualizar",
        "## Licenca",
    ):
        assert field in upstream, f"UPSTREAM.md sem {field!r}"
    assert "MIT" in upstream, "licenca MIT nao registrada"
    _assert_self_contained(upstream)


@pytest.mark.unit
def test_skill_registrada_no_opencode_skills(repo_root: Path) -> None:
    """A skill aparece no inventario de skills atualizaveis do helper."""

    assert "writing-for-agents" in list_updatable(repo_root)


@pytest.mark.unit
def test_skill_autocontida(repo_root: Path) -> None:
    """SKILL.md nao cita codigos de decisao nem o nome do plano interno."""

    _assert_self_contained(_skill_text(repo_root, "SKILL.md"))
