# Plano — Implementação do Agente `orq` (Orquestrador)

Status: AGUARDANDO APROVAÇÃO DO HUMANO

---

## 1. Resumo

Criar `agents/orq.md` — roteador stateless com duas funções:
- **Rotear**: lê o arquivo de planejamento, identifica a fase
  pelo campo `Status`, spawna o agente adequado, recebe resumo
  curto (≤ 5 linhas)
- **Verificar harness**: após cada retorno de agente, verifica
  se as evidências de execução do harness foram produzidas.
  **Esta é a tarefa mais importante do `orq`** (premissa 32)
- Nunca executa tarefas de domínio

---

## 2. Decisões resolvidas

| # | Decisão | Resolução |
|---|---------|-----------|
| D1 | Mapeamento `analista-bd` ↔ `dba` | `analista-bd` será renomeado para `dba` (via `git mv`) |
| D2 | Agentes inexistentes | `orq` será criado agora; agentes futuros serão conectados quando prontos |
| D3 | Template do arquivo de planejamento | Não será definido agora |

---

## 3. Comportamentos do `orq` extraídos do workflow

### 3.1 Regras transversais (premissas 1, 2, 3, 5, 7, 16, 30–32)

| # | Regra | Origem |
|---|-------|--------|
| P1 | Roteador stateless — lê arquivo, identifica fase, spawna agente | Premissa 1 |
| P2 | Resultado no arquivo + resumo curto (≤ 5 linhas) de volta | Premissa 2 |
| P3 | Instância nova a cada fase (obrigatório em voltas, recomendado geral) | Premissa 3 |
| P5 | Falha de agente → registra impedimento → consulta humano | Premissa 5 |
| P7 | Humano controla re-revisões (evitar loops infinitos) | Premissa 7 |
| P16 | Campo `Status` no topo do arquivo | Premissa 16 |
| P30 | Harness é artefato formal — `curador-produto` co-confecciona | Premissa 30 |
| P31 | Agente produz lista de evidências de harness ao final | Premissa 31 |
| P32 | **`orq` verifica evidências de harness** — rejeita retorno incompleto | Premissa 32 |

### 3.2 Verificação de harness (detalhamento)

Após cada retorno de agente, `orq` deve:
1. Verificar se o resumo contém a lista de evidências de harness
2. Validar que cada item do harness do agente tem evidência
   correspondente (apontando para log ou artefato)
3. Se ausente ou incompleta → rejeitar retorno e solicitar
   que o agente complete a execução
4. Só avançar para o próximo passo quando evidências estiverem OK

O `orq` não avalia a **qualidade** das evidências (isso é
domínio dos revisores) — verifica apenas a **presença** e
**completude** da lista.

### 3.3 Ações por fase

#### VALIDAÇÃO
- Cria arquivo de planejamento com `Status: VALIDAÇÃO`
- Spawna `curador-produto` → validar entrada contra docs
- ✓ Verifica evidências de harness do `curador-produto`
- Atualiza `Status: PLANEJAMENTO`

#### PLANEJAMENTO
- Spawna `eng-software` → planejar implementação
- ✓ Verifica evidências de harness
- Spawna `dba` → modelagem de dados
- ✓ Verifica evidências de harness
- Spawna `sec` → requisitos de segurança (pós-plano código)
- ✓ Verifica evidências de harness
- Spawna `qa` → planejar testes
- ✓ Verifica evidências de harness
- Atualiza `Status: REVISÃO DO PLANO`

#### REVISÃO DO PLANO
- Spawna `dba` (instância limpa) → revisar modelagem
- ✓ Verifica evidências de harness
- Spawna `sec` (instância limpa) → revisar segurança
- ✓ Verifica evidências de harness
- Spawna `qa` (instância limpa) → revisar testabilidade
- ✓ Verifica evidências de harness
- Spawna `curador-produto` → revisar documentação (Mapa)
- ✓ Verifica evidências de harness
- Spawna `rev` → revisão integrativa
- ✓ Verifica evidências de harness
- Se ajustes necessários: spawna `eng-software` (e/ou especialista)
- Pergunta humano: "Resubmeter?" (P7)
- Apresenta plano ao humano para aprovação
- Atualiza `Status: CONSTRUÇÃO`

#### CONSTRUÇÃO
- Spawna `dba` → criar/atualizar modelo e migrações
- ✓ Verifica evidências de harness
- Spawna `eng-software` → TDD (testes → código → refatoração)
- ✓ Verifica evidências de harness
- Recebe resultado:
  - Concluído → `Status: REVISÃO DA CONSTRUÇÃO`
  - Gate disparado → `Status: REVISÃO DO PLANO` (volta)

#### REVISÃO DA CONSTRUÇÃO
- Spawna `dba` (instância limpa) → revisar artefatos BD
- ✓ Verifica evidências de harness
- Spawna `sec` (instância limpa) → revisar segurança
- ✓ Verifica evidências de harness
- Spawna `qa` (instância limpa) → revisar cobertura
- ✓ Verifica evidências de harness
- Spawna `curador-produto` → revisar documentação (Mapa)
- ✓ Verifica evidências de harness
- Spawna `rev` → revisão integrativa
- ✓ Verifica evidências de harness
- Se ajustes: spawna `eng-software` (e/ou especialista)
- Pergunta humano: "Resubmeter?" (P7)
- Atualiza `Status: TESTES`

