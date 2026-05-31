# Redesign do Ecossistema de Curadoria do Produto

> Sessão de discovery assistido — andamento
> Data: 2026-05-29

---

## Decisão Central

O **Mapa do Produto** (template tabular fixo com 3 seções
obrigatórias) morre como artefato único. O conteúdo
sobrevive, mas distribuído em locais diferentes.

---

## Nova Estrutura de Artefatos

### `/doc/README.md` (novo local)

Contém 3 seções:

1. **Definição de Escopo**
   - O que o analista elicita (RFs, RNFs, critérios de
     aceitação — ou o que o humano definir)
   - Pode ser fornecido pelo humano antes do workflow
   - Pode ser gerado durante o workflow pelo analista
   - Fica no Arquivo de Planejamento durante o processo
   - É insumo para o workflow de desenvolvimento
   - **Morre** após transformação nos Elementos de
     Especificação (não sobrevive ao ciclo)

2. **Elementos de Especificação** (tabela)
   - Substitui a tabela do antigo Mapa do Produto
   - Colunas: `| Elemento | Formato/Ferramenta |
     Agente Responsável | Destino |`
   - **Todos os elementos são obrigatórios** — ou
     fornecidos pelo humano, ou criados durante o workflow
   - Outros agentes podem sugerir modificações em
     qualquer especificação
   - Fase de elaboração é o Planejamento — guardada
     durante Construção/Revisão (não precisa coluna)
   - Recomenda `/doc/` como padrão, respeita convenções
     existentes do projeto
   - Regras de Documentação ficam como subseções dentro
     do `/doc/README.md`, para cada elemento que o humano
     quiser detalhar

3. **Estratégias de Indexação de Código** (no final)
   - Técnicas para ajudar agentes IA a encontrar
     informação rapidamente e consumir menos tokens
   - Ferramentas padrão: codebase-memory + doctree
     (graphify sai da tabela sugerida)
   - Curador ou editor orientam o humano a instalar as
     ferramentas selecionadas

### `AGENTS.md` (topo do arquivo)

- **Harness por Agente** — tabela de comandos por agente
- **Link para `/doc/README.md`** — referência no início

---

## Elementos de Especificação — Tabela Sugerida

| Elemento | Formato/Ferramenta | Agente Responsável | Destino |
|---|---|---|---|
| Critérios de Aceite + Requisitos | Concordion | eng-software | docs/specs/ |
| Regras de Produto | Tabela | eng-software | nenhum |
| Modelo de Dados | DBML | dba | docs/modelo.dbml |
| Threat Model | Markdown | sec | docs/threat-model.md |
| Plano de Testes | Markdown | qa | nenhum |
| Identidade Visual | Protótipo HTML/SVG | front | plan/ui/ |
| ADR (Arquitetura) | Markdown | eng-software | docs/adr/ |

> Code as Doc / Graphify **removido** da tabela. Vai para
> a seção de Estratégias de Indexação de Código no final
> do `/doc/README.md`.

---

## Papéis dos Agentes

### `curador-produto` — Guardião (mantém nome)

- Verifica existência e aderência ao `/doc/README.md`
  (3 seções) + Harness no AGENTS.md
- **Não edita** nenhum dos dois — delega ao
  `curador-produto-editor`
- Atua em:
  - **Curadoria (início)** — verifica existência dos
    artefatos
  - **Revisão do Plano (dev)** — verifica aderência ao
    `/doc/README.md`
  - **Revisão da Construção (dev)** — verifica aderência
    ao `/doc/README.md`
  - **Finalização (dev)** — lista artefatos obrigatórios,
    verifica existência, reporta lacunas

O que verifica nas revisões do dev:
- **Elementos**: specs seguem formato/destino/agente da
  tabela de Elementos de Especificação?
- **Harness**: agente executou seu script? Evidência JSON
  no arquivo de planejamento?

> **Nota:** a Definição de Escopo NÃO é verificada pelo
> curador nas revisões do dev. Ela é usada pelo analista
> no workflow de Definição de Escopo (início) para
> orientar a elicitação.

### `curador-produto-editor` — Editor (renomeado de
`editor-mapa-produto`)

- **Único** que edita `/doc/README.md` e cria/mantém
  scripts de harness
- Pergunta ao humano o que deve ter, ajuda com perguntas,
  orienta e escreve o conteúdo
