# Plano: Devflow como Mediador de Comunicação Humano-Agente

**Status: PLANEJAMENTO**
**Criado: 2026-07-29**

## 1. Problema

O Devflow atual é roteador stateless puro. A premissa 4 do
`workflow-agentes-dev.md:194` permite que qualquer agente
spawnado consulte o humano diretamente. Isso falha porque:

- **Limitação de plataforma** — VS Code só permite agentes
  primários falarem com humano; OpenCode exige tool `ask`
  em subagentes. A tabela em
  `workflow-agentes-dev.md:849-862` documenta a assimetria.
- **Sem gate de qualidade** — perguntas mal formuladas,
  ambíguas ou sem contexto chegam ao humano sem filtro.
- **Sem gestão de carga cognitiva** — múltiplos agentes
  podem fazer perguntas simultâneas, sobrecarregando o
  humano.

## 2. Solução Proposta

O Devflow acumula uma segunda responsabilidade: **mediador
de comunicação**. Continua roteador stateless, mas passa a
intermediar TODA comunicação agente↔humano quando agentes
são spawnados por ele.

### 2.1 O que o Devflow faz como mediador

- **Avalia estrutura da pergunta** — está clara? Tem
  contexto? Exemplos ou opções ajudariam?
- **Nunca julga conteúdo** — não avalia se a pergunta é
  necessária, não tenta responder, não substitui o humano.
- **Apresenta uma pergunta por vez** — usa grill-me para
  serializar e evitar bombardeio.
- **Pede reformulação ao agente** — se pergunta está
  confusa ou sem contexto, repassa orientação específica
  do que melhorar.
- **Melhora input do humano proativamente** — detecta
  ambiguidade e sugere prompt-improver antes de rotear.

### 2.2 O que o Devflow NÃO faz

- Não responde perguntas no lugar do humano
- Não julga necessidade ou relevância de perguntas
- Não busca código para contextualizar
- Não filtra perguntas por domínio
- Não usa caveman em texto destinado ao humano
- Não executa tarefas de domínio (já era regra)

## 3. Skills Agregadas

| Skill | Gatilho no Devflow | Modo |
|---|---|---|
| **prompt-improver** | Input do humano com ambiguidade detectável | Proativo — Devflow sugere melhoria ao humano antes de rotear |
| **grill-me** | Agente retorna pergunta(s) | Mediação — Devflow usa grill-me para apresentar uma pergunta por vez ao humano, com recomendação |

### 3.1 grill-me — Mediação de perguntas

**Quando usar:**
- Agente retorna com pergunta(s) elaborada(s) ou múltiplas
- Devflow julga que apresentação serializada ajuda o humano
  a não se sobrecarregar
- Pergunta tem trade-offs complexos que beneficiam de
  discussão estruturada

**Quando NÃO usar:**
- Pergunta curta/objetiva (sim/não, escolha simples)
- Humano já deu contexto suficiente anteriormente
- Devflow julga que apresentação direta é mais eficiente

**Boas práticas:**
- Sempre incluir a recomendação do agente junto com a
  pergunta
- Se múltiplas perguntas, avaliar se podem ser agrupadas
  antes de serializar
- Após cada resposta, repassar ao agente antes da próxima

**Exemplo:**

```
Agente retorna:
  "Q1: Índice na coluna status. Recomendo idx_pedido_status.
   Alternativa: índice composto (status, criado_em)."

Devflow apresenta ao humano:
  "O DBA precisa de uma decisão: índice simples na coluna
   status (recomendado, menos espaço) ou índice composto
   (status, criado_em, +30% espaço mas cobre ordenação).
   Qual prefere?"
```

### 3.2 prompt-improver — Melhoria de input do humano

**Quando usar:**
- Input do humano é ambíguo, vago ou pode ser
  interpretado de múltiplas formas
- Devflow detecta que melhor estruturação ajudaria o
  agente a trabalhar melhor
- Humano descreve requisito de forma conversacional e
  o agente se beneficiaria de um prompt mais estruturado

**Quando NÃO usar:**
- Input já é claro e objetivo
- Humano está com pressa e pede execução direta
- Ambiguidade é irrelevante para o resultado

