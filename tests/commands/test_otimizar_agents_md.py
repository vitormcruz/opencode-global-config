"""Guardas do command global de otimizacao de AGENTS.md."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

COMMAND_PATH = Path("harness-conf/commands/otimizar-agents-md.md")

# Artefatos de producao devem ser autocontidos: sem codigos de decisao do
# plano interno e sem citar o arquivo do plano.
_PLAN_LEAK_RE = re.compile(r"\bD\d{1,2}\b")
_PLAN_FILE_TOKEN = "otimizacao-custo-contexto"


@pytest.fixture
def command_content(repo_root: Path) -> str:
    """Conteudo integral do command otimizar-agents-md."""

    path = repo_root / COMMAND_PATH
    assert path.is_file(), f"{path} nao existe"
    return path.read_text(encoding="utf-8")


@pytest.mark.unit
def test_command_tem_frontmatter_description(command_content: str) -> None:
    """Frontmatter declara description (exibida no discovery do OpenCode)."""

    assert command_content.startswith("---\n"), "command sem frontmatter"
    frontmatter = command_content.split("---", 2)[1]
    assert re.search(r"^description:\s*\S", frontmatter, re.M), (
        "command sem description no frontmatter"
    )


@pytest.mark.unit
def test_command_define_os_dois_estagios(command_content: str) -> None:
    """O metodo embutido cobre descobribilidade e compressao."""

    assert "descobribilidade" in command_content
    assert "compressão" in command_content
    # Alavancas de compressão com garantia de comportamento.
    for lever in ("No-op test", "Imperativo positivo", "termo por conceito"):
        assert lever in command_content, f"alavanca ausente: {lever}"


@pytest.mark.unit
def test_command_exige_diff_e_aprovacao(command_content: str) -> None:
    """Nenhuma aplicacao sem diff apresentado e aprovacao explicita."""

    command_lower = command_content.lower()
    assert "nenhuma escrita no arquivo alvo antes de o humano aprovar" in (
        command_lower
    )
    assert "aprovação" in command_lower
    assert "diff unificado" in command_lower


@pytest.mark.unit
def test_command_relata_antes_e_depois(command_content: str) -> None:
    """O relatorio cobre tokens aproximados e cobertura das regras."""

    assert "Contagem aproximada de tokens antes e depois" in command_content
    assert "Tabela de cobertura das regras operacionais" in command_content


@pytest.mark.unit
def test_command_autocontido(command_content: str) -> None:
    """O command nao cita codigos de decisao nem o nome do plano interno."""

    assert not _PLAN_LEAK_RE.search(command_content), (
        "command cita codigo de decisao do plano interno"
    )
    assert _PLAN_FILE_TOKEN not in command_content, (
        "command cita o nome do plano interno"
    )
