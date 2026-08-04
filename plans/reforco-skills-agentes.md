# Plano: Reforço de Skills nos Agentes

## Overview

Adicionar seção `## Skills` estruturada (obrigatórias,
condicionais, transversais) a 10 agentes e converter
menções passivas ("consulte a skill X") em gatilhos
imperativos ("**ANTES** de fazer Y, carregue a skill X").
Objetivo: aumentar a taxa de ativação consistente de skills
durante execução dos agentes.

## Decisões de Arquitetura

| Decisão | Justificativa |
|---------|--------------|
| Seção entre Contrato Operacional e Capacidades | LLM lê skills antes de instruções de capacidade |
| Formato tabular com 3 subseções | Estrutura escaneável, classificação clara |
| devflow e val-harness sem seção Skills | Orquestração/validação pura, sem capacidade técnica |
| revisor-historia sem seção Skills | Subagent de revisão textual, escopo ultra-restrito |
| aws-analista com seção adaptada | Sem estrutura padrão, apenas transversais |
| curador/editor sem spec-driven-development | Validam/estruturam docs, não escrevem specs |

## Task List

### Fase 1: Agentes de Execução

---

#### Task 1: eng-software — seção Skills + 5 gatilhos

**Description:** Inserir seção `## Skills` entre L80 e L83
e converter 5 menções passivas em gatilhos imperativos.
Adicionar 5 skills novas: planning-and-task-breakdown,
api-and-interface-design, debugging-and-error-recovery,
performance-optimization, code-explorer-priority.

**Acceptance criteria:**
- [ ] Seção `## Skills` presente com 5 obrig + 5 cond + 1 trans
- [ ] 5 menções passivas convertidas para gatilhos imperativos
- [ ] Nenhuma linha excede 120 colunas
- [ ] Frontmatter YAML inalterado
- [ ] Conteúdo existente preservado (apenas adições e substituições)

**Verification:**
- [ ] `grep -n "consulte a skill\|consulte \`" agents/eng-software.md`
  retorna zero resultados
- [ ] `awk 'length > 120' agents/eng-software.md` retorna zero linhas
- [ ] `head -16 agents/eng-software.md` mostra frontmatter intacto

**Dependencies:** Nenhuma
**Files likely touched:** `agents/eng-software.md`
**Estimated scope:** S (1 arquivo, ~12 edições)

---

#### Task 2: front — seção Skills + 1 gatilho

**Description:** Inserir seção `## Skills` entre L78 e L81
e converter 1 menção passiva em gatilho imperativo.
Adicionar 4 skills novas: accessibility-audit,
code-simplification, performance-optimization,
code-explorer-priority.

**Acceptance criteria:**
- [ ] Seção `## Skills` presente com 3 obrig + 2 cond + 1 trans
- [ ] 1 menção passiva convertida para gatilho imperativo
- [ ] Nenhuma linha excede 120 colunas
- [ ] Frontmatter YAML inalterado

**Verification:**
- [ ] `grep -n "consulte a skill\|consulte \`" agents/front.md`
  retorna zero resultados
- [ ] `awk 'length > 120' agents/front.md` retorna zero linhas

**Dependencies:** Nenhuma
**Files likely touched:** `agents/front.md`
**Estimated scope:** S (1 arquivo, ~3 edições)

---

#### Task 3: dba — seção Skills + 1 gatilho

**Description:** Inserir seção `## Skills` entre L60 e L63
e converter 1 menção passiva em gatilho imperativo.
Adicionar 2 skills novas: planning-and-task-breakdown,
debugging-and-error-recovery.

**Acceptance criteria:**
- [ ] Seção `## Skills` presente com 2 obrig + 2 cond
- [ ] 1 menção passiva convertida para gatilho imperativo
- [ ] Nenhuma linha excede 120 colunas
- [ ] Frontmatter YAML inalterado

**Verification:**
- [ ] `grep -n "ref: skill" agents/dba.md` retorna zero resultados
- [ ] `awk 'length > 120' agents/dba.md` retorna zero linhas

**Dependencies:** Nenhuma
**Files likely touched:** `agents/dba.md`
**Estimated scope:** S (1 arquivo, ~3 edições)

