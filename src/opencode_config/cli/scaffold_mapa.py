"""Geração dos scaffolds de documentação e harness do mapa de produto."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
import sys
from textwrap import dedent
from typing import TextIO


DOC_TEMPLATE = dedent(
    """
    ## Definição de Escopo

    O analista deve elicitar:
    - Requisitos funcionais e não funcionais
    - Critérios de aceitação por exemplos
    - Organizados por histórias de usuário
    - Critérios devem referenciar requisitos funcionais
    - Nenhum requisito pode ficar sem critério
    Skill recomendada: (opcional — humano define)

    ## Elementos de Especificação

    | Elemento | Formato/Ferramenta | Agente Responsável | Destino |
    |----------|-------------------|-------------------|---------|
    | Critérios de Aceite + Requisitos | Concordion | eng-software | docs/specs/ |
    | Regras de Produto | Tabela | eng-software | nenhum |
    | Modelo de Dados | DBML | dba | docs/modelo.dbml |
    | Threat Model | Markdown | sec | docs/threat-model.md |
    | Plano de Testes | Markdown | qa | nenhum |
    | Identidade Visual | Protótipo HTML/SVG | front | plan/ui/ |
    | ADR (Arquitetura) | Markdown | eng-software | docs/adr/ |

    ### Regras de Documentação

    #### Regras Gerais

    - Documentação complementa o código, não o repete
    - Doc derivável do código não se armazena — gere sob demanda
    - Doc desatualizada é pior que ausência de doc
    - Preferir formatos versionáveis (Markdown, Mermaid, DBML)
    - Seguir convenção de nomenclatura do projeto

    #### Critérios de Aceite + Requisitos

    Os critérios de aceite devem estar organizados por
    Funcionalidade levando-se em conta a coesão. Cada
    funcionalidade deve ter um arquivo Concordion
    separado. Os requisitos associados aos critérios
    de aceitação devem estar no mesmo arquivo, e os
    critérios devem referenciar os requisitos que
    estão sendo atendidos.

    #### Regras de Produto

    Manter como tabela no arquivo de planejamento.
    Inicializar com `(a definir)` campos não
    identificados. Cada agente que encontrar campo
    ausente pergunta ao humano e registra antes de
    prosseguir. Formato: Campo | Tam. máx |
    Tipo/Formato | Máscara | Limite | Observação.

    #### Modelo de Dados

    Versionar junto com o código em `docs/modelo.dbml`.
    Regenerar schema diff a cada alteração de modelo.
    Divergências entre modelo e schema são bloqueantes.

    #### Threat Model

    Atualizar a cada ciclo de desenvolvimento.
    Documentar ativos, ameaças, vulnerabilidades e
    controles. Findings high/critical são bloqueantes.

    #### Plano de Testes

    Registrar no arquivo de planejamento: tipos de
    teste (unidade, integração, aceitação), escopo,
    baseline de cobertura. Relatório final deve
    incluir total executados, passaram, falharam,
    skipped e delta de cobertura.

    #### Identidade Visual

    Protótipos em `plan/ui/` aprovados pelo humano
    viram contrato visual. Desvios não autorizados da
    identidade visual aprovada são bloqueantes. Toda
    alteração de identidade requer re-aprovação
    explícita do humano.

    #### ADR (Arquitetura)

    Seguir template ADR: Título, Status, Contexto,
    Decisão, Consequências. Versionar em `docs/adr/`.
    Cada decisão arquitetural significativa gera um
    ADR. ADRs existentes não são alterados — gerar
    novo ADR que referencia o anterior.

    ## Estratégias de Indexação de Código

    - (preencher com ferramentas selecionadas)
    """
)

HARNESS_TEMPLATE = dedent(
    """
    ## Harness por Agente

    | Agente | Comando de Execução | Descrição |
    |--------|--------------------|-----------|
    | eng-software | harness/eng-software | Testes, análise estática |
    | dba | harness/dba | Validação de schema |
    | sec | harness/sec | OWASP checks, secrets |
    | qa | harness/qa | Cobertura, aceitação |
    | front | harness/front | Linting, a11y |
    | rev | (sem harness) | SEM HARNESS A PEDIDO DO HUMANO |
    | val-harness | (sem harness) | SEM HARNESS A PEDIDO DO HUMANO |
    | curador-produto | (sem harness) | SEM HARNESS A PEDIDO DO HUMANO |

    ### Especificação dos Scripts de Harness

    O `curador-produto-editor` usa as especificações abaixo para criar e
    manter os scripts de harness. Cada script segue a interface padronizada:
    sem argumentos, saída JSON (`status`, `findings`, `prompt`), exit code
    0/1.

    #### harness/eng-software

    **Objetivo:** Validar código — testes automatizados e análise estática.

    **Ferramentas sugeridas:**
    - Linter da linguagem (ESLint, ruff, shellcheck, etc.)
    - Type checker (mypy, pyright, tsc, etc.)
    - Test runner do projeto

    **Critérios de falha (bloqueante):**
    - Testes quebrados
    - Erros de lint/type check

    #### harness/dba

    **Objetivo:** Validar schema e migrations.

    **Ferramentas sugeridas:**
    - SQLFluff (lint SQL)
    - Ferramenta de schema diff do projeto
    - checkov/tflint (se houver infra de BD)

    **Critérios de falha (bloqueante):**
    - SQL inválido (error no linter)
    - Divergência entre schema e modelo "as code"

    #### harness/sec

    **Objetivo:** Validar segurança do código e dependências.

    **Ferramentas sugeridas:**
    - Semgrep (SAST)
    - gitleaks/git-secrets (secrets scan)
    - Snyk/npm audit/pip-audit (dependency check)

    **Critérios de falha (bloqueante):**
    - Findings high/critical no SAST
    - Segredos detectados
    - Vulnerabilidades críticas em dependências

    #### harness/qa

    **Objetivo:** Validar cobertura de testes e qualidade.

    **Ferramentas sugeridas:**
    - Test runner com cobertura
    - axe-core/pa11y (acessibilidade, se frontend)

    **Critérios de falha (bloqueante):**
    - Cobertura abaixo do baseline
    - Violations critical de acessibilidade

    #### harness/front

    **Objetivo:** Validar código frontend — lint, acessibilidade e aderência
    visual.

    **Ferramentas sugeridas:**
    - stylelint, htmlhint
    - axe-core, pa11y
    - Playwright/Cypress snapshot (se aplicável)

    **Critérios de falha (bloqueante):**
    - Erros de lint CSS/HTML
    - Violations critical de acessibilidade
    - Desvios não autorizados da identidade visual
    """
)


def _append_scaffold(
    destination: Path,
    *,
    marker: str,
    template: str,
    created_message: str,
    existing_message: str,
) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.touch(exist_ok=True)
    content = destination.read_text(encoding="utf-8")
    if marker in content.splitlines():
        return existing_message.format(destination=destination)
    destination.write_text(content + template, encoding="utf-8")
    return created_message.format(destination=destination)


def scaffold_doc(destination: Path) -> str:
    """Cria o scaffold de documentação sem duplicar a seção principal."""

    return _append_scaffold(
        destination,
        marker="## Definição de Escopo",
        template=DOC_TEMPLATE,
        created_message="Scaffold do /doc/README.md criado em: {destination}",
        existing_message=(
            "Scaffold do /doc/README.md já existe em {destination}. Nada a fazer."
        ),
    )


def scaffold_harness(destination: Path) -> str:
    """Cria o scaffold de harness sem duplicar a tabela."""

    return _append_scaffold(
        destination,
        marker="## Harness por Agente",
        template=HARNESS_TEMPLATE,
        created_message="Scaffold do harness criado em: {destination}",
        existing_message=(
            "Scaffold do harness já existe em {destination}. Nada a fazer."
        ),
    )


def _usage() -> str:
    return (
        "Uso: opencode-scaffold-mapa [--doc <path>] [--harness <path>]\n"
        "  --doc <path>      Scaffold do /doc/README.md\n"
        "  --harness <path>  Scaffold da tabela de harness no AGENTS.md\n"
        "  (sem flags, caminho posicional = --doc)\n"
    )


def run(
    arguments: Sequence[str],
    *,
    output: TextIO,
    error: TextIO,
) -> int:
    doc_destination: str | None = None
    harness_destination: str | None = None
    index = 0
    if arguments and not arguments[0].startswith("--"):
        doc_destination = arguments[0]
        index = 1

    while index < len(arguments):
        argument = arguments[index]
        if argument in {"--doc", "--harness"}:
            index += 1
            if index >= len(arguments) or arguments[index].startswith("--"):
                error.write(_usage())
                return 1
            if argument == "--doc":
                doc_destination = arguments[index]
            else:
                harness_destination = arguments[index]
        else:
            error.write(_usage())
            return 1
        index += 1

    if doc_destination is None and harness_destination is None:
        error.write(_usage())
        return 1

    if doc_destination is not None:
        output.write(scaffold_doc(Path(doc_destination)) + "\n")
    if harness_destination is not None:
        output.write(scaffold_harness(Path(harness_destination)) + "\n")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Executa o entrypoint `opencode-scaffold-mapa`."""

    return run(
        list(sys.argv[1:] if argv is None else argv),
        output=sys.stdout,
        error=sys.stderr,
    )


if __name__ == "__main__":
    raise SystemExit(main())
