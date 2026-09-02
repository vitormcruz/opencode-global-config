# Testes por Especialidade

Scripts por especialidade e o orquestrador `harness/testes`.
Interface JSON: `{ status, findings[] }`. Exit 0 = pass,
exit 1 = fail. Sem argumentos.

O orquestrador chama as quatro suítes e agrega o relatório.
Falha se qualquer suíte falhar.

Critérios, orçamento e ferramentas saem da entrevista de
curadoria. Fingerprint e cache ficam em `harness/target/`
e não são versionados.

**PROIBIDO:** bypassar, comentar, remover ou condicionar
qualquer verificação. Ferramenta ausente não justifica
remoção — reporte finding com instrução de instalação.

## backend

**Arquivo:** `harness/backend`

**Descrição:** Testes e análise do backend.

**O que deve conter:**
- Comandos de teste do projeto (unitários + integração)
- Relatório de cobertura de testes
- Análise estática, se o projeto tiver

**Ferramentas:** definidas na entrevista

**Critérios:** definidos na entrevista

**Orçamento:** tetos da entrevista; ver interface padronizada

## dados

**Arquivo:** `harness/dados`

**Descrição:** Validação de schema e modelo de dados.

**O que deve conter:**
- Validação de existência de documentos de especificação
- Validação de sintaxe do modelo (DBML ou equivalente)
- Conferência entre modelo e schema atual

**Ferramentas:** definidas na entrevista

**Critérios:** definidos na entrevista

**Orçamento:** tetos da entrevista; ver interface padronizada

## segurança

**Arquivo:** `harness/seguranca`

**Descrição:** Segurança — secrets, dependências, OWASP.

**O que deve conter:**
- Secrets scan no repositório
- Auditoria de dependências
- Verificação de vulnerabilidades conhecidas

**Ferramentas:** definidas na entrevista

**Critérios:** definidos na entrevista

**Orçamento:** tetos da entrevista; ver interface padronizada

## frontend

**Arquivo:** `harness/frontend`

**Descrição:** Testes, lint, build e acessibilidade do
frontend.

**O que deve conter:**
- Testes frontend
- Lint e build
- Verificação de acessibilidade
- Cobertura da suíte de UI, se houver
- `pa11y`, `axe-core` ou ambos: a entrevista decide

**Ferramentas:** definidas na entrevista

**Critérios:** definidos na entrevista

**Orçamento:** tetos da entrevista; ver interface padronizada

## Orquestrador

**Arquivo:** `harness/testes`

Chama as quatro suítes (`harness/backend`, `harness/dados`,
`harness/seguranca`, `harness/frontend`) e agrega o
relatório no fim. `status` é `fail` se qualquer suíte
falhar. Não reabre entrevista nem inventa check.