---

#### Task 4: sec — seção Skills + 3 gatilhos

**Description:** Inserir seção `## Skills` entre L75 e L78
e converter 3 menções passivas em gatilhos imperativos.
Sem skills novas — apenas reorganização.

**Acceptance criteria:**
- [ ] Seção `## Skills` presente com 2 obrig + 2 cond
- [ ] 3 menções passivas convertidas para gatilhos imperativos
- [ ] Nenhuma linha excede 120 colunas
- [ ] Frontmatter YAML inalterado

**Verification:**
- [ ] `grep -n "consulte a skill\|consulte \`" agents/sec.md`
  retorna zero resultados
- [ ] `awk 'length > 120' agents/sec.md` retorna zero linhas

**Dependencies:** Nenhuma
**Files likely touched:** `agents/sec.md`
**Estimated scope:** S (1 arquivo, ~5 edições)

---

#### Task 5: qa — seção Skills + 3 gatilhos

**Description:** Inserir seção `## Skills` entre L70 e L73
e converter 3 menções passivas em gatilhos imperativos.
Adicionar 2 skills novas: accessibility-audit,
performance-optimization.

**Acceptance criteria:**
- [ ] Seção `## Skills` presente com 4 obrig + 4 cond
- [ ] 3 menções passivas convertidas para gatilhos imperativos
- [ ] Nenhuma linha excede 120 colunas
- [ ] Frontmatter YAML inalterado

**Verification:**
- [ ] `grep -n "consulte a skill\|consulte \`" agents/qa.md`
  retorna zero resultados
- [ ] `awk 'length > 120' agents/qa.md` retorna zero linhas

**Dependencies:** Nenhuma
**Files likely touched:** `agents/qa.md`
**Estimated scope:** S (1 arquivo, ~5 edições)

---

### Checkpoint: Fase 1
- [ ] Todos os 5 agentes de execução têm seção `## Skills`
- [ ] Zero menções passivas ("consulte a skill") nos 5 agentes
- [ ] Zero linhas > 120 colunas nos 5 agentes
- [ ] Todos os frontmatters YAML intactos
- [ ] Revisão humana antes de prosseguir

---

### Fase 2: Agentes de Suporte

---

#### Task 6: rev — seção Skills + 1 gatilho

**Description:** Inserir seção `## Skills` entre L67 e L70
e converter 1 menção passiva (2 skills) em gatilho
imperativo. Adicionar 2 skills novas: code-simplification,
api-and-interface-design.

**Acceptance criteria:**
- [ ] Seção `## Skills` presente com 1 obrig + 3 cond
- [ ] 1 menção passiva convertida para gatilho imperativo
- [ ] Nenhuma linha excede 120 colunas
- [ ] Frontmatter YAML inalterado

**Verification:**
- [ ] `grep -n "consulte a skill\|consulte \`" agents/rev.md`
  retorna zero resultados
- [ ] `awk 'length > 120' agents/rev.md` retorna zero linhas

**Dependencies:** Nenhuma
**Files likely touched:** `agents/rev.md`
**Estimated scope:** S (1 arquivo, ~3 edições)

---

#### Task 7: analista — seção Skills + 1 gatilho

**Description:** Inserir seção `## Skills` após frontmatter
(L16) e antes de `## Papel` (L19). Converter 1 menção
passiva em gatilho imperativo. Adicionar 1 skill nova:
spec-driven-development.

**Acceptance criteria:**
- [ ] Seção `## Skills` presente com 1 obrig + 1 cond
- [ ] 1 menção passiva convertida para gatilho imperativo
- [ ] Nenhuma linha excede 120 colunas
- [ ] Frontmatter YAML inalterado

**Verification:**
- [ ] `grep -n "conforme a skill" agents/analista.md`
  retorna zero resultados (convertido para imperativo)
- [ ] `awk 'length > 120' agents/analista.md` retorna zero linhas

**Dependencies:** Nenhuma
**Files likely touched:** `agents/analista.md`
**Estimated scope:** S (1 arquivo, ~3 edições)

---

#### Task 8: curador-produto — seção Skills + 1 gatilho

