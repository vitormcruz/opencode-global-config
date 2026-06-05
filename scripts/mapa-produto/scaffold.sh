#!/usr/bin/env bash
# scripts/mapa-produto/scaffold.sh
# Cria scaffold do /doc/README.md e/ou tabela de harness no AGENTS.md.
# Uso: scripts/mapa-produto/scaffold.sh [--doc <path>] [--harness <path>]
# Compatibilidade retroativa: chamada posicional sem flag = --doc.
# Idempotente: se seções já existem, não duplica.

set -euo pipefail

usage() {
  echo "Uso: $0 [--doc <path>] [--harness <path>]" >&2
  echo "  --doc <path>      Scaffold do /doc/README.md" >&2
  echo "  --harness <path>  Scaffold da tabela de harness no AGENTS.md" >&2
  echo "  (sem flags, caminho posicional = --doc)" >&2
  exit 1
}

DOC_DEST=""
HARNESS_DEST=""

# Backward compat: se primeiro arg não é flag, trata como --doc
if [[ $# -ge 1 && "$1" != --* ]]; then
  DOC_DEST="$1"
  shift
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --doc)
      shift
      DOC_DEST="${1:-}"
      [[ -z "$DOC_DEST" ]] && usage
      shift
      ;;
    --harness)
      shift
      HARNESS_DEST="${1:-}"
      [[ -z "$HARNESS_DEST" ]] && usage
      shift
      ;;
    *)
      usage
      ;;
  esac
done

if [[ -z "$DOC_DEST" && -z "$HARNESS_DEST" ]]; then
  usage
fi

scaffold_doc() {
  local dest="$1"
  mkdir -p "$(dirname "$dest")"
  touch "$dest"

  if grep -q "^## Definição de Escopo" "$dest" 2>/dev/null; then
    echo "Scaffold do /doc/README.md já existe em $dest. Nada a fazer."
    return 0
  fi

  cat >> "$dest" << 'DOCEOF'

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
DOCEOF

  echo "Scaffold do /doc/README.md criado em: $dest"
}

scaffold_harness() {
  local dest="$1"
  mkdir -p "$(dirname "$dest")"
  touch "$dest"

  if grep -q "^## Harness por Agente" "$dest" 2>/dev/null; then
    echo "Scaffold do harness já existe em $dest. Nada a fazer."
    return 0
  fi

  cat >> "$dest" << 'HARNESSEOF'

## Harness por Agente

| Agente | Comando de Execução | Descrição |
|--------|--------------------|-----------|
| eng-software | harness/eng-software.sh | Testes, análise estática |
| dba | harness/dba.sh | Validação de schema |
| sec | harness/sec.sh | OWASP checks, secrets |
| qa | harness/qa.sh | Cobertura, aceitação |
| front | harness/front.sh | Linting, a11y |
| rev | (sem harness) | SEM HARNESS A PEDIDO DO HUMANO |
| val-harness | (sem harness) | SEM HARNESS A PEDIDO DO HUMANO |
| curador-produto | (sem harness) | SEM HARNESS A PEDIDO DO HUMANO |

### Especificação dos Scripts de Harness

O `curador-produto-editor` usa as especificações abaixo para criar e
manter os scripts de harness. Cada script segue a interface padronizada:
sem argumentos, saída JSON (`status`, `findings`, `prompt`), exit code
0/1.

#### harness/eng-software.sh

**Objetivo:** Validar código — testes automatizados e análise estática.

**Ferramentas sugeridas:**
- Linter da linguagem (ESLint, ruff, shellcheck, etc.)
- Type checker (mypy, pyright, tsc, etc.)
- Test runner do projeto

**Critérios de falha (bloqueante):**
- Testes quebrados
- Erros de lint/type check

#### harness/dba.sh

**Objetivo:** Validar schema e migrations.

**Ferramentas sugeridas:**
- SQLFluff (lint SQL)
- Ferramenta de schema diff do projeto
- checkov/tflint (se houver infra de BD)

**Critérios de falha (bloqueante):**
- SQL inválido (error no linter)
- Divergência entre schema e modelo "as code"

#### harness/sec.sh

**Objetivo:** Validar segurança do código e dependências.

**Ferramentas sugeridas:**
- Semgrep (SAST)
- gitleaks/git-secrets (secrets scan)
- Snyk/npm audit/pip-audit (dependency check)

**Critérios de falha (bloqueante):**
- Findings high/critical no SAST
- Segredos detectados
- Vulnerabilidades críticas em dependências

#### harness/qa.sh

**Objetivo:** Validar cobertura de testes e qualidade.

**Ferramentas sugeridas:**
- Test runner com cobertura
- axe-core/pa11y (acessibilidade, se frontend)

**Critérios de falha (bloqueante):**
- Cobertura abaixo do baseline
- Violations critical de acessibilidade

#### harness/front.sh

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
HARNESSEOF

  echo "Scaffold do harness criado em: $dest"
}

# Executa scaffolds solicitados
if [[ -n "$DOC_DEST" ]]; then
  scaffold_doc "$DOC_DEST"
fi
if [[ -n "$HARNESS_DEST" ]]; then
  scaffold_harness "$HARNESS_DEST"
fi
