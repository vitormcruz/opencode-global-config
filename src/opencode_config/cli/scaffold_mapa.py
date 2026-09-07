"""Geração dos scaffolds de documentação e testes-produto do mapa."""

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

    ## Testes por Especialidade

    Scripts por especialidade e o orquestrador `testes-produto`.
    Interface JSON: `{ status, findings[] }`. Exit 0 = pass,
    exit 1 = fail. Sem argumentos. O orquestrador chama as
    quatro suítes e agrega o relatório; falha se qualquer
    suíte falhar. Critérios, orçamento e ferramentas saem da
    entrevista de curadoria. Fingerprint e cache ficam em
    `testes-produto/target/` e não são versionados.

    **PROIBIDO:** bypassar, comentar, remover ou condicionar
    qualquer verificação. Ferramenta ausente não justifica
    remoção — reporte finding com instrução de instalação.

    ### Dois níveis de teste

    1. **Testes da aplicação** — validam o produto em
       desenvolvimento. Rodam via suítes/orquestrador
       `testes-produto` na fase Testes do workflow, sempre
       que se desenvolve funcionalidade.
    2. **Testes dos scripts de teste** — os scripts de suíte
       e o orquestrador são código e têm testes próprios.
       Esta seção é a especificação executável deles: os
       testes dos scripts cobrem exatamente o que ela define.
       Rodam SOMENTE quando os scripts mudam, nunca no ciclo
       normal de desenvolvimento.

    O `AGENTS.md` do projeto mantém apenas a tabela índice das
    suítes com link para esta seção
    (`docs/README.md#testes-por-especialidade`).

    ### Suítes

    - backend: `testes-produto/backend`
    - dados: `testes-produto/dados`
    - segurança: `testes-produto/seguranca`
    - frontend: `testes-produto/frontend`
    - Orquestrador: `testes-produto`
    """
)

TESTES_PRODUTO_TEMPLATE = dedent(
    """
    ## Testes por Especialidade

    | Especialidade | Script |
    |---------------|--------|
    | backend | testes-produto/backend |
    | dados | testes-produto/dados |
    | segurança | testes-produto/seguranca |
    | frontend | testes-produto/frontend |

    Orquestrador: testes-produto

    Spec: [docs/README.md#testes-por-especialidade](docs/README.md#testes-por-especialidade)
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


def scaffold_testes_produto(destination: Path) -> str:
    """Cria o scaffold de testes-produto sem duplicar a tabela."""

    return _append_scaffold(
        destination,
        marker="## Testes por Especialidade",
        template=TESTES_PRODUTO_TEMPLATE,
        created_message="Scaffold de testes-produto criado em: {destination}",
        existing_message=(
            "Scaffold de testes-produto já existe em {destination}. Nada a fazer."
        ),
    )


def _usage() -> str:
    return (
        "Uso: opencode-scaffold-mapa [--doc <path>] [--testes-produto <path>]\n"
        "  --doc <path>             Scaffold do /doc/README.md\n"
        "  --testes-produto <path>  Scaffold da tabela de testes no AGENTS.md\n"
        "  (sem flags, caminho posicional = --doc)\n"
    )


def run(
    arguments: Sequence[str],
    *,
    output: TextIO,
    error: TextIO,
) -> int:
    doc_destination: str | None = None
    testes_produto_destination: str | None = None
    index = 0
    if arguments and not arguments[0].startswith("--"):
        doc_destination = arguments[0]
        index = 1

    while index < len(arguments):
        argument = arguments[index]
        if argument in {"--doc", "--testes-produto"}:
            index += 1
            if index >= len(arguments) or arguments[index].startswith("--"):
                error.write(_usage())
                return 1
            if argument == "--doc":
                doc_destination = arguments[index]
            else:
                testes_produto_destination = arguments[index]
        else:
            error.write(_usage())
            return 1
        index += 1

    if doc_destination is None and testes_produto_destination is None:
        error.write(_usage())
        return 1

    if doc_destination is not None:
        output.write(scaffold_doc(Path(doc_destination)) + "\n")
    if testes_produto_destination is not None:
        output.write(
            scaffold_testes_produto(Path(testes_produto_destination)) + "\n"
        )
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