**Description:** Inserir seção `## Skills` após seção
`## O que você faz` (L97) e antes de `## Arquivo de
Documentação do Produto` (L99). Converter 1 menção passiva
em gatilho imperativo. Adicionar 1 skill nova:
documentation-and-adrs.

**Acceptance criteria:**
- [ ] Seção `## Skills` presente com 1 obrig + 1 cond
- [ ] 1 menção passiva convertida para gatilho imperativo
- [ ] Nenhuma linha excede 120 colunas
- [ ] Frontmatter YAML inalterado

**Verification:**
- [ ] `grep -n "consulte a skill" agents/curador-produto.md`
  retorna zero resultados
- [ ] `awk 'length > 120' agents/curador-produto.md`
  retorna zero linhas

**Dependencies:** Nenhuma
**Files likely touched:** `agents/curador-produto.md`
**Estimated scope:** S (1 arquivo, ~3 edições)

---

#### Task 9: curador-produto-editor — seção Skills + 1 gatilho

**Description:** Inserir seção `## Skills` após parágrafo
introdutório (L29) e antes de `## O que você faz` (L32).
Converter 1 menção passiva em gatilho imperativo.
Adicionar 1 skill nova: documentation-and-adrs.

**Acceptance criteria:**
- [ ] Seção `## Skills` presente com 2 obrig
- [ ] 1 menção passiva convertida para gatilho imperativo
- [ ] Nenhuma linha excede 120 colunas
- [ ] Frontmatter YAML inalterado

**Verification:**
- [ ] `grep -n "conforme a skill" agents/curador-produto-editor.md`
  retorna zero resultados
- [ ] `awk 'length > 120' agents/curador-produto-editor.md`
  retorna zero linhas

**Dependencies:** Nenhuma
**Files likely touched:** `agents/curador-produto-editor.md`
**Estimated scope:** S (1 arquivo, ~3 edições)

---

### Checkpoint: Fase 2
- [ ] Todos os 4 agentes de suporte têm seção `## Skills`
- [ ] Zero menções passivas nos 4 agentes
- [ ] Zero linhas > 120 colunas nos 4 agentes
- [ ] Todos os frontmatters YAML intactos

---

### Fase 3: Caso Especial

---

#### Task 10: aws-analista — seção Skills adaptada

**Description:** Inserir seção `## Skills` adaptada (apenas
transversais) antes de `## Regras operacionais` (L20).
Adicionar 1 skill nova: debugging-and-error-recovery.
Sem edições cirúrgicas (não há menções passivas).

**Acceptance criteria:**
- [ ] Seção `## Skills` presente com 1 transversal
- [ ] Nenhuma linha excede 120 colunas
- [ ] Frontmatter YAML inalterado

**Verification:**
- [ ] `awk 'length > 120' agents/aws-analista.md`
  retorna zero linhas
- [ ] Seção `## Skills` visível no arquivo

**Dependencies:** Nenhuma
**Files likely touched:** `agents/aws-analista.md`
**Estimated scope:** XS (1 arquivo, 1 edição)

---

### Checkpoint: Fase 3 + Validação Final
- [ ] 10 agentes com seção `## Skills` (5 execução + 4 suporte + 1 especial)
- [ ] 4 agentes inalterados (devflow, val-harness, revisor-historia, smart-planner)
- [ ] Grep global: `grep -rn "consulte a skill\|consulte \`\|ver skill" agents/*.md`
  retorna zero resultados em agentes editados
- [ ] Grep global: `awk 'length > 120' agents/*.md` retorna zero linhas novas
- [ ] `make test-opencode` passa sem regressão

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Linha > 120 colunas ao inserir tabela | Medium | Verificar com `awk` após cada task |
| Quebrar frontmatter YAML | High | Não tocar nas primeiras N linhas (frontmatter) |
| Perder conteúdo existente | High | Apenas adicionar e substituir, nunca remover blocos |
| Menção passiva residual | Low | Grep de verificação no checkpoint |
| Testes BATS quebram | Low | Agentes são Markdown — testes não validam conteúdo |

## Open Questions

Nenhuma — todas as decisões foram resolvidas com o humano.

