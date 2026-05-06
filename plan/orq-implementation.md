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
  **Esta é a tarefa mais importante do `orq`** (premissa 35)
- Nunca executa tarefas de domínio
- É o **único** agente que conhece o workflow e a sequência de
  fases (premissa 6 — agentes são agnósticos do workflow)

---

## 2. Decisões resolvidas

| # | Decisão | Resolução |
|---|---------|-----------|
| D1 | Mapeamento `analista-bd` ↔ `dba` | Renomeação já executada via `git mv` |
| D2 | Agentes inexistentes | `orq` criado agora; futuros conectados quando prontos |
| D3 | Template do arquivo de planejamento | Não definido agora |
| D4 | Skills do `orq` | Nenhuma skill atribuída — `orq` é router puro (ver seção 9) |

---

## 3. Comportamentos do `orq` extraídos do workflow

### 3.1 Regras transversais (premissas 1–7, 9, 18, 32–35)

| # | Regra | Origem |
|---|-------|--------|
| P1 | Roteador stateless — lê arquivo, identifica fase, spawna agente | Premissa 1 |
| P2 | Resultado no arquivo + resumo curto (≤ 5 linhas) de volta | Premissa 2 |
| P3 | Instância nova a cada fase (obrigatório em voltas, recomendado geral) | Premissa 3 |
| P5 | Falha de agente → registra impedimento → consulta humano | Premissa 5 |
| P6 | **Agentes são agnósticos do workflow** — só `orq` conhece fases e sequência | Premissa 6 |
| P7 | **Seleção de modelo por fase** — pergunta via tool no início do workflow | Premissa 7 |
| P9 | Humano controla re-revisões (evitar loops infinitos) | Premissa 9 |
| P18 | Campo `Status` obrigatório no topo do arquivo | Premissa 18 |
| P32 | Harness definido no Mapa do Produto (não hardcoded) | Premissa 32 |
| P33 | Agente localiza harness no Mapa antes de executar | Premissa 33 |
| P34 | Agente produz evidências (script: exit code+stdout; prompt: declaração) | Premissa 34 |
| P35 | **`orq` verifica evidências de harness** — rejeita retorno incompleto | Premissa 35 |

### 3.2 Verificação de harness (detalhamento)

Sequência completa (workflow P32→P35):
1. Agente localiza seu harness no Mapa do Produto (P33)
2. Agente executa script ou segue regras de prompt
3. Agente produz evidências e persiste no arquivo (P34)
4. **`orq` verifica** presença e completude das evidências (P35)

Protocolo do `orq` após cada retorno:
1. Verificar se o resumo contém a lista de evidências de harness
2. Validar que cada item do harness do agente tem evidência
   correspondente (exit code + stdout para scripts, declaração
   estruturada para prompt-only)
3. Se ausente ou incompleta → rejeitar retorno e solicitar
   que o agente complete a execução
4. Só avançar para o próximo passo quando evidências estiverem OK

O `orq` não avalia a **qualidade** das evidências (domínio dos
revisores) — verifica apenas **presença** e **completude**.

**Caso sem harness**: se o agente retorna informando que não
encontrou harness no Mapa, `orq` registra e recomenda ao humano
acionar `curador-produto` para confeccioná-lo. Pode prosseguir
sem harness se o humano autorizar.

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
- Pergunta humano: "Resubmeter?" (P8)
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
- Pergunta humano: "Resubmeter?" (P8)
- Atualiza `Status: TESTES`

#### TESTES
- Spawna `qa` → executar testes automatizados + manuais
- ✓ Verifica evidências de harness
- Se falharam: spawna `eng-software` → corrigir → humano decide
- Spawna `sec` → testes de segurança
- ✓ Verifica evidências de harness
- Se falharam: spawna `eng-software` → corrigir → humano decide
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
  incompletos (premissa 35). Nunca executa tarefas de domínio.
  Único agente que conhece o workflow e a sequência de fases.
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

1. **Identidade** — roteador stateless, PT-BR, nunca executa domínio,
   único conhecedor do workflow (P6)
2. **Duas funções** — rotear + verificar harness
3. **Arquivo de planejamento** — formato esperado, campo Status,
   criação, leitura, atualização de Status