**Boas práticas:**
- Sempre SUGERIR ao humano, nunca aplicar automaticamente
- Mostrar o que seria melhorado e por quê
- Se humano recusar, seguir normalmente sem insistir

**Exemplo:**

```
Humano diz: "quero uma tela de cadastro"

Devflow sugere:
  "Posso estruturar melhor esse pedido antes de passar ao
   front? Isso ajuda o agente a prototipar sem precisar
   perguntar de volta. Algo como: 'Tela de cadastro de
   cliente com campos nome, email, telefone. Validação
   de email único. Layout responsivo.' Quer que eu refine?"
```

## 4. Protocolo de Mediação (Fluido)

O agente **não precisa concluir a tarefa** antes de
perguntar:

```
1. Devflow spawna agente para uma fase (ex: planejamento)

2. Agente trabalha → encontra ponto de decisão que
   depende do humano

3. Agente salva progresso parcial no arquivo de
   planejamento e retorna ao Devflow com:
   - Resumo curto do progresso (≤5 linhas)
   - Seção `## Perguntas para o Humano — <agente>`
     com uma ou mais perguntas

4. Devflow avalia cada pergunta (checklist estrutural).
   Decide se usa grill-me com base no contexto:
   pergunta curta/objetiva → apresenta direto ao humano;
   elaborada/múltiplas/volumosa → usa grill-me para
   serializar uma por vez.

5. Se pergunta estiver confusa → Devflow orienta agente
   (re-spawn ou retoma sessão) com instrução específica
   do que melhorar.

6. Se pergunta estiver clara → Devflow apresenta ao
   humano (direto ou via grill-me, conforme passo 4),
   com recomendação do agente.

7. Humano responde → Devflow repassa resposta ao agente
   (re-spawn ou retoma sessão).

8. Agente continua trabalho com a resposta → pode gerar
   nova pergunta (volta ao passo 2).

9. Quando agente conclui a fase → retorna resumo curto
   final (≤5 linhas).
```

### 4.1 Formato da seção de perguntas

```markdown
## Perguntas para o Humano — dba

### Q1: Índice na coluna `status`
**Contexto:** A query mais frequente filtra por status.
  Sem índice, tabela com >1M linhas fará full scan.
**Recomendação:** Índice `idx_pedido_status`. Bloqueante
  para performance.
**Alternativas:** Índice composto `(status, criado_em)` —
  cobre ordenação por data, mas +30% espaço.

### Q2: Nome da tabela de auditoria
**Contexto:** Definir nome para tabela de log. Padrão do
  projeto é `audit_<entidade>`, módulo financeiro usa
  `_log`.
**Opções:**
  - `audit_pedido` — segue padrão do projeto
  - `pedido_log` — segue precedente do módulo financeiro
```

### 4.2 Checklist estrutural

Para cada pergunta, verificar:
- [ ] O que está sendo decidido está explícito?
- [ ] O contexto (por que isso importa) está presente?
- [ ] Se há opções, estão listadas com trade-offs?
- [ ] Se há recomendação, está justificada?
- [ ] A pergunta é autocontida?
- [ ] Se pede escolha, há exemplos concretos?

Itens ausentes → orientação de reformulação. Máximo 2
rodadas de reformulação; na terceira, apresenta ao humano
com nota: "Agente não conseguiu detalhar mais."

**Continuidade da mediação:** o Devflow nunca encerra a
mediação por conta própria — continua tentando ajustar
a comunicação enquanto o humano quiser prosseguir. Se o
humano não entender a pergunta mesmo após reformulações,
o Devflow oferece alternativas (reformulação manual,
pular com registro, etc.) mas só para quando o humano
decidir parar.

### 4.3 Serialização com grill-me

Quando devflow julgar necessário (complexidade, volume,
risco de sobrecarga cognitiva):
1. Avalia cada pergunta com o checklist
2. Agrupa as que passaram
3. Apresenta uma por vez com grill-me
4. Após cada resposta, repassa ao agente antes da próxima

## 5. Arquivos Afetados

### 5.1 `agents/devflow.md` — Refatoração principal

| Seção | Mudança |
|---|---|
| Frontmatter `description` | Adicionar "e mediador de comunicação humano-agente" |
| `## Função principal` | Parágrafo sobre mediação como segunda função |
| Novo: `## Função de Mediação` | Melhoria de Input, Mediação de Perguntas, Gestão de Carga |
| Novo: `## Protocolo de Mediação` | Checklist, formato de perguntas, fluxo fluido, cross-platform |
| `## Contrato com agentes spawnados` | Item 4: substituir "use grill-me" por "se tiver dúvidas que dependem de decisão do humano, salve progresso parcial no arquivo, formule as perguntas na seção `## Perguntas` e retorne com resumo curto + perguntas." |
| `## Contrato com agentes spawnados` | Novo item 6: "Não precisa concluir a tarefa inteira antes de perguntar. Salve progresso parcial, formule perguntas e retorne. A resposta será repassada para que você continue." |
| `## Governança` (linha 294) | Remover "Qualquer agente pode consultar humano diretamente". Adicionar: "Toda comunicação de agentes executores em modo orquestrado é mediada. Para agentes não mediados (ex: analista), devflow instrui humano a trocar de agente." |
| Novo: `## Agentes não mediados` | Quando devflow precisa de agente que conversa direto com humano (analista), instrui o humano a trocar de agente. Devflow não media esses agentes. |
| Tabelas de fluxo | Setas `agente → Humano` viram `agente → devflow → Humano` |

