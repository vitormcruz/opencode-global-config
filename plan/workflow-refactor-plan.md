# Plano: Refatorar Workflows de Curadoria e Definicao de Escopo

**Data:** 2026-06-12
**Tipo:** Refatoracao de workflows

---

## Resumo das Decisoes

- **Estrategia:** Refatoracao completa (separar responsabilidades)
- **Ponto de entrada:** `devflow` sempre executa sequencia completa: curadoria → escopo → desenvolvimento
- **Organizacao:** workflow-agentes-dev.md terah links claros para workflow-curadoria.md e workflow-definicao-escopo.md

---

## Objetivo

Separar e reorganizar os workflows para que curadoria, definicao de escopo e desenvolvimento sejam fases independentes e bem definidas, com responsabilidades claras e links explicitos entre eles.

---

## Fases de Implementacao

### Phase 1: Preparacao e Analise (paralelo)

1. Analisar workflow-agentes-dev.md completo para identificar onde inserir chamadas
2. Revisar workflow-curadoria.md atual — verificar se precisa de complementacao
3. Verificar agentes/curador-produto.md e agentes/curador-produto-editor.md para consistencia

### Phase 1.5: Criar Templates Padrao (paralelo com Phase 1)

4. **Criar pasta `agents/default-artifacts/`**
5. **Criar `agents/default-artifacts/doc-readme.md`** — template com as 3 secoes (Definicao de Escopo, Elementos de Especificacao, Estrategias de Indexacao)
6. **Criar `agents/default-artifacts/harness-section.md`** — template da tabela de harness por agente

### Phase 1.6: Definir Conteudo dos Templates

**Arquivo: `agents/default-artifacts/doc-readme.md`**

```markdown
# Documentacao do Produto

## Definicao de Escopo
O analista deve elicitar:
- Requisitos funcionais e nao funcionais
- Criterios de aceitacao por exemplos
- Organizados por historias de usuario
- Criterios devem referenciar requisitos funcionais
- Nenhum requisito pode ficar sem criterio
- **Skill recomendada:** `grill-me` (entrevista estruturada com humano)

## Elementos de Especificacao

| Elemento | Formato/Ferramenta | Agente Responsavel | Destino |
|----------|-------------------|-------------------|---------|
| Criterios de Aceite + Requisitos | Concordion | eng-software | docs/specs/ |
| Regras de Produto | Tabela | eng-software | nenhum |
| Modelo de Dados | DBML | dba | docs/modelo.dbml |
| Threat Model | Markdown | sec | docs/threat-model.md |
| Plano de Testes | Markdown | qa | nenhum |
| Identidade Visual | Prototipo HTML/SVG | front | plan/ui/ |
| ADR (Arquitetura) | Markdown | eng-software | docs/adr/ |

### Regras Gerais
- Documentacao complementa o codigo, nao o repete
- Doc derivavel do codigo nao se armazena — gere sob demanda
- Doc desatualizada e pior que ausencia de doc
- Preferir formatos versionaveis (Markdown, Mermaid, DBML)

##### Criterios de Aceite + Requisitos
Os criterios de aceite devem estar organizados por Funcionalidade levando-se em conta a coesao. Cada funcionalidade deve ter um arquivo Concordion separado. Cenarios devem ser expressos em linguagem natural e executaveis.

##### Regras de Produto
Regras de negocio devem ser documentadas em tabela com: ID da regra, descricao, origem (requisito), e agente responsavel pela verificacao.

##### Modelo de Dados
Schema de banco deve ser versionado em DBML. DBA verifica consistencia entre modelo e schema real via diff. Convencoes de nomenclatura SQL seguem padrao do projeto (lowercase_com_snake_case, nomes no singular para tabelas e colunas).

##### Threat Model
Modelo de ameacas segue STRIDE. Cadastro e pagamento sao areas de elevada atencao. OWASP Top 10 deve ser verificado.

##### Plano de Testes
Plano define: estrategia de testes, ambientes, tipos de teste (unit, integracao, aceitacao), criterios de entrada/saida, e responsabilidades por agente.

##### Identidade Visual
Prototipos devem ser validados pelo humano antes de implementacao. Design system baseado em shadcn/ui (preset new-york) com Tailwind CSS 4.

##### ADR (Arquitetura)
ADR registra decisoes arquiteturais significativas. Formato: contexto, decisao, consequencias, status (proposed/accepted/deprecated/superseded).

## Estrategias de Indexacao de Codigo

- codebase-memory
```

**Arquivo: `agents/default-artifacts/harness-section.md`**

Estrutura híbrida: tabela + subseções detalhadas