---

## Apêndice: Referência de Edições

Este apêndice contém o conteúdo exato a inserir e as
edições cirúrgicas para cada agente. O executor deve
usar este apêndice como fonte de verdade para as edições.

### A1. eng-software.md

**Seção Skills** (inserir entre L80 `---` e L83
`## Capacidades`):

```markdown
## Skills

### Obrigatórias (carregar ANTES da capacidade indicada)

| Skill | Capacidade | Quando |
|-------|-----------|--------|
| test-driven-development | Construir via TDD | Sempre que escrever código produtivo |
| tests-as-spec | Proteger testes como spec | Sempre que houver testes existentes |
| grill-me | Validar decisões | Em planejamento e gates |
| planning-and-task-breakdown | Planejar implementação | Na capacidade 1 (planejar) |
| documentation-and-adrs | Registrar decisões arquiteturais | Quando decisão arquitetural significativa |

### Condicionais (carregar quando a condição se aplicar)

| Skill | Capacidade | Condição |
|-------|-----------|----------|
| api-and-interface-design | Planejar implementação | Quando a tarefa envolver API ou interface pública |
| code-simplification | Refatorar código | No gate de refatoração |
| code-review-and-quality | Aplicar ajustes integrativos | Na capacidade 3 (ajustes de revisão) |
| debugging-and-error-recovery | Diagnosticar falhas | Quando testes falham ou build quebra |
| performance-optimization | Otimizar performance | Quando há requisitos de performance |

### Transversais (úteis em qualquer capacidade)

| Skill | Uso |
|-------|-----|
| code-explorer-priority | Buscar código no repositório |
```

**Gatilhos:**

1. L115-116 (capacidade 1, passo 7):
   - OLD: `sugerir registro em ADR (ver skill` /
     ``documentation-and-adrs`).``
   - NEW: `sugerir registro em ADR. **ANTES** de criar o` /
     `ADR, carregue a skill `documentation-and-adrs` —` /
     `ela define o template e o processo de registro.`

2. L184-187 (após Etapa 3):
   - OLD: `Para detalhes do ciclo TDD, padrões de teste` /
     `e boas práticas, consulte a skill` /
     ``test-driven-development`. Para critérios de` /
     `simplificação na refatoração, consulte` /
     ``code-simplification`.``
   - NEW: `**ANTES** de escrever testes, carregue a skill` /
     ``test-driven-development` — ela define o ciclo` /
     `red-green-refactor e padrões de teste.` /
     `No gate de refatoração, carregue` /
     ``code-simplification` para critérios de` /
     `simplificação.`

3. L202-203 (capacidade 3):
   - OLD: `Para referência de qualidade na aplicação dos` /
     `ajustes, consulte a skill` /
     ``code-review-and-quality`.``
   - NEW: `**ANTES** de aplicar ajustes, carregue a skill` /
     ``code-review-and-quality` — ela define o checklist` /
     `multi-eixo de revisão.`

4. L218-219 (Regras Internas):
   - OLD: `Consulte a skill `tests-as-spec`.`
   - NEW: `**ANTES** de modificar qualquer teste existente,` /
     `carregue a skill `tests-as-spec` — ela define a` /
     `imutabilidade de testes na construção.`

5. L254-256 (Boas Práticas):
   - OLD: `Para diretrizes de construção, consulte as` /
     `skills `test-driven-development`,` /
     ``code-simplification` e `documentation-and-adrs`.``
   - NEW: `As skills obrigatórias e condicionais para este` /
     `agente estão listadas na seção `## Skills` acima.` /
     `Carregue-as conforme indicado antes de cada` /
     `capacidade.`

### A2. front.md

**Seção Skills** (inserir entre L78 `---` e L81
`## Capacidades`):

