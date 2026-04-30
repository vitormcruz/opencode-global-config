# Plano — Implementação do Agente `orq` (Orquestrador)

Status: AGUARDANDO APROVAÇÃO DO HUMANO

---

## 1. Resumo

Criar `agents/orq.md` — roteador stateless que:
- Lê o arquivo de planejamento
- Identifica a fase pelo campo `Status`
- Spawna o agente adequado
- Recebe resumo curto (≤ 5 linhas)
- Nunca executa tarefas de domínio

---

## 2. Comportamentos do `orq` extraídos do workflow

### 2.1 Regras transversais (premissas 1, 2, 3, 5, 7, 16)

| # | Regra | Origem |
|---|-------|--------|
| P1 | Roteador stateless — lê arquivo, identifica fase, spawna agente | Premissa 1 |
| P2 | Resultado no arquivo + resumo curto (≤ 5 linhas) de volta | Premissa 2 |
| P3 | Instância nova a cada fase (obrigatório em voltas, recomendado geral) | Premissa 3 |
| P5 | Falha de agente → registra impedimento → consulta humano (corrigir/ajustar/pular) | Premissa 5 |
| P7 | Humano controla re-revisões (evitar loops infinitos) | Premissa 7 |
| P16 | Campo `Status` no topo do arquivo (ex: `Status: CONSTRUÇÃO — etapa 2/3`) | Premissa 16 |

### 2.2 Ações por fase

#### VALIDAÇÃO
- Cria arquivo de planejamento com `Status: VALIDAÇÃO`
- Spawna `curador-produto` → validar entrada contra docs
- Atualiza `Status: PLANEJAMENTO`

#### PLANEJAMENTO
- Spawna `eng-software` → planejar implementação
- Spawna `dba` → modelagem de dados
- Spawna `sec` → requisitos de segurança (pós-plano código)
- Spawna `qa` → planejar testes
- Atualiza `Status: REVISÃO DO PLANO`

#### REVISÃO DO PLANO
- Spawna `dba` (instância limpa) → revisar modelagem
- Spawna `sec` (instância limpa) → revisar segurança
- Spawna `qa` (instância limpa) → revisar testabilidade
- Spawna `rev` → revisão integrativa
- Se ajustes integrativos: spawna `eng-software` (e/ou especialista)
- Pergunta humano: "Resubmeter?" (P7)
- Apresenta plano ao humano para aprovação
- Atualiza `Status: CONSTRUÇÃO`

#### CONSTRUÇÃO
- Spawna `dba` → criar/atualizar modelo e migrações
- Spawna `eng-software` → TDD (testes → código → refatoração)
- Recebe resultado:
  - Concluído → `Status: REVISÃO DA CONSTRUÇÃO`
  - Gate disparado → `Status: REVISÃO DO PLANO` (volta)

#### REVISÃO DA CONSTRUÇÃO
- Spawna `dba` (instância limpa) → revisar artefatos BD
- Spawna `sec` (instância limpa) → revisar segurança
- Spawna `qa` (instância limpa) → revisar cobertura
- Spawna `rev` → revisão integrativa
- Se ajustes: spawna `eng-software` (e/ou especialista)
- Pergunta humano: "Resubmeter?" (P7)
- Atualiza `Status: TESTES`

#### TESTES
- Spawna `qa` → executar testes automatizados + manuais
- Se falharam: spawna `eng-software` → corrigir → humano decide re-execução
- Spawna `sec` → testes de segurança
- Se falharam: spawna `eng-software` → corrigir → humano decide re-execução
- Atualiza `Status: FINALIZAÇÃO`

#### FINALIZAÇÃO
- Spawna `curador-produto` → revisão final (docs + estrutura)
- Informa humano: funcionalidade concluída

---

## 3. Artefato: `agents/orq.md`

### 3.1 Frontmatter

```yaml
---
description: >
  Orquestrador stateless do workflow multi-agente.
  Lê o arquivo de planejamento, identifica a fase pelo campo Status,
  spawna o agente adequado e recebe resumo curto. Nunca executa tarefas
  de domínio. Entrada: requisitos de nova funcionalidade ou retomada
  de workflow em andamento.
mode: primary
temperature: 0.1
permission:
  edit: allow
  bash: deny
  webfetch: deny
  websearch: deny
  task:
    eng-software: allow
    curador-produto: allow
    dba: allow
    sec: allow
    qa: allow
    rev: allow
---
```