```markdown
## Harness por Agente

| Agente | Comando | Descrição | Detalhes |
|--------|---------|-----------|----------|
| eng-software | `harness/eng-software.sh` | Testes, análise estática | [Ver detalhes](#agente-eng-software) |
| dba | `harness/dba.sh` | Validação de schema | [Ver detalhes](#agente-dba) |
| sec | `harness/sec.sh` | OWASP checks, secrets | [Ver detalhes](#agente-sec) |
| qa | `harness/qa.sh` | Cobertura, aceitação | [Ver detalhes](#agente-qa) |
| front | `harness/front.sh` | Linting, a11y | [Ver detalhes](#agente-front) |
| rev | — | SEM HARNESS | [Ver detalhes](#agente-rev) |
| val-harness | — | SEM HARNESS | [Ver detalhes](#agente-val-harness) |
| curador-produto | — | SEM HARNESS | [Ver detalhes](#agente-curador-produto) |

### Detalhes por Agente

#### Agente: eng-software
**Arquivo:** `harness/eng-software.sh`
**Descrição:** Testes, análise estática, cobertura
**O que deve conter:**
- Ferramentas de teste específicas do projeto
- Analisadores estáticos (lint, typecheck)
- Validação de cobertura mínima
- Critérios de harness: [a definir com humano]

#### Agente: dba
**Arquivo:** `harness/dba.sh`
**Descrição:** Validação de schema, migrações
**O que deve conter:**
- Validação de schema contra modelo DBML
- Teste de migrações (up/down)
- Checks de performance de queries
- Critérios de harness: [a definir com humano]

#### Agente: sec
**Arquivo:** `harness/sec.sh`
**Descrição:** OWASP checks, secrets scanning
**O que deve conter:**
- Escaneamento de secrets
- OWASP dependency check
- SAST (análise estática de segurança)
- Critérios de harness: [a definir com humano]

#### Agente: qa
**Arquivo:** `harness/qa.sh`
**Descrição:** Cobertura de testes, aceitação
**O que deve conter:**
- Validação de critérios de aceite
- Verificação de cobertura de testes
- Testes exploratórios automatizados
- Critérios de harness: [a definir com humano]

#### Agente: front
**Arquivo:** `harness/front.sh`
**Descrição:** Linting, acessibilidade
**O que deve conter:**
- Lint de CSS/HTML/JS
- Validação de acessibilidade (a11y)
- Lighthouse checks
- Critérios de harness: [a definir com humano]

#### Agente: rev
**Status:** `SEM HARNESS A PEDIDO DO HUMANO`
**Justificativa:** Revisor não executa harness, apenas revisa

#### Agente: val-harness
**Status:** `SEM HARNESS A PEDIDO DO HUMANO`
**Justificativa:** Validador de harness não precisa de harness próprio

#### Agente: curador-produto
**Status:** `SEM HARNESS A PEDIDO DO HUMANO`
**Justificativa:** Curador não executa harness, apenas orquestra
```

**Benefícios desta abordagem:**

1. **Visão geral rápida** — tabela permite ver todos os agentes de uma vez
2. **Navegação fácil** — links na coluna "Detalhes" permitem ir direto à subseção
3. **Processamento por agente** — cada subseção tem estrutura consistente para o editor processar
4. **Extensível** — adicionar novo agente = adicionar linha na tabela + subseção

**Fluxo do curador-produto-editor com este template:**
1. Copia doc-readme.md para `docs/README.md`
2. Para cada secao, pergunta ao humano:
   - "Quer manter esta secao como esta?"
   - "Quer modificar alguma parte?"
3. Se humano escolher modificar → entrevista seccao por secao usando grill-me
4. Gera scripts de harness baseado na tabela de Elementos
5. Commit com msg: "chore(setup): scaffold inicial de documentacao e harness"

### Phase 2: Refatoracao dos Workflows (depende das Phases 1 e 1.5)

#### 2.1 — workflow-curadoria.md
8. Garantir conteudo completo de validacao (README + AGENTS.md)
9. Verificar fluxo com curador-produto → curador-produto-editor
10. Definir criterios de saída ("curadoria OK" ou "necessario criar documentacao")

#### 2.2 — workflow-definicao-escopo.md (simplificado)
11. Remover completamente a Fase 1 (Validacao) — agora fica em workflow-curadoria
12. Atualizar a tabela de agentes — remover curador-produto e curador-produto-editor
13. Simplificar fluxo para: ELICITACAO apenas (analista)
14. Atualizar premissas — assumir que curadoria ja foi feita
15. Atualizar diagrama de sequencia — remover bloco de validacao

#### 2.3 — workflow-agentes-dev.md (orquestrador)
16. Adicionar secao inicial descrevendo a sequencia dos workflows filhos
17. Inserir link/referencia explicita: [`workflow-curadoria.md`](workflow-curadoria.md)
18. Inserir link/referencia explicita: [`workflow-definicao-escopo.md`](workflow-definicao-escopo.md)
19. Atualizar diagrama para refletir: devflow → curadoria → escopo → dev

### Phase 2.4: Corrigir Caminho /doc/ → docs/

20. Corrigir todas as referencias de `/doc/README.md` para `docs/README.md` em:
    - `agents/curador-produto.md`
    - `agents/curador-produto-editor.md`
    - `docs/workflow-curadoria.md`
    - `docs/workflow-definicao-escopo.md`
    - `docs/workflow-agentes-dev.md`

### Phase 3: Sincronizacao e Validacao (depende da Phase 2)

21. Atualizar `agents/curador-produto-editor.md`:
    - Referenciar templates em `agents/default-artifacts/`
    - Fluxo: copiar templates → perguntar se quer modificar → se nao, sugerir commit → encerrar