- Cria a seção Definição de Escopo no `/doc/README.md`
  (estrutura do que elicitar) antes do analista atuar
- **Padrão sugerido** para a seção:
  ```markdown
  ## Definição de Escopo
  O analista deve elicitar:
  - Requisitos funcionais e não funcionais
  - Critérios de aceitação por exemplos
  - Organizados por histórias de usuário
  - Critérios devem referenciar requisitos funcionais
  - Nenhum requisito pode ficar sem critério
  Skill recomendada: (opcional — humano define)
  ```
  O humano pode customizar. Editor entrevista para
  definir a estrutura, analista elicita o conteúdo.
- **Skill para o analista**: editor pergunta ao humano
  se quer que o analista use alguma skill específica
  (ex: `grill-me`, `spec-driven-development`). Se sim,
  registra na seção. Analista lê e usa.

### `analista` — Elicitador de Escopo (mantém nome,
mais flexível)

- Perde a obrigatoriedade do `BACKLOG.md` — pergunta ao
  humano como quer organizar
- Pode ser chamado na etapa de Planejamento se
  requisitos/critérios não foram fornecidos pré-workflow
- **Não edita** `/doc/README.md` — apenas lê a seção de
  Definição de Escopo para contextualizar
- Elicita com o humano, compara com o definido no readme
- Escrita: **somente** no Arquivo de Planejamento (ou
  onde o humano orientar)
- Subagente: apenas `revisor-historia`

### `val-harness` — Validador de Harness (mantém)

- Cruza evidências do arquivo de planejamento com o
  Harness definido no **AGENTS.md** (não mais no Mapa)

---

## Novo Workflow: Definição de Escopo (NÃO EXISTE HOJE)

Este workflow é **novo** — precisa ser criado. O `orq`
agora inicia por ele, que **substitui** a fase de
VALIDAÇÃO do workflow de dev.

O **Arquivo de Planejamento** é criado pelo `orq` no
início deste workflow (antes era criado no início do dev).

```
WORKFLOW DE DEFINIÇÃO DE ESCOPO (NOVO)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. orq → VALIDAÇÃO (transferida do dev)
   → spawna curador-produto
   → curador chama workflow de curadoria (autônomo)
   → verifica:
     a. /doc/README.md existe?
     b. Definição de Escopo preenchida?
     c. Harness existe no AGENTS.md?
   → se faltar → spawna curador-produto-editor
     → editor pergunta ao humano, ajuda, escreve
   → quando tudo OK → retorna para Definição de Escopo

2. orq → analista
   → analista lê /doc/README.md (seção Definição de
     Escopo) + o que o humano forneceu
   → compara: bate com o definido?
   → se faltar → elicita com humano
   → grava no Arquivo de Planejamento
   → quando OK → retorna para orq

3. orq → workflow de DESENVOLVIMENTO
   (começa em PLANEJAMENTO, sem VALIDAÇÃO)
```

### Regras críticas

- `workflow-curadoria` **nunca** chama `analista` —
  mantém autonomia
- `analista` **nunca** edita `/doc/README.md`
- `curador-produto-editor` cria a seção Definição de
  Escopo no readme **antes** do analista atuar
- `orq` é roteador stateless — só spawna, não lê, não
  valida

---

## Mudanças nos Workflows

### `docs/workflow-curadoria.md`

- Descrever novo `/doc/README.md` e `AGENTS.md`
- Garantir que workflow-curadoria é autônomo
- Garantir que workflow-curadoria NUNCA chama analista
- Renomear `editor-mapa-produto` →
  `curador-produto-editor`

### `docs/workflow-agentes-dev.md`

- Fase de VALIDAÇÃO transferida para o workflow de
  Definição de Escopo
- VALIDAÇÃO interna referencia workflow de curadoria
- Referências a "Mapa do Produto" → `/doc/README.md`
- Referências a "editor-mapa-produto" →
  `curador-produto-editor`
- Workflow começa em PLANEJAMENTO (VALIDAÇÃO movida)

---

## Arquivos a Modificar

1. **`/doc/README.md`** — Novo (criar template)
2. **`AGENTS.md`** — Atualizar (Harness + link)
3. **`docs/workflow-definicao-escopo.md`** — **CRIAR**
   (workflow novo, não existe hoje)