```markdown
## Skills

### Obrigatórias (carregar ANTES da capacidade indicada)

| Skill | Capacidade | Quando |
|-------|-----------|--------|
| frontend-ui-engineering | Implementar UI | Sempre que implementar componentes visuais |
| accessibility-audit | Garantir acessibilidade | Sempre que produzir componentes visuais |
| grill-me | Validar decisões visuais | Na prototipagem de telas |

### Condicionais (carregar quando a condição se aplicar)

| Skill | Capacidade | Condição |
|-------|-----------|----------|
| code-simplification | Simplificar componentes | No gate de refatoração de componentes |
| performance-optimization | Otimizar performance de UI | Quando há requisitos de Core Web Vitals ou bundle size |

### Transversais (úteis em qualquer capacidade)

| Skill | Uso |
|-------|-----|
| code-explorer-priority | Buscar código no repositório |
```

**Gatilhos:**

1. L175-176 (capacidade 2):
   - OLD: `Para detalhes de frontend, padrões de` /
     `acessibilidade e boas práticas, consulte a skill` /
     ``frontend-ui-engineering`.``
   - NEW: `**ANTES** de implementar componentes, carregue a` /
     `skill `frontend-ui-engineering` — ela define padrões` /
     `de acessibilidade, responsividade e boas práticas de` /
     `UI. Carregue também `accessibility-audit` para o` /
     `checklist de conformidade WCAG.`

### A3. dba.md

**Seção Skills** (inserir entre L60 `---` e L63
`## Capacidades`):

```markdown
## Skills

### Obrigatórias (carregar ANTES da capacidade indicada)

| Skill | Capacidade | Quando |
|-------|-----------|--------|
| grill-me | Validar decisões de modelagem | Na modelagem de dados |
| planning-and-task-breakdown | Planejar migração | Na capacidade 1 (modelar dados) |

### Condicionais (carregar quando a condição se aplicar)

| Skill | Capacidade | Condição |
|-------|-----------|----------|
| security-and-hardening | Proteger dados | Na revisão de segurança de artefatos de BD |
| debugging-and-error-recovery | Diagnosticar falhas | Quando migração falha ou lock inesperado |
```

**Gatilhos:**

1. L179 (Checklist de Revisão, item Segurança):
   - OLD: `**Segurança** (ref: skill` /
     `security-and-hardening):`
   - NEW: `**Segurança** — **ANTES** de revisar segurança` /
     `de artefatos de BD, carregue a skill` /
     ``security-and-hardening`:`

### A4. sec.md

**Seção Skills** (inserir entre L75 `---` e L78
`## Capacidades`):

```markdown
## Skills

### Obrigatórias (carregar ANTES da capacidade indicada)

| Skill | Capacidade | Quando |
|-------|-----------|--------|
| security-and-hardening | Analisar segurança | Sempre que analisar ou revisar segurança |
| grill-me | Validar decisões | Na análise de requisitos de segurança |

### Condicionais (carregar quando a condição se aplicar)

| Skill | Capacidade | Condição |
|-------|-----------|----------|
| code-review-and-quality | Revisar segurança | Na capacidade 3 (revisar e corrigir) |
| debugging-and-error-recovery | Diagnosticar falhas | Quando ferramentas de segurança falham inesperadamente |
```

**Gatilhos:**

1. L114-115 (capacidade 1):
   - OLD: `Para checklist OWASP e padrões de hardening,` /
     `consulte a skill `security-and-hardening`.`
   - NEW: `**ANTES** de avaliar requisitos de segurança,` /
     `carregue a skill `security-and-hardening` — ela` /
     `define o checklist OWASP e os padrões de hardening.`

2. L162-163 (capacidade 3):
   - OLD: `Para eixo "security" de code review, consulte` /
     `a skill `code-review-and-quality`.`
   - NEW: `**ANTES** de revisar segurança do código,` /
     `carregue a skill `code-review-and-quality` — ela` /
     `define o eixo "security" da revisão multi-eixo.`

3. L191-192 (capacidade 4):
   - OLD: `Para diagnóstico de falhas inesperadas, consulte` /
     `a skill `debugging-and-error-recovery`.`
   - NEW: `**Se** ferramentas de segurança falharem` /
     `inesperadamente, carregue a skill` /
     ``debugging-and-error-recovery` para diagnóstico` /
     `sistemático.`

### A5. qa.md

**Seção Skills** (inserir entre L70 `---` e L73
`## Capacidades`):