22. Verificar se agentes/curador-produto.md e agentes/curador-produto-editor.md precisam atualizacao
23. Verificar consistencia entre docs/workflow-*.md (AGENTS.md menciona workflows)
24. Rodar testes para garantir que links e referencias estao corretos

---

## Detalhes da Migracao: workflow-definicao-escopo → workflow-curadoria

### Conteudo que DEVE ser movido/ajustado:

#### 1. workflow-curadoria.md — Adicionar:
- [ ] Anotacao sobre sequencia: "workflow-curadoria → workflow-definicao-escopo → PLANEJAMENTO"
- [ ] Premissa sobre curadoria ser autonoma e nao chamar analista
- [ ] Diagrama de sequencia completo (ja existe, verificar se cobre devflow → curador → editor)

#### 2. workflow-definicao-escopo.md — Remover:
- [ ] **Objetivo:** Remover parte sobre "Validacao" (deixa so "Elicitacao")
- [ ] **Agentes:** Remover curador-produto e curador-produto-editor da tabela
- [ ] **Premissa #2:** Remover "Workflow de curadoria eh autonomo"
- [ ] **Fase 1:** Remover toda a secao "Fase 1: Validacao"
- [ ] **Diagrama:** Remover participantes curador-produto e curador-produto-editor
- [ ] Manter so: devflow → analista (para elicitacao)

#### 3. workflow-agentes-dev.md — Adicionar:
- [ ] Secao inicial descrevendo a sequencia completa:
  ```
  devflow → workflow-curadoria → workflow-definicao-escopo → PLANEJAMENTO
  ```
- [ ] Explicar que workflow-curadoria executa primeiro (validacao)
- [ ] Que workflow-definicao-escopo executa depois (elicita)
- [ ] Que PLANEJAMENTO comeca apos ambos

### Verificacoes antes de apagar:

| Item | workflow-curadoria ja tem? | Acao |
|------|---------------------------|------|
| Fluxo devflow → curador → editor | Sim (diagrama existe) | OK |
| Templates em default-artifacts/ | Referencia, mas pasta nao existe | Criar pasta |
| Premissa curadoria autonoma | Nao explicitamente | Adicionar |
| Sequencia → definicao-escopo | Nao | Adicionar nota |
| Fluxo curador-produto stateless | Sim | OK |

### Checklist de migracao:

- [ ] Ler todo workflow-curadoria.md (completo)
- [ ] Comparar com Fase 1: Validacao do workflow-definicao-escopo
- [ ] Garantir que nada sera perdido na separacao
- [ ] Atualizar workflow-curadoria.md (adicionar nota e premissa)
- [ ] So depois: remover Fase 1 do workflow-definicao-escopo

---

## Arquivos Relevantes

| Arquivo | O que Modificar |
|---------|-----------------|
| `docs/workflow-curadoria.md` | Validacao de documentacao e harness (garantir completude) |
| `docs/workflow-definicao-escopo.md` | Elicitacao de requisitos (simplificar, remover validacao) |
| `docs/workflow-agentes-dev.md` | Orquestrador principal (adicionar links e sequencia) |
| `agents/curador-produto.md` | Verificar consistencia |
| `agents/curador-produto-editor.md` | Verificar consistencia |
| `agents/default-artifacts/` | CRIAR — pasta com templates |

---

## Fluxo Desejado (Depois da Refatoracao)

```
workflow-agentes-dev.md (orquestrador)
├── workflow-curadoria.md (validacao de docs/harness)
│   ├── curador-produto (verifica)
│   └── curador-produto-editor (copia templates, pergunta ao humano)
├── workflow-definicao-escopo.md (elicitar o que construir)
│   └── analista (entrevista humano, gera Arquivo de Planejamento)
└── [continua fluxo de desenvolvimento normal]
```

---

## Criterios de Aceitacao

- [ ] workflow-curadoria.md contem toda a logica de validacao de documentacao
- [ ] workflow-definicao-escopo.md contem apenas elicitacao (sem agentes de curadoria)
- [ ] workflow-agentes-dev.md tem links explicitos para os dois workflows filhos
- [ ] Diagramas de sequencia refletem o novo fluxo
- [ ] Agentes atualizados consistentemente
- [ ] Templates em agents/default-artifacts/ criados
- [ ] **Testes automatizados passam** — executar `make test` antes de considerar concluido
- [ ] **Testes de integracao passam** — workflows funcionam em sequencia completa
- [ ] **Sem regressoes** — testes existentes nao quebram

---

## Decisoes Tomadas (via grill-me)

1. **Refatoracao completa** — separar responsabilidades claras
2. **Sequencia fixa** — devflow sempre faz curadoria → escopo → desenvolvimento
3. **Workflows independentes** — cada um pode ser reusado separadamente
4. **Templates externos** — extrair de curador-produto-editor.md para arquivos separados
5. **Fluxo do editor** — copiar templates → perguntar ao humano → se nao quiser modificar, sugerir commit
6. **Caminho unificado** — usar `docs/README.md` em vez de `/doc/README.md`