4. **`docs/workflow-curadoria.md`** — Revisar
5. **`docs/workflow-agentes-dev.md`** — Revisar
6. **`agents/curador-produto.md`** — Revisar
7. **`agents/analista.md`** — Revisar (mais flexível)
8. **`agents/editor-mapa-produto.md`** — RENAME para
   `agents/curador-produto-editor.md`
9. **`agents/references/mensagens-curadoria.md`** —
   Atualizar referências

---

## Decisões Consolidadas

| # | Decisão |
|---|---|
| 1 | Mapa do Produto morre como artefato único |
| 2 | `/doc/README.md` substitui (3 seções) |
| 3 | Harness vai para topo do AGENTS.md |
| 4 | `editor-mapa-produto` → `curador-produto-editor` |
| 5 | Colunas: Elemento, Formato, Agente, Destino |
| 6 | "Origem" removida da tabela |
| 7 | Todos os elementos são obrigatórios |
| 8 | Code as Doc sai da tabela |
| 9 | Estratégias de Indexação no final do readme |
| 10 | Analista mais flexível (sem BACKLOG.md obrigatório) |
| 11 | Novo workflow: Definição de Escopo |
| 12 | VALIDAÇÃO do dev movida para Definição de Escopo |
| 13 | Curadoria é workflow autônomo (não chama analista) |
| 14 | Analista nunca edita /doc/README.md |
| 15 | val-harness cruza com AGENTS.md (não Mapa) |

---

## Pendências da Entrevista

- [x] Formato da Definição de Escopo: **B — editor
  entrevista o humano** (customizado por projeto)
- [x] Padrão sugerido: RFs/RNFs + critérios por exemplos
  organizados por histórias de usuário
- [x] Workflow de Definição de Escopo: 2 fases
  (VALIDAÇÃO + ELICITAÇÃO) → transição para dev
- [x] Analista SEMPRE usa revisor-historia para revisar
- [x] Revisor-historia já é flexível, sem mudanças
- [ ] Mapear referências no workflow-agentes-dev.md
  (21 ocorrências — ver tabela abaixo)
- [ ] Gerar prompt final de handoff para implementação

---

## Mapeamento de Referências — workflow-agentes-dev.md

21 ocorrências de "Mapa do Produto" ou
"editor-mapa-produto" encontradas. Agrupadas por tipo:

### Tipo 1: "Mapa do Produto" → "/doc/README.md"

| Linha | Contexto |
|-------|----------|
| 34 | Especialidades: "Verifica aderência ao Mapa" |
| 40 | val-harness: "cruza com Mapa do Produto" |
| 53 | Contrato 1: "Mapa do Produto" (seção inteira) |
| 66 | Contrato 2: "Harness listado no Mapa" |
| 93 | Contrato 5: "Mapa define para cada elemento" |
| 263 | Arquivo: "Mapa para validação em lote" |
| 295 | Premissas: "Mapa do Produto" (subseção) |
| 297 | P21: "workflow exige Mapa" |
| 302 | P21: "aciona editor para criá-lo" |
| 327 | P21.2: "conforme Mapa" |
| 353 | P25: "conformidade com Mapa" |
| 356 | P25: "Não altera Mapa" |
| 420 | P32: "Harness definido no Mapa" |
| 430 | P33: "localiza Mapa no arquivo" |
| 451 | P35: "cruza com Mapa" |
| 575 | Diagrama: "Verifica aderência ao Mapa" |
| 676 | Diagrama: "Verifica aderência ao Mapa" |

### Tipo 2: "editor-mapa-produto" → "curador-produto-editor"

| Linha | Contexto |
|-------|----------|
| 34 | Especialidades: "delega ao editor-mapa-produto" |
| 299 | P21: "editor-mapa-produto conforme" |
| 358 | P25: "delega ao editor-mapa-produto" |
| 422 | P32: "editor-mapa-produto conforme" |
| 509 | Diagrama: "aciona editor-mapa-produto" |

### Tipo 3: VALIDAÇÃO removida (transferida)

| Linha | Contexto |
|-------|----------|
| 504-514 | Diagrama: bloco VALIDAÇÃO inteiro |

> **Nota:** a VALIDAÇÃO não é removida — é transferida
> para o workflow de Definição de Escopo. O diagrama do
> dev precisa referenciar esse workflow no início.