```markdown
## Skills

### Obrigatórias (carregar ANTES da capacidade indicada)

| Skill | Capacidade | Quando |
|-------|-----------|--------|
| test-driven-development | Planejar testes | Sempre que planejar ou revisar testes |
| tests-as-spec | Proteger cobertura como spec | Na revisão de testabilidade e cobertura |
| grill-me | Validar decisões | No planejamento de testes |
| browser-testing | Testes funcionais de UI | Quando houver UI no escopo de testes |

### Condicionais (carregar quando a condição se aplicar)

| Skill | Capacidade | Condição |
|-------|-----------|----------|
| planning-and-task-breakdown | Decompor critérios | Quando decompor critérios de aceitação em cenários |
| debugging-and-error-recovery | Diagnosticar falhas | Quando testes falham inesperadamente |
| accessibility-audit | Auditar acessibilidade | Quando há UI no escopo de testes |
| performance-optimization | Testar performance | Quando há RNF de performance |
```

**Gatilhos:**

1. L111-116 (capacidade 1):
   - OLD: `Para padrões de teste, convenções de` /
     `nomenclatura e anti-padrões, consulte a skill` /
     ``test-driven-development`. Para decomposição de` /
     `critérios de aceitação, consulte` /
     ``planning-and-task-breakdown`. Para testes` /
     `funcionais que requerem navegação em UI, consulte` /
     `a skill `browser-testing`.`
   - NEW: `**ANTES** de planejar testes, carregue a skill` /
     ``test-driven-development` — ela define padrões,` /
     `nomenclatura e anti-padrões de teste.` /
     `Para decompor critérios de aceitação em cenários,` /
     `carregue `planning-and-task-breakdown`.` /
     `Quando houver UI no escopo, carregue` /
     ``browser-testing` para testes funcionais com` /
     `Playwright.`

2. L139-140 (capacidade 2):
   - OLD: `Para o princípio de testes como especificação e` /
     `suas implicações em cobertura, consulte` /
     ``tests-as-spec`.``
   - NEW: `**ANTES** de revisar cobertura, carregue a skill` /
     ``tests-as-spec` — ela define testes como` /
     `especificação imutável e suas implicações.`

3. L170-171 (capacidade 3):
   - OLD: `Para diagnóstico de falhas, consulte a skill` /
     ``debugging-and-error-recovery`.``
   - NEW: `**Se** testes falharem inesperadamente, carregue` /
     `a skill `debugging-and-error-recovery` para` /
     `diagnóstico sistemático antes de reportar.`

### A6. rev.md

**Seção Skills** (inserir entre L67 `---` e L70
`## Capacidade`):

```markdown
## Skills

### Obrigatórias (carregar ANTES da capacidade indicada)

| Skill | Capacidade | Quando |
|-------|-----------|--------|
| code-review-and-quality | Revisão multi-eixo | Sempre que fazer revisão integrativa |

### Condicionais (carregar quando a condição se aplicar)

| Skill | Capacidade | Condição |
|-------|-----------|----------|
| documentation-and-adrs | Avaliar documentação | Quando revisar consistência de docs |
| code-simplification | Identificar complexidade | Quando revisar qualidade de código |
| api-and-interface-design | Avaliar interfaces | Quando revisar consistência de API ou interface pública |
```

**Gatilhos:**

1. L107-110 (após Saídas):
   - OLD: `Para critérios de revisão multi-eixo, consulte` /
     `a skill `code-review-and-quality`. Para avaliar se` /
     `documentação está consistente, consulte a skill` /
     ``documentation-and-adrs`.``
   - NEW: `**ANTES** de iniciar a revisão integrativa,` /
     `carregue a skill `code-review-and-quality` — ela` /
     `define o checklist multi-eixo (correção,` /
     `legibilidade, arquitetura, segurança, performance).` /
     `Quando revisar consistência de documentação,` /
     `carregue `documentation-and-adrs` para critérios de` /
     `ADR e docs.`

### A7. analista.md

**Seção Skills** (inserir após L16 frontmatter e antes
de L19 `## Papel`):

