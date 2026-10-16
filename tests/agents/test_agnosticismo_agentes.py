"""Travas para manter agentes e referências independentes de roteamento."""

from __future__ import annotations

import re
from pathlib import Path

import pytest


AGENT_NAMES = (
    "dba",
    "eng-software",
    "front",
    "qa",
    "sec",
    "rev",
    "curador-produto",
    "analista",
)

FORBIDDEN_CONCEPTS = re.compile(
    r"devflow|orquestr\w*|\bworkflow\w*|mediaç\w*|mediad\w*|"
    r"(?-i:\bFluxos?\b)|\bfases?\b|\betapas?\b",
    re.IGNORECASE,
)
FORBIDDEN_BRANCHES = (
    re.compile(r"\bacionado diretamente\b", re.IGNORECASE),
    re.compile(r"\b(?:acionado|chamado)\b[^.\n]{0,60}\bpelo humano\b", re.IGNORECASE),
    re.compile(r"\bchamado por\b", re.IGNORECASE),
    re.compile(r"\binteraja normalmente\b", re.IGNORECASE),
    re.compile(r"\bpergunt\w* o que precis\w*\b", re.IGNORECASE),
    re.compile(r"\bquando chamado\b", re.IGNORECASE),
    re.compile(r"\bquando acionado\b", re.IGNORECASE),
    re.compile(r"quando chamado por outro agente", re.IGNORECASE),
    re.compile(r"quando chamado diretamente pelo humano", re.IGNORECASE),
    re.compile(r"acionado por outro agente", re.IGNORECASE),
    re.compile(r"outros agentes", re.IGNORECASE),
)
FORBIDDEN_PROMPT_PATHS = (
    "docs/readme.md",
    "docs/testes-por-especialidade.md",
    "docs/adr/",
    "plan/",
)
INTERACTION_AGENTS = AGENT_NAMES[:-1]

# Exceções de termos que não descrevem o Fluxo:
# - Etapas numeradas de analista/eng-software são procedimentos internos.
# - As ocorrências do AGENTS.base.md orientam contexto e compactação.
# - O nome da skill de versionamento é uma referência técnica legítima.
# - "Fluxos de autenticação" descreve domínio do template de produto.
# - Estes três rótulos nomeiam procedimentos internos dos agentes, não o
#   Fluxo de roteamento do Framework.
LEGITIMATE_CONCEPT_EXCEPTIONS = {
    "analista.md": (
        r"\bEtapa [12]\b",
        r"## Fluxo de interação",
    ),
    "curador-produto.md": (r"\*\*Fluxo\*\*",),
    "eng-software.md": (r"\bEtapa [123]\b",),
    "AGENTS.base.md": (
        r"\buma etapa ou decisão\b",
        r"\bResumo de etapas\b",
        r"\bEtapa concluída\b",
        r"\bfronteira de etapa seguinte\b",
    ),
    "doc-readme-template.md": (
        r"\bFluxos de autenticação e autorização por perfil\b",
    ),
    "rev.md": (r"\*\*Fluxo de achados\*\*",),
}


def _agent_path(repo_root: Path, name: str) -> Path:
    return repo_root / "harness-conf" / "agents" / f"{name}.md"


def _guard_text(path: Path, content: str) -> str:
    """Remove apenas termos explicitamente legítimos do scan."""

    if path.name == "eng-software.md":
        content = content.replace("git-workflow-and-versioning", "")
    if path.name == "AGENTS.base.md":
        content = content.replace("git-workflow-and-versioning", "")
    content = content.replace("## Evidências de Testes — <fase>", "")

    for pattern in LEGITIMATE_CONCEPT_EXCEPTIONS.get(path.name, ()):
        content = re.sub(pattern, "", content, flags=re.IGNORECASE)

    return content


def _interaction_section(content: str) -> str:
    """Extrai a seção Interação até o próximo heading de mesmo nível."""

    lines = content.replace("\r", "").splitlines()
    start = lines.index("## Interação")
    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if lines[index].startswith("## ")
        ),
        len(lines),
    )
    return "\n".join(lines[start:end])


def _agnosticism_paths(repo_root: Path) -> list[Path]:
    """Retorna prompts e documentos lidos pelos agentes operacionais."""

    agents_dir = repo_root / "harness-conf" / "agents"
    paths = [_agent_path(repo_root, name) for name in AGENT_NAMES]
    paths += sorted((agents_dir / "references").glob("*.md"))
    paths += sorted((agents_dir / "default-artifacts").glob("*"))
    paths += [
        repo_root / "harness-conf" / "AGENTS.base.md",
        repo_root / "docs" / "testes-por-especialidade.md",
    ]
    return [path for path in paths if path.is_file()]


@pytest.mark.unit
def test_agentes_operacionais_sao_agnosticos_e_devolvem_ao_caller(
    repo_root: Path,
) -> None:
    """Prompts não conhecem roteamento e retornam a quem os acionou."""

    for name in AGENT_NAMES:
        path = _agent_path(repo_root, name)
        content = path.read_text(encoding="utf-8")
        normalized = content.lower()

        assert re.search(
            r"(?:d[úu]vida|pergunta|falha|decis[ãa]o).{0,100}"
            r"quem o acionou",
            content,
            re.IGNORECASE | re.DOTALL,
        ), f"{path}: retorno a quem o acionou não está ligado a uma decisão"
        assert all(phrase.search(content) is None for phrase in FORBIDDEN_BRANCHES), (
            f"{path}: contrato especializado de acionamento encontrado"
        )
        assert all(token not in normalized for token in FORBIDDEN_PROMPT_PATHS), (
            f"{path}: caminho físico de especificação encontrado"
        )
        assert FORBIDDEN_CONCEPTS.search(_guard_text(path, content)) is None, (
            f"{path}: termo de roteamento encontrado"
        )

    for name in INTERACTION_AGENTS:
        content = _agent_path(repo_root, name).read_text(encoding="utf-8")
        interaction = _interaction_section(content)
        assert "Dúvida, falha e decisão vão a quem o acionou." in interaction, name
        assert "Não consulte o humano diretamente." not in interaction, name


@pytest.mark.unit
def test_referencias_skills_e_templates_nao_conhecem_roteamento(
    repo_root: Path,
) -> None:
    """Artefatos consumidos pelos agentes não vazam o contrato de roteamento."""

    for path in _agnosticism_paths(repo_root):
        content = path.read_text(encoding="utf-8")
        assert FORBIDDEN_CONCEPTS.search(_guard_text(path, content)) is None, (
            f"{path}: termo de roteamento encontrado"
        )

        if path == repo_root / "harness-conf" / "AGENTS.base.md":
            normalized = content.lower()
            assert all(token not in normalized for token in FORBIDDEN_PROMPT_PATHS), (
                f"{path}: caminho físico de especificação encontrado"
            )