### 5.2 `docs/workflow-agentes-dev.md`

| Local | Mudança |
|---|---|
| Premissa 4 (linha 193) | Substituir: "Quando têm dúvidas que dependem de decisão, agentes formulam perguntas, salvam progresso parcial e retornam." |
| Novas: 4.1 a 4.4 | Mediação: checklist, grill-me serial, reformulação (máx 2), cross-platform |
| Premissa 11 (linha 245) | Remover grill-me direto; agentes retornam perguntas, Devflow media |
| Notas de implementação (linha 849) | Atualizar: só Devflow fala com humano. Subagentes não precisam de `ask` nem ser primários. |

### 5.3 `tests/agents/devflow-test.bats` — Novo

- Validação de checklist estrutural
- Detecção de múltiplas perguntas e serialização
- Formatação de orientação de reformulação
- Comportamento com pergunta única vs múltiplas

### 5.4 O que NÃO muda

- Prompts dos agentes executores — premissa 6 preservada
- `docs/workflow-definicao-escopo.md` — analista conversa
  direto com humano, sem mediação do devflow
- `agents/analista.md` — idem
- `docs/workflow-curadoria.md` — sem perguntas ao humano
- `skills/grill-me/SKILL.md` — skill já faz o necessário
- `skills/prompt-improver/SKILL.md` — regra de não
  auto-ativação mantida; Devflow decide sugerir

## 6. Impacto Cross-Platform

### Comunicação

| Antes | Depois |
|---|---|
| VS Code: subagentes precisam ser primários | Só Devflow (primário) fala com humano |
| OpenCode: subagentes precisam de tool `ask` | Subagentes não precisam de `ask` |
| Ambos: bombardeio de perguntas | Devflow serializa uma por vez |

### Preservação de sessão

| Plataforma | Pergunta → resposta |
|---|---|
| OpenCode | `task_id` — mesma sessão, contexto preservado |
| Copilot | Re-spawn — contexto via arquivo de planejamento |

O fallback (re-spawn) é natural: já é o mecanismo usado
entre fases (premissa 3). A diferença é só eficiência.

## 7. Riscos

| Risco | Mitigação |
|---|---|
| `task_id` não funciona como esperado | Re-spawn é fallback sempre disponível |
| Loop de reformulação | Máx 2 rodadas. Na 3ª, apresenta com nota |
| Agente gera muitas perguntas | Grill-me serializa. >5 alerta sobre escopo |
| Devflow acumula complexidade | Mediação é determinística — checklist + grill-me |

## 8. Plano de Implementação

> **Nota:** as tasks abaixo são atômicas e verificáveis.
> Cada task referencia o conteúdo exato a inserir,
> copiado das seções 3, 4 e 5 deste plano. Um agente
> executor pode seguir este plano sem interpretar —
> basta copiar e adaptar ao contexto do arquivo.

