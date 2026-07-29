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
| **prompt-improver** | Input do humano com ambiguidade detectável | Proativo — sugere melhoria sem esperar pedido |
| **grill-me** | Agente retorna pergunta(s) ao humano | Mediação — uma pergunta por vez, com recomendação |

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
   Se múltiplas, serializa — uma por vez com grill-me.

5. Se pergunta estiver confusa → Devflow orienta agente
   (re-spawn ou retoma sessão) com instrução específica
   do que melhorar.

6. Se pergunta estiver clara → Devflow apresenta ao
   humano (grill-me), com recomendação do agente.

7. Humano responde → Devflow repassa resposta ao agente
   (re-spawn ou retoma sessão).

8. Agente continua trabalho com a resposta → pode gerar
   nova pergunta (volta ao passo 2).

9. Quando agente conclui a fase → retorna resumo curto
   final (≤5 linhas).
```

### 4.1 Preservação de contexto entre perguntas

| Plataforma | Mecanismo | Efeito |
|---|---|---|
| **OpenCode** | `task_id` — retoma mesma sessão de subagente | Contexto preservado, sem re-indexação |
| **Copilot/VS Code** | Re-spawn com contexto via prompt + arquivo de planejamento | Agente novo lê o arquivo e continua |

O Devflow prefere `task_id` quando disponível e usa
re-spawn como fallback. Ambos funcionam — a diferença é
eficiência de tokens. A premissa 3 (instância nova a cada
fase) se mantém; o que estamos flexibilizando é a
continuidade **dentro da mesma fase**.

### 4.2 Formato da seção de perguntas

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

### 4.3 Checklist estrutural

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

### 4.4 Serialização com grill-me

Se o agente retorna múltiplas perguntas de uma vez:
1. Devflow avalia cada uma com o checklist
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
| `## Contrato com agentes spawnados` | Item 4: substituir "use grill-me" por "retorne perguntas ao Devflow. Salve progresso antes de perguntar." |
| `## Contrato com agentes spawnados` | Novo item 6: "Não conclua tarefa para perguntar. Salve progresso parcial, formule pergunta, retorne. Devflow repassa resposta." |
| `## Governança` (linha 294) | Remover "Qualquer agente pode consultar humano diretamente". Adicionar: "Toda comunicação agente→humano em modo orquestrado passa pelo Devflow." |
| Tabelas de fluxo | Setas `agente → Humano` viram `agente → devflow → Humano` |

### 5.2 `docs/workflow-agentes-dev.md`

| Local | Mudança |
|---|---|
| Premissa 4 (linha 193) | Substituir: "Agentes não consultam humano diretamente. Formulam perguntas ao Devflow." |
| Novas: 4.1 a 4.4 | Mediação: checklist, grill-me serial, reformulação (máx 2), cross-platform |
| Premissa 11 (linha 245) | Remover grill-me direto; agentes retornam perguntas, Devflow media |
| Notas de implementação (linha 849) | Atualizar: só Devflow fala com humano. Subagentes não precisam de `ask` nem ser primários. |

### 5.3 `docs/workflow-definicao-escopo.md`

| Local | Mudança |
|---|---|
| Diagrama (linha 87-112) | `analista → Humano` vira `analista → devflow → Humano` |
| Fluxo textual (linha 50-58) | Analista retorna perguntas; Devflow avalia e media |

### 5.4 `tests/agents/devflow-test.bats` — Novo

- Validação de checklist estrutural
- Detecção de múltiplas perguntas e serialização
- Formatação de orientação de reformulação
- Comportamento com pergunta única vs múltiplas

### 5.5 O que NÃO muda

- Prompts dos agentes executores — premissa 6 preservada
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