4. **Contrato com agentes spawnados** — resultado no arquivo +
   resumo ≤ 5 linhas + evidências de harness; instância nova a
   cada fase
5. **Verificação de harness** — protocolo de verificação:
   - Checar presença da lista de evidências no retorno
   - Para scripts: validar exit code + stdout
   - Para prompt-only: validar declaração estruturada
   - Caso agente não encontre harness no Mapa → registrar e
     recomendar ao humano acionar `curador-produto`
   - Rejeitar e solicitar reenvio se incompleto
   - Avançar somente com evidências OK (ou autorização do humano)
6. **Tratamento de falha** — impedimento → consulta humano →
   3 opções (corrigir, ajustar escopo, pular com registro)
7. **Fluxo por fase** — tabela de decisão:
   Status lido → ação → agente(s) a spawnar → próximo Status
8. **Governança** — humano aprova plano; humano controla
   re-revisões; sem loops automáticos
9. **Retomada** — se o arquivo já existe com Status preenchido,
   retomar a partir da fase indicada
10. **Seleção de modelo por fase** — no início do workflow,
    via tool `ask`/`question`, apresentar ao humano:
    - Opção 1: "Usar o modelo atual para todas as fases"
    - Opção 2: "Definir por fase" (resposta livre:
      `<nº>. <modelo>`; fases omitidas = modelo atual)
    Fases: 1-VALIDAÇÃO 2-PLANEJAMENTO 3-REVISÃO DO PLANO
    4-CONSTRUÇÃO 5-REVISÃO DA CONSTRUÇÃO 6-TESTES
    7-FINALIZAÇÃO.
    Registrar mapa no arquivo de planejamento.
    VS Code: passar `model` ao `runSubagent`.
    OpenCode: parar antes de fase com modelo diferente.

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
| `qa` | **Sim** | Criado recentemente |
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

### 7.2 Nenhum outro teste existente é afetado

---

## 8. Checklist de entrega

- [x] `git mv agents/analista-bd.md agents/dba.md`
- [x] Atualizar conteúdo de `agents/dba.md` (identidade)
- [ ] Criar `agents/orq.md` com frontmatter + corpo
- [x] Atualizar teste `analista-bd` → `dba` em `agents-test.bats`
- [ ] Adicionar teste do `orq` em `agents-test.bats`
- [ ] Atualizar `AGENTS.md` (referência ao `orq`)
- [ ] Rodar `make test`
- [ ] Verificar que `vscode-sync.ps1` gera `orq.agent.md`

---

## 9. Análise de skills do repositório

O `orq` é um **router puro** — não executa tarefas de domínio.
Por premissa 6, ele é o único que conhece o workflow. Nenhuma
skill do repo é atribuída diretamente ao `orq`.

Análise das skills curadas do repo vs. relevância para `orq`:

| Skill | Relevância para `orq` | Destinatário real |
|-------|----------------------|-------------------|
| planning-and-task-breakdown | Nenhuma — `orq` não planeja, roteia | `eng-software` |
| spec-driven-development | Nenhuma — `orq` não escreve specs | `eng-software` |
| code-review-and-quality | Nenhuma — `orq` não revisa código | `rev`, `eng-software` |
| test-driven-development | Nenhuma | `eng-software`, `qa` |
| debugging-and-error-recovery | Nenhuma | `eng-software` |
| security-and-hardening | Nenhuma | `sec` |
| documentation-and-adrs | Nenhuma | `curador-produto`, `rev` |
| git-workflow-and-versioning | Nenhuma | `eng-software` |
| api-and-interface-design | Nenhuma | `eng-software` |
| code-simplification | Nenhuma | `eng-software` |
| performance-optimization | Nenhuma | `eng-software` |
| frontend-ui-engineering | Nenhuma | `eng-software` |
| accessibility-audit | Nenhuma | `qa` (via harness) |

**Conclusão**: o `orq` não recebe skills. Suas instruções são
auto-contidas no prompt (workflow + protocolo de verificação).
Skills serão atribuídas aos agentes executores conforme seus
harnesses forem definidos no Mapa do Produto de cada projeto.