### Phase 1: `agents/devflow.md` — Mediação

#### Task 1: Atualizar frontmatter `description`

**Arquivo:** `agents/devflow.md`, linhas 2–13

**O que fazer:** adicionar "e mediador de comunicação
humano-agente" ao final da description, antes de
"Entrada: requisitos".

**Antes:**
```
  de harness. Entrada: requisitos
```

**Depois:**
```
  de harness. Mediador de comunicação humano-agente
  quando agentes retornam perguntas. Entrada: requisitos
```

**Critérios de aceitação:**
- [ ] description contém "mediador de comunicação"
- [ ] Nenhum outro campo do frontmatter alterado
- [ ] YAML válido (sem quebra de indentação)

---

#### Task 2: Adicionar parágrafo de mediação em
`## Função principal`

**Arquivo:** `agents/devflow.md`, após linha 51
(depois de "consulta o humano.")

**O que fazer:** inserir parágrafo abaixo da função
de roteador.

**Texto a inserir:**
```markdown
## Função de mediação

Além de rotear, você media a comunicação entre agentes
e humano. Quando um agente retorna com perguntas, você
avalia a qualidade estrutural, sugere melhorias no input
do humano quando detecta ambiguidade, e apresenta as
perguntas de forma organizada — diretamente ou via
skill `grill-me`, conforme a complexidade. Você nunca
responde perguntas no lugar do humano, nunca julga
conteúdo e nunca filtra por domínio.
```

**Critérios de aceitação:**
- [ ] Seção `## Função de mediação` existe após
      `## Função principal`
- [ ] Texto menciona: avaliar qualidade, sugerir melhorias,
      apresentar direto ou via grill-me
- [ ] Texto menciona: nunca responde, nunca julga conteúdo

---

#### Task 3: Atualizar contrato item 4
(substituir grill-me)

**Arquivo:** `agents/devflow.md`, linhas 103–108
(item 4 do contrato)

**O que fazer:** substituir o texto do item 4.

**Antes:**
```
4. **Nas fases de planejamento** (PLANEJAMENTO e
   REVISÃO DO PLANO), carregue a skill `grill-me` e
   valide cada decisão não-trivial com o humano antes
   de persistir no arquivo. Decisões triviais (nome
   de variável, formatação, ordem de passos sem
   impacto funcional) não precisam de validação.
```

**Depois:**
```
4. **Nas fases de planejamento** (PLANEJAMENTO e
   REVISÃO DO PLANO), valide cada decisão não-trivial
   com o humano antes de persistir no arquivo. Se tiver
   dúvidas que dependem de decisão, salve progresso
   parcial no arquivo de planejamento, formule as
   perguntas na seção `## Perguntas` e retorne com
   resumo curto + perguntas. Decisões triviais (nome
   de variável, formatação, ordem de passos sem
   impacto funcional) não precisam de validação.
```

**Critérios de aceitação:**
- [ ] Item 4 não menciona mais `grill-me`
- [ ] Item 4 instrui: salve progresso, formule perguntas
      na seção `## Perguntas`, retorne com resumo + perguntas
- [ ] Decisões triviais continuam isentas de validação

---

#### Task 4: Adicionar item 6 ao contrato

**Arquivo:** `agents/devflow.md`, após item 5 do
contrato (após linha 112)

**O que fazer:** inserir novo item 6.

**Texto a inserir:**
```
6. **Não precisa concluir a tarefa inteira antes de
   perguntar.** Se encontrar ponto de decisão durante
   a execução, salve progresso parcial no arquivo,
   formule as perguntas e retorne. A resposta será
   repassada para que você continue.
```

**Critérios de aceitação:**
- [ ] Item 6 existe no contrato
- [ ] Instrui: não precisa concluir tarefa antes de perguntar
- [ ] Instrui: salve progresso parcial antes de retornar
- [ ] Não menciona "Devflow" (agente não sabe do mediador)

---

#### Task 5: Atualizar seção Governança

**Arquivo:** `agents/devflow.md`, seção
`## Governança` (após linha 302)

**O que fazer:** substituir a linha "Qualquer agente
pode consultar o humano diretamente durante sua
execução." por novo texto.