#### TESTES
- Spawna `qa` → executar testes automatizados + manuais
- ✓ Verifica evidências de harness
- Se falharam: spawna `eng-software` → corrigir → humano decide re-execução
- Spawna `sec` → testes de segurança
- ✓ Verifica evidências de harness
- Se falharam: spawna `eng-software` → corrigir → humano decide re-execução
- Atualiza `Status: FINALIZAÇÃO`

#### FINALIZAÇÃO
- Spawna `curador-produto` → revisão final (docs + estrutura)
- ✓ Verifica evidências de harness
- Informa humano: funcionalidade concluída

---

## 4. Artefato: `agents/orq.md`

### 4.1 Frontmatter

```yaml
---
description: >
  Orquestrador stateless do workflow multi-agente.
  Lê o arquivo de planejamento, identifica a fase pelo campo Status,
  spawna o agente adequado e recebe resumo curto. Após cada retorno,
  verifica evidências de execução do harness — rejeita retornos
  incompletos (premissa 32). Nunca executa tarefas de domínio.
  Entrada: requisitos de nova funcionalidade ou retomada de workflow.
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

### 4.2 Corpo (estrutura planejada)

Seções do corpo do agente:

1. **Identidade** — roteador stateless, PT-BR, nunca executa domínio
2. **Duas funções** — rotear + verificar harness
3. **Arquivo de planejamento** — formato esperado, campo Status,
   criação, leitura, atualização de Status
4. **Contrato com agentes spawnados** — resultado no arquivo +
   resumo ≤ 5 linhas + evidências de harness; instância nova a
   cada fase
5. **Verificação de harness** — protocolo de verificação:
   - Checar presença da lista de evidências no retorno
   - Validar completude contra o harness do agente
   - Rejeitar e solicitar reenvio se incompleto
   - Avançar somente com evidências OK
6. **Tratamento de falha** — impedimento → consulta humano →
   3 opções (corrigir, ajustar escopo, pular com registro)
7. **Fluxo por fase** — tabela de decisão:
   Status lido → ação → agente(s) a spawnar → próximo Status
8. **Governança** — humano aprova plano; humano controla
   re-revisões; sem loops automáticos
9. **Retomada** — se o arquivo já existe com Status preenchido,
   retomar a partir da fase indicada

### 4.3 Compatibilidade VS Code

O `vscode-sync.ps1` já converte `agents/*.md` → `*.agent.md`:
- Strip-AgentFrontmatter mantém apenas `description`
- Resultado: `orq.agent.md` em `%APPDATA%\Code\User\prompts\`
- No VS Code, `orq` usará `runSubagent` para spawnar agentes
- Agentes spawnados precisam ser `mode: primary` para interagir
  com o humano (restrição da plataforma)

---

## 5. Renomeação: `analista-bd` → `dba`

Renomeação já executada via `git mv agents/analista-bd.md
agents/dba.md`. Conteúdo reescrito. Testes atualizados.

---

## 6. Agentes referenciados (ainda não existentes)

| Agente | Existente? | Observação |
|--------|-----------|-------------|
| `eng-software` | Não | Será criado depois |
| `curador-produto` | Não | Será criado depois |
| `dba` | **Sim** | Após renomeação do `analista-bd` |
| `sec` | Não | Será criado depois |
| `qa` | Não | Será criado depois |
| `rev` | Não | Será criado depois |

O `orq` será implementado agora referenciando todos.
Agentes que ainda não existem serão conectados quando prontos.

---

## 7. Modificações em testes

### 7.1 `tests/opencode-int-test/agents-test.bats`

**Adicionar:**

```bats
@test "behavioral: GET /agent lista o agente orq" {
  run curl -sf "${OPENCODE_BASE_URL}/agent"
  assert_success
  assert_output --partial "orq"
}
```

**Alterar** (renomeação analista-bd → dba):

```bats
# DE:
@test "behavioral: GET /agent lista o agente analista-bd" {
  ...
  assert_output --partial "analista-bd"
}

# PARA:
@test "behavioral: GET /agent lista o agente dba" {
  ...
  assert_output --partial "dba"
}
```

### 7.2 Nenhum outro teste existente é afetado

---

## 8. Checklist de entrega

- [ ] `git mv agents/analista-bd.md agents/dba.md`
- [ ] Atualizar conteúdo de `agents/dba.md` (identidade)
- [ ] Criar `agents/orq.md` com frontmatter + corpo
- [ ] Atualizar teste `analista-bd` → `dba` em `agents-test.bats`
- [ ] Adicionar teste do `orq` em `agents-test.bats`
- [ ] Atualizar `AGENTS.md` (referências ao `dba` e novo `orq`)
- [ ] Rodar `make test`
- [ ] Verificar que `vscode-sync.ps1` gera `orq.agent.md` e
      `dba.agent.md` corretamente
