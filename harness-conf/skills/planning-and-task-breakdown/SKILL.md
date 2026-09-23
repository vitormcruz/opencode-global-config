---
name: planning-and-task-breakdown
description: >
  Use quando tiver spec a quebrar em unidades implementáveis, task grande ou
  vaga para começar, trabalho a paralelizar entre agentes ou sessões, ou
  ordem de implementação pouco óbvia. Decompõe o trabalho em tasks pequenas
  e verificáveis, com critérios de aceitação explícitos e grafo de
  dependências. Triggers: "planning", "task breakdown", "decompose work",
  "scope estimation", "task list", "sprint planning", "backlog",
  "acceptance criteria", "epic", "user story", "order tasks",
  "task dependencies", "parallel work", "sequencing", "prioritize",
  "what to build next", "break this down", "implementation plan".
---

# Planning and Task Breakdown

Decomponha trabalho em tasks pequenas e verificáveis, com critérios de
aceitação explícitos e grafo de dependências. Task pequena é o que separa
um agente que entrega de um que enrola: cada task deve ser implementável,
testável e verificável em uma sessão focada.

Quando não usar: mudança de arquivo único com escopo óbvio, ou spec que
já traz tasks bem definidas.

## Processo de planejamento

**1. Modo planejamento (read-only).** Antes de escrever código, leia a
spec e as partes relevantes do codebase, identifique padrões e
convenções existentes, mapeie dependências e anote riscos e incógnitas.
Não escreva código no planejamento; o output é o plano.

**2. Grafo de dependências.** Mapeie o que depende do quê:

```
schema de banco
    ├── models/types da API
    │       ├── endpoints
    │       │       └── client da API no frontend
    │       └── validação
    └── seeds / migrations
```

A ordem de implementação segue o grafo, de baixo para cima: fundação
primeiro.

**3. Fatie verticalmente.** Cada slice entrega um caminho completo e
funcional, não uma camada inteira:

```
# Ruim (horizontal):
Task 1: todo o schema do banco
Task 2: todos os endpoints
Task 3: toda a UI
Task 4: conectar tudo

# Bom (vertical):
Task 1: usuário cria conta (schema + API + UI de registro)
Task 2: usuário faz login (auth + API + UI de login)
Task 3: usuário cria task (schema + API + UI de criação)
Task 4: usuário vê a lista (query + API + UI de listagem)
```

Cada fatia vertical é funcional e testável por si só.

**4. Escreva as tasks.** Estrutura por task:

```markdown
## Task [N]: [Título curto e descritivo]

**Description:** um parágrafo com o que a task entrega.

**Acceptance criteria:**
- [ ] [Condição específica e testável]

**Verification:**
- [ ] Testes: `npm test -- --grep "feature-name"`
- [ ] Build: `npm run build`
- [ ] Manual: [o que verificar]

**Dependencies:** [tasks de que depende, ou "None"]

**Files likely touched:**
- `src/path/to/file.ts`

**Estimated scope:** [S: 1-2 arquivos | M: 3-5 | L: 5+]
```

**5. Ordene e marque checkpoints.** Dependências satisfeitas, sistema
em estado funcional após cada task, risco alto no começo (fail fast) e
checkpoint explícito a cada 2-3 tasks:

```markdown
## Checkpoint: after Tasks 1-3
- [ ] All tests pass, build clean
- [ ] Core user flow works end-to-end
- [ ] Review with human before proceeding
```

## Dimensionamento

| Tamanho | Arquivos | Escopo | Exemplo |
|---|---|---|---|
| **XS** | 1 | função ou config | nova regra de validação |
| **S** | 1-2 | componente ou endpoint | novo endpoint de API |
| **M** | 3-5 | uma fatia de feature | fluxo de registro |
| **L** | 5-8 | feature multi-componente | busca com filtros e paginação |
| **XL** | 8+ | muito grande, dividir | — |

Agente performa melhor em S e M. Quebre mais uma task se: não cabe em
uma sessão focada (~2h de trabalho de agente); os critérios de aceitação
não cabem em 3 bullets; toca 2+ subsistemas independentes (auth e
billing); o título tem "and" (são duas tasks).

## Template de plano

```markdown
# Implementation Plan: [Feature]

## Overview
[Um parágrafo do que será construído]

## Architecture Decisions
- [Decisão-chave + rationale]

## Task List
### Phase 1: Foundation
- [ ] Task 1: ...
### Checkpoint: Foundation
- [ ] Tests pass, build clean

### Phase 2: Core Features
- [ ] Task 2: ...
### Checkpoint: Core
- [ ] End-to-end flow works

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|

## Open Questions
- [Questão que precisa do humano]
```

## Paralelização

- **Paralelizável:** fatias independentes, testes de feature já
  implementada, documentação.
- **Sequencial:** migrations, mudança de estado compartilhado, cadeia de
  dependências.
- **Coordenado:** features que dividem contrato de API (defina o
  contrato primeiro, depois paralelize).

## Separação plano ↔ artefato

O plano é artefato de trabalho temporário. TODO artefato de produção
gerado na execução (código, docs, prompts, testes, configuração) deve
ser AUTOCONTIDO: jamais citar códigos de decisão (D1, D2...), números de
task, seções ou vocabulário interno do plano. Conteúdo que só faz
sentido com o plano na mão deve ser reescrito em linguagem autocontida.

## Anti-racionalizações

| Racionalização | Realidade |
|---|---|
| "Vou resolvendo no caminho" | É assim que vira nó cego e retrabalho; 10 minutos de plano economizam horas. |
| "As tasks são óbvias" | Escreva assim mesmo: tasks explícitas expõem dependência escondida e edge case esquecido. |
| "Planejar é overhead" | Planejamento é a task; implementar sem plano é só digitar. |
| "Consigo segurar na cabeça" | Janela de contexto acaba; plano escrito sobrevive a troca de sessão e compaction. |

## Red flags

Implementação começada sem lista de tasks escrita; task "implemente a
feature" sem critério de aceitação; plano sem passo de verificação; todas
as tasks XL; sem checkpoint entre fases; ordem ignorando dependências.

## Verificação (antes de implementar)

- [ ] Toda task tem critérios de aceitação e passo de verificação
- [ ] Dependências identificadas e ordenadas
- [ ] Nenhuma task toca mais de ~5 arquivos
- [ ] Checkpoints entre fases grandes
- [ ] Humano revisou e aprovou o plano
- [ ] Nenhum artefato de produção cita identificadores do plano