**Antes:**
```
- **Qualquer agente pode consultar o humano** diretamente
  durante sua execução.
```

**Depois:**
```
- **Toda comunicação de agentes executores em modo
  orquestrado é mediada por você.** Agentes retornam
  perguntas; você avalia, reformula se necessário e
  apresenta ao humano.
- **Agentes não mediados** (ex: analista): quando
  precisar de agente que conversa direto com humano,
  instrua o humano a trocar de agente. Você não media
  esses agentes.
```

**Critérios de aceitação:**
- [ ] Linha "Qualquer agente pode consultar" removida
- [ ] Novo texto menciona: comunicação mediada por você
- [ ] Novo texto menciona: agentes não mediados → humano troca
- [ ] Não expõe agentes a saberem do Devflow (apenas governança
      interna do Devflow)

---

#### Task 6: Atualizar tabelas de fluxo

**Arquivo:** `agents/devflow.md`, seções de fluxo
por fase (linhas 178–300)

**O que fazer:** em todas as tabelas de fluxo onde
aparece "(usa grill-me)" na coluna Ação, substituir
por "(retorna perguntas se tiver dúvidas)".

**Exemplos de substituição:**
- `| 2.1 | eng-software | Planejar implementação (usa grill-me) |`
  → `| 2.1 | eng-software | Planejar implementação |`
- `| 2.2 | front | Prototipar telas (se houver UI; usa grill-me) |`
  → `| 2.2 | front | Prototipar telas (se houver UI) |`

**Critérios de aceitação:**
- [ ] Nenhuma tabela de fluxo menciona "grill-me"
- [ ] Agentes nas tabelas não têm instrução de mediação
      explícita (mediação é implícita no contrato de spawn)
- [ ] Estrutura das tabelas preservada

---

### Checkpoint: Phase 1

- [ ] `agents/devflow.md` tem seção "Função de mediação"
- [ ] Contrato item 4 não menciona grill-me
- [ ] Contrato tem item 6 (não precisa concluir antes de perguntar)
- [ ] Governança reflete mediação
- [ ] Tabelas de fluxo sem "grill-me"
- [ ] Em nenhum lugar do arquivo o agente executor é instruído
      a saber que existe um "Devflow" mediando — apenas
      instruções de comportamento

---

### Phase 2: `docs/workflow-agentes-dev.md` — Premissas

#### Task 7: Atualizar premissa 4

**Arquivo:** `docs/workflow-agentes-dev.md`, linha 192–193

**O que fazer:** substituir o texto da premissa 4.

**Antes:**
```
4. **Qualquer agente pode consultar o humano** a qualquer
   momento para esclarecer dúvidas da sua especialidade.
```

**Depois:**
```
4. **Quando têm dúvidas que dependem de decisão, agentes
   formulam perguntas, salvam progresso parcial e
   retornam.** O Devflow media a comunicação agente-humano
   em modo orquestrado (ver premissas 4.1 a 4.4).
```

**Critérios de aceitação:**
- [ ] Premissa 4 não diz "qualquer agente pode consultar
      o humano"
- [ ] Premissa 4 instrui: formule perguntas, salve progresso,
      retorne
- [ ] Referencia premissas 4.1 a 4.4

---

#### Task 8: Adicionar premissas 4.1 a 4.4

**Arquivo:** `docs/workflow-agentes-dev.md`, após premissa 4

**O que fazer:** inserir 4 sub-premissas detalhando
a mediação.

**Texto a inserir:**
```markdown
   4.1. **Checklist estrutural** — Devflow avalia cada
       pergunta com: o que está sendo decidido está
       explícito? Contexto presente? Opções com trade-offs?
       Recomendação justificada? Pergunta autocontida?
       Itens ausentes → orientação de reformulação. Máximo
       2 rodadas; na 3ª, apresenta ao humano com nota:
       "Agente não conseguiu detalhar mais."
   4.2. **Grill-me sob demanda** — Devflow decide se usa
       grill-me com base no contexto. Pergunta curta/objetiva
       → apresenta direto. Elaborada/múltiplas/volumosa →
       grill-me serializa uma por vez.
   4.3. **Continuidade da mediação** — Devflow nunca encerra
       a mediação por conta própria. Continua enquanto o
       humano quiser prosseguir. Se humano não entender
       após reformulações, oferece alternativas mas só para
       quando humano decidir parar.
   4.4. **Prompt-improver** — Devflow pode sugerir ao humano
       melhorar seu input antes de rotear ao agente. Sempre
       sugere, nunca aplica automaticamente. Se humano
       recusar, segue normalmente.
```

