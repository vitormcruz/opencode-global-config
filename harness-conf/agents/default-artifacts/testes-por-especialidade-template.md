<!-- TEMPLATE: especificação própria das suítes de validação do
     projeto-alvo. Fica na mesma pasta da Especificação do Produto e
     é referenciada por ela e pelo AGENTS.md. -->
# Testes por Especialidade

| Especialidade | Script |
|---------------|--------|
| backend | `testes-produto/backend` |
| dados | `testes-produto/dados` |
| segurança | `testes-produto/seguranca` |
| frontend | `testes-produto/frontend` |

## Contrato das Suítes

Scripts por especialidade e o agregador `testes-produto`.
Interface JSON: `{ status, findings[] }`. Exit 0 = pass,
exit 1 = fail. Sem argumentos.

O agregador chama as quatro suítes e consolida o relatório.
Falha se qualquer suíte falhar. 

Critérios, orçamento e ferramentas saem da entrevista de curadoria.
Fingerprint e cache ficam em `testes-produto/target/` e não são
versionados.

**PROIBIDO:** bypassar, comentar, remover ou condicionar qualquer
verificação. Ferramenta ausente não justifica remoção. Reporte o
finding com instrução de instalação.

## Dois níveis de teste

1. **Testes da aplicação:** validam o produto em desenvolvimento.
   Rodam via suítes e agregador `testes-produto` durante a validação
   do produto.
2. **Testes dos scripts de teste:** os scripts de suíte e o agregador
   são código e têm testes próprios em `testes-produto/tests/`.
   Eles rodam somente quando esses scripts mudam, nunca no ciclo
   normal de desenvolvimento.

## backend

**Arquivo:** `testes-produto/backend`

**Descrição:** Testes e análise do backend.

**O que deve conter:**
- Comandos de teste do projeto (unitários + integração)
- Relatório de cobertura de testes
- Análise estática, se o projeto tiver
- Specs executáveis da especialidade, quando aplicável

**Ferramentas:** definidas na entrevista

**Critérios:** definidos na entrevista

**Orçamento:** tetos da entrevista; ver interface padronizada

## dados

**Arquivo:** `testes-produto/dados`

**Descrição:** Validação de schema e modelo de dados.

**O que deve conter:**
- Validação de existência de documentos de especificação
- Validação de sintaxe do modelo (DBML ou equivalente)
- Conferência entre modelo e schema atual
- Specs executáveis da especialidade, quando aplicável

**Ferramentas:** definidas na entrevista

**Critérios:** definidos na entrevista

**Orçamento:** tetos da entrevista; ver interface padronizada

## segurança

**Arquivo:** `testes-produto/seguranca`

**Descrição:** Segurança, secrets, dependências e OWASP.

**O que deve conter:**
- Secrets scan no repositório
- Auditoria de dependências
- Verificação de vulnerabilidades conhecidas
- Specs executáveis da especialidade, quando aplicável

**Ferramentas:** definidas na entrevista

**Critérios:** definidos na entrevista

**Orçamento:** tetos da entrevista; ver interface padronizada

## frontend

**Arquivo:** `testes-produto/frontend`

**Descrição:** Testes, lint, build e acessibilidade do frontend.

**O que deve conter:**
- Testes frontend
- Lint e build
- Verificação de acessibilidade
- Cobertura da suíte de UI, se houver
- `pa11y`, `axe-core` ou ambos: a entrevista decide
- Specs executáveis da especialidade, quando aplicável

**Ferramentas:** definidas na entrevista

**Critérios:** definidos na entrevista

**Orçamento:** tetos da entrevista; ver interface padronizada

## Agregador

**Arquivo:** `testes-produto`

Chama as quatro suítes (`testes-produto/backend`,
`testes-produto/dados`, `testes-produto/seguranca`,
`testes-produto/frontend`) e consolida o relatório. `status` é
`fail` se qualquer suíte falhar. Não reabre entrevista nem inventa
check.