### 3.2 Corpo (estrutura planejada)

Seções do corpo do agente:

1. **Identidade** — roteador stateless, PT-BR, nunca executa domínio
2. **Arquivo de planejamento** — formato esperado, campo Status,
   criação, leitura, atualização de Status
3. **Contrato com agentes spawnados** — resultado no arquivo +
   resumo ≤ 5 linhas; instância nova a cada fase
4. **Tratamento de falha** — impedimento → consulta humano →
   3 opções (corrigir, ajustar escopo, pular com registro)
5. **Fluxo por fase** — tabela de decisão:
   Status lido → ação → agente(s) a spawnar → próximo Status
6. **Governança** — humano aprova plano; humano controla
   re-revisões; sem loops automáticos
7. **Retomada** — se o arquivo já existe com Status preenchido,
   retomar a partir da fase indicada

### 3.3 Compatibilidade VS Code

O `vscode-sync.ps1` já converte `agents/*.md` → `*.agent.md`:
- Strip-AgentFrontmatter mantém apenas `description`
- Resultado: `orq.agent.md` em `%APPDATA%\Code\User\prompts\`
- No VS Code, `orq` usará `runSubagent` para spawnar agentes
- Agentes spawnados precisam ser `mode: primary` para interagir
  com o humano (restrição da plataforma)

**Impacto**: agentes que hoje são `mode: subagent` e que `orq`
precisa spawnar com interação humana:
- `analista-bd.md` → atualmente `mode: subagent` → **precisa mudar
  para `primary`** se for usado como `dba` no workflow
- `revisor-historia.md` → `mode: subagent` → sem impacto (não
  participa do workflow)

**Decisão necessária**: os agentes `dba`, `sec`, `qa`, `rev`,
`eng-software` e `curador-produto` ainda não existem neste repo.
Serão criados em etapa posterior. Este plano cobre apenas o `orq`.

---

## 4. Agentes referenciados pelo workflow (ainda não existentes)

O `orq` referencia agentes que precisarão ser criados:

| Agente no workflow | Existente? | Observação |
|--------------------|-----------|-------------|
| `eng-software` | Não | — |
| `curador-produto` | Não | — |
| `dba` | **Parcial** | `analista-bd` cobre parte do escopo |
| `sec` | Não | — |
| `qa` | Não | — |
| `rev` | Não | — |

**Decisão para o humano**: mapear `analista-bd` → `dba` (renomear?)
ou manter separados? Isso afeta o `task` permission do `orq`.

---

## 5. Modificações em testes

### 5.1 Teste existente: `tests/opencode-int-test/agents-test.bats`

Adicionar:

```bats
@test "behavioral: GET /agent lista o agente orq" {
  run curl -sf "${OPENCODE_BASE_URL}/agent"
  assert_success
  assert_output --partial "orq"
}
```

### 5.2 Nenhum outro teste existente é afetado

- `commands-test.bats`, `skills-activation-test.bats`, etc. não
  tocam em agentes.

---

## 6. Checklist de entrega

- [ ] Criar `agents/orq.md` com frontmatter + corpo
- [ ] Adicionar teste em `agents-test.bats`
- [ ] Rodar `make test` — validar que o novo agente é listado
- [ ] Verificar que `vscode-sync.ps1` gera `orq.agent.md` corretamente
- [ ] Atualizar `AGENTS.md` se necessário (description do orq no
      contexto de agentes disponíveis)

---

## 7. Decisões pendentes (para o humano)

1. **Mapeamento `analista-bd` ↔ `dba`**: renomear ou manter separados?
2. **Agentes inexistentes**: o `orq` deve ser criado agora referenciando
   agentes futuros (graceful fallback) ou só após todos existirem?
3. **Formato do arquivo de planejamento**: definir template agora ou
   deixar para a implementação do `eng-software`?
4. **Harnesses do orq**: incluir regras de harness (ex: timeout por
   fase, limite de re-tentativas) ou manter simples na v1?