**Critérios de aceitação:**
- [ ] Premissas 4.1, 4.2, 4.3, 4.4 existem
- [ ] 4.1 menciona checklist e máximo 2 reformulações
- [ ] 4.2 menciona grill-me sob demanda (não obrigatório)
- [ ] 4.3 menciona continuidade (nunca encerra sozinho)
- [ ] 4.4 menciona prompt-improver como sugestão

---

#### Task 9: Atualizar premissa 11

**Arquivo:** `docs/workflow-agentes-dev.md`,
linha 252–261 (premissa 11)

**O que fazer:** remover menção a `grill-me` direto.
Agentes retornam perguntas, Devflow media.

**Antes (trecho relevante):**
```
11. **Planeje perguntando, execute com autonomia** — no
    planejamento, todo agente deve validar cada decisão
    não-trivial com o humano usando a skill `grill-me`.
```

**Depois:**
```
11. **Planeje perguntando, execute com autonomia** — no
    planejamento, todo agente deve validar cada decisão
    não-trivial com o humano, formulando perguntas e
    retornando para mediação do Devflow (ver premissa 4).
```

**Critérios de aceitação:**
- [ ] Premissa 11 não menciona mais `grill-me`
- [ ] Premissa 11 referencia premissa 4
- [ ] Resto da premissa 11 preservado (construção com
      autonomia, exceção do gate de refatoração)

---

#### Task 10: Atualizar notas de implementação

**Arquivo:** `docs/workflow-agentes-dev.md`,
linhas 852–865 (seção "Notas de Implementação")

**O que fazer:** substituir a tabela e texto para
refletir mediação centralizada.

**Antes (tabela):**
```
| Plataforma | Como `devflow` spawna agentes | Quem pode interagir com o humano |
|---|---|---|
| **Copilot CLI** | `task(agent_type=...)` ou `/fleet` | `devflow` medeia toda interação agente-humano |
| **OpenCode** | Subagentes | `devflow` medeia toda interação agente-humano |
```

**Depois:**
```
| Plataforma | Como `devflow` spawna agentes | Comunicação com humano |
|---|---|---|
| **Copilot CLI** | `task(agent_type=...)` ou `/fleet` | Devflow media. Subagentes retornam perguntas; não precisam ser primários. |
| **OpenCode** | Subagentes | Devflow media. Subagentes retornam perguntas; não precisam de tool `ask`. |
```

**Texto abaixo da tabela — substituir:**
```
**Copilot CLI**: subagentes são isolados do humano. Perguntas e decisões
retornam ao `devflow`, que as apresenta ao humano e retoma a sessão correta.

**OpenCode**: a mesma mediação é aplicada no modo orquestrado. A interação
direta fora desse modo continua disponível conforme a configuração do agente.
```

**Por:**
```
**Ambas as plataformas**: subagentes retornam perguntas ao invés de
consultar o humano diretamente. O `devflow` avalia, reformula se necessário
e apresenta ao humano. Subagentes não precisam de tool `ask` (OpenCode)
nem ser primários (Copilot CLI).

**Exceção**: agentes não mediados (ex: analista no workflow de definição
de escopo) conversam direto com o humano. O `devflow` instrui o humano
a trocar de agente quando necessário.
```

**Critérios de aceitação:**
- [ ] Tabela atualizada com coluna "Comunicação com humano"
- [ ] Texto menciona: subagentes retornam perguntas
- [ ] Texto menciona: não precisam de `ask` nem ser primários
- [ ] Texto menciona exceção: agentes não mediados (analista)

---

### Checkpoint: Phase 2

- [ ] Premissa 4 atualizada (formulam perguntas, salvam, retornam)
- [ ] Premissas 4.1–4.4 existem com checklist, grill-me,
      continuidade, prompt-improver