```markdown
## Skills

### Obrigatórias (carregar ANTES da capacidade indicada)

| Skill | Capacidade | Quando |
|-------|-----------|--------|
| grill-me | Conduzir entrevista | Sempre que elicitar escopo |

### Condicionais (carregar quando a condição se aplicar)

| Skill | Capacidade | Condição |
|-------|-----------|----------|
| spec-driven-development | Estruturar specs | Quando definir estrutura de elicitação com o humano |
```

**Gatilhos:**

1. L122-123 (Comportamento de Entrevistador):
   - OLD: `Ao interagir com o humano durante a elicitação,` /
     `adote comportamento de entrevistador conforme a` /
     `skill `grill-me`: uma pergunta por vez, sempre com` /
     `resposta recomendada embutida, explorando o` /
     `repositório e o contexto antes de perguntar o que` /
     `já está documentado, percorrendo ramos da decisão` /
     `sistematicamente até entendimento compartilhado.`
   - NEW: `**ANTES** de iniciar a elicitação, carregue a` /
     `skill `grill-me`. Adote comportamento de` /
     `entrevistador: uma pergunta por vez, sempre com` /
     `resposta recomendada embutida, explorando o` /
     `repositório e o contexto antes de perguntar o que` /
     `já está documentado, percorrendo ramos da decisão` /
     `sistematicamente até entendimento compartilhado.`

### A8. curador-produto.md

**Seção Skills** (inserir após L97 `---` e antes de
L99 `## Arquivo de Documentação do Produto`):

```markdown
## Skills

### Obrigatórias (carregar ANTES da capacidade indicada)

| Skill | Capacidade | Quando |
|-------|-----------|--------|
| documentation-and-adrs | Avaliar documentação | Sempre que revisar docs ou detectar ausência |

### Condicionais (carregar quando a condição se aplicar)

| Skill | Capacidade | Condição |
|-------|-----------|----------|
| harness-catalog | Sugerir harness | Quando sugerir organização de harness por agente |
```

**Gatilhos:**

1. L201-202 (final do arquivo):
   - OLD: `Para sugestões de harness por agente, consulte` /
     `a skill `harness-catalog`.`
   - NEW: `**Quando** sugerir organização de harness por` /
     `agente, carregue a skill `harness-catalog` — ela` /
     `define o catálogo de referência de harness por` /
     `agente.`

### A9. curador-produto-editor.md

**Seção Skills** (inserir após L29 e antes de L32
`## O que você faz`):

```markdown
## Skills

### Obrigatórias (carregar ANTES da capacidade indicada)

| Skill | Capacidade | Quando |
|-------|-----------|--------|
| documentation-and-adrs | Criar/atualizar docs | Sempre que criar ou atualizar docs/README.md |
| grill-me | Entrevistar humano | Na construção seção por seção do docs/README.md |
```

**Gatilhos:**

1. L256-258 (Comportamento de Entrevistador):
   - OLD: `Ao interagir com o humano durante a construção` /
     `do `docs/README.md` (fluxo seção por seção), adote` /
     `comportamento de entrevistador conforme a skill` /
     ``grill-me`: uma pergunta por vez, sempre com` /
     `resposta recomendada embutida, explorando o` /
     `repositório antes de perguntar o que o código já` /
     `responde, percorrendo ramos da decisão` /
     `sistematicamente até entendimento compartilhado.`
   - NEW: `**ANTES** de iniciar a construção do` /
     ``docs/README.md`, carregue a skill `grill-me`.` /
     `Adote comportamento de entrevistador: uma pergunta` /
     `por vez, sempre com resposta recomendada embutida,` /
     `explorando o repositório antes de perguntar o que o` /
     `código já responde, percorrendo ramos da decisão` /
     `sistematicamente até entendimento compartilhado.` /
     `Carregue também `documentation-and-adrs` para os` /
     `padrões de documentação e ADRs.`

### A10. aws-analista.md

**Seção Skills** (inserir antes de L20
`## Regras operacionais`):

```markdown
## Skills

### Transversais (úteis em qualquer capacidade)

| Skill | Uso |
|-------|-----|
| debugging-and-error-recovery | Diagnosticar problemas em recursos AWS |
```

Sem gatilhos — não há menções passivas no agente.