- [ ] Premissa 11 sem grill-me direto
- [ ] Notas de implementação refletem mediação centralizada
- [ ] `grep -i "grill-me" docs/workflow-agentes-dev.md` retorna 0
      resultados (ou apenas nas premissas 4.x como referência
      ao Devflow usando)

---

### Phase 3: Testes

#### Task 11: Criar `tests/agents/devflow-test.bats`

**Arquivo:** `tests/agents/devflow-test.bats` (novo)

**O que fazer:** criar arquivo de teste com 4 cenários
validando o conteúdo de `agents/devflow.md`.

**Cenários:**

1. **Checklist estrutural presente** — verificar que
   `agents/devflow.md` contém os itens do checklist
   (o que está sendo decidido, contexto, opções com
   trade-offs, recomendação, autocontida).

2. **Detecção de múltiplas perguntas** — verificar que
   `agents/devflow.md` contém instrução de serialização
   com grill-me sob demanda.

3. **Formatação de orientação de reformulação** — verificar
   que `agents/devflow.md` contém menção a máximo 2 rodadas
   de reformulação e nota na 3ª.

4. **Contrato sem grill-me** — verificar que o contrato
   com agentes spawnados NÃO menciona `grill-me`
   (agente não carrega a skill).

**Estrutura sugerida:**
```bash
#!/usr/bin/env bats

setup() {
    DEVFLOW="agents/devflow.md"
}

@test "devflow: checklist estrutural presente" {
    grep -q "o que está sendo decidido" "$DEVFLOW"
    grep -q "contexto" "$DEVFLOW"
    grep -q "trade-offs" "$DEVFLOW"
}

@test "devflow: serialização grill-me sob demanda" {
    grep -q "grill-me" "$DEVFLOW"
    grep -qi "sob demanda\|julgar necessário" "$DEVFLOW"
}

@test "devflow: máximo 2 reformulações" {
    grep -q "2 rodadas\|2 reformulações\|Máximo 2" "$DEVFLOW"
}

@test "devflow: contrato não menciona grill-me" {
    # O contrato com agentes spawnados não deve
    # instruir o agente a usar grill-me
    ! grep -A 20 "Contrato com agentes spawnados" "$DEVFLOW" \
        | grep -q "grill-me"
}
```

**Critérios de aceitação:**
- [ ] Arquivo existe em `tests/agents/devflow-test.bats`
- [ ] 4 testes definidos
- [ ] `make test-opencode` passa (todos os 4 testes green)
- [ ] Testes validam conteúdo do arquivo, não comportamento
      runtime

---

### Checkpoint: Phase 3

- [ ] `tests/agents/devflow-test.bats` existe
- [ ] 4 testes passam

---

### Phase 4: Verificação Final

Executar os comandos abaixo e confirmar que todos passam:

```bash
# 1. Nenhum agente executor menciona grill-me no contrato
! grep -A 20 "Contrato com agentes spawnados" agents/devflow.md | grep -q "grill-me"

# 2. Premissa 4 não diz "qualquer agente pode consultar"
! grep -q "Qualquer agente pode consultar" docs/workflow-agentes-dev.md

# 3. Premissa 11 não menciona grill-me direto
! grep -A 5 "Planeje perguntando" docs/workflow-agentes-dev.md | grep -q "grill-me"

# 4. Devflow tem seção de mediação
grep -q "Função de mediação\|Função de Mediação" agents/devflow.md

# 5. Contrato tem item 6
grep -q "^6\." agents/devflow.md

# 6. Governança não diz "Qualquer agente pode consultar"
! grep -A 10 "Governança" agents/devflow.md | grep -q "Qualquer agente pode consultar"

# 7. Analista não está no escopo de mediação
grep -q "analista" agents/devflow.md

# 8. Testes passam
make test-opencode
```

**Critérios finais:**
- [ ] Todos os 8 comandos acima passam
- [ ] Premissa 6 preservada: nenhum agente executor
      menciona fases, sequência ou workflow no prompt
- [ ] `agents/analista.md` inalterado
- [ ] `docs/workflow-definicao-escopo.md` inalterado
- [ ] `skills/grill-me/SKILL.md` inalterado
- [ ] `skills/prompt-improver/SKILL.md` inalterado
