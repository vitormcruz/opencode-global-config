# Plano: Refatoração do Curador, Mapa do Produto e Harness

Status: RASCUNHO — aguardando revisão do humano

## Objetivo

Reestruturar o papel do `curador-produto`, o formato
do Mapa do Produto e a mecânica de harness. Mudanças
principais:

1. Curador **não valida mais requisitos** — foca
   exclusivamente no Mapa do Produto (especificações,
   documentação, harness)
2. Requisitos passam a ser responsabilidade do
   `eng-software` e demais agentes no planejamento
3. Mapa do Produto ganha **template default** com
   formato fechado (anti-alucinação)
4. Harness vira **um script único por agente** com
   interface padronizada e linguagem livre
5. Novo agente `editor-mapa-produto` dedicado a **entender
   o projeto** e ajudar a criar o Mapa inicial

---

## Etapa 1 — Template Default do Mapa do Produto

### Definição

O Mapa do Produto é composto por três seções
obrigatórias. O formato tabular fechado reduz
alucinação — o agente preenche campos, não inventa
estrutura. Qualquer agente pode criar, consultar ou
sugerir mudanças em qualquer elemento — não há dono
fixo.

#### 1A. Elementos de Especificação

```markdown
## Mapa do Produto

### Elementos de Especificação

| Elemento                          | Formato/Ferramenta | Origem                      | Destino              |
|-----------------------------------|--------------------|-----------------------------|----------------------|
| Critérios de Aceite + Requisitos  | Concordion         | História de Usuário em MD   | specs/               |
| Regras de Produto                 | Tabela (ver §1.1)  | arquivo de planej.          | nenhum               |
| Modelo de Dados                   | DBML               | arquivo de planej.          | docs/modelo.dbml     |
| Threat Model                      | Markdown           | arquivo de planej.          | docs/threat-model.md |
| Plano de Testes                   | Markdown           | arquivo de planej.          | nenhum               |
| Identidade Visual                 | Protótipo HTML/SVG | plan/ui/                    | nenhum               |
| Code as Doc                       | Graphify           | graphify-out/               | graphify-out/        |
```

**Coluna "Destino":**
- Caminho = artefato extraído para local definitivo
  antes de descartar o arquivo de planejamento
- `nenhum` = descartado ao final do ciclo junto com
  o arquivo de planejamento

**Regra:** o humano pode adicionar, remover ou alterar
linhas. O template acima é o **default** — ponto de
partida, não prescrição.

#### 1B. Regras de Documentação

Subseções opcionais — só existem para elementos que
o humano quis detalhar. Elementos sem regras
específicas não precisam de subseção.

O `editor-mapa-produto` deve informar ao humano que esta
seção existe, explicar o propósito e ajudar a preencher
as regras que o humano considerar necessárias.

```markdown
### Regras de Documentação

#### Critérios de Aceite + Requisitos

Os critérios de aceite devem estar organizados por
Funcionalidade levando-se em conta a coesão. Cada
funcionalidade deve ter um arquivo Concordion separado.
Os requisitos associados aos critérios de aceitação
devem estar no mesmo arquivo, e os critérios devem
referenciar os requisitos que estão sendo atendidos.

(demais elementos: só criar subseção se houver regra
específica a registrar)
```

#### 1C. Harness por Agente

```markdown
### Harness por Agente

| Agente         | Comando de Execução            | Descrição                                |
|----------------|--------------------------------|------------------------------------------|
| eng-software   | harness/eng-software.sh        | Testes, análise estática, regressão      |
| dba            | harness/dba.sh                 | Validação de schema, migrações           |
| sec            | harness/sec.sh                 | OWASP checks, secrets scan               |
| qa             | harness/qa.sh                  | Cobertura, testes de aceitação           |
| front          | harness/front.sh               | Linting, a11y, aderência visual          |
| rev            | (sem harness)                  | SEM HARNESS A PEDIDO DO HUMANO           |
| val-harness    | (sem harness)                  | SEM HARNESS A PEDIDO DO HUMANO           |
| curador-produto| (sem harness)                  | SEM HARNESS A PEDIDO DO HUMANO           |
```

### Arquivos afetados

| Arquivo | O que muda |
|---------|------------|
| `docs/workflow-curadoria.md` | Adicionar template default (§1A-C); alterar premissa 2: "livre" → "template default, customizável" |
| `agents/editor-mapa-produto.md` | **(novo)** — embutir template como referência |

---

## Etapa 2 — Interface Padronizada de Harness

### Definição

- **Chamada**: comando livre registrado no Mapa
  (bash, python, node, qualquer coisa)
- **Sem argumentos** — paths de diretórios, configs e
  ferramentas ficam definidos internamente no script
- **Saída stdout**: JSON com schema fixo
- **Exit code**: 0 = pass, 1 = fail

```json
{
  "status": "pass | fail",
  "findings": [
    {
      "severity": "bloqueante | melhoria",
      "tool": "eslint | ruff | manual | ...",
      "message": "descrição do problema"
    }
  ],
  "prompt": "instrução adicional para o agente (opcional, só quando pass)"
}
```

**Comportamento do agente:**
1. Ao final da execução (construção ou revisão),
   roda o comando do Mapa
2. `fail` → lê `findings`, tenta resolver, roda
   harness novamente
3. `pass` → lê `prompt`, executa se houver
4. Persiste saída JSON na seção
   `## Evidências de Harness` do arquivo de planejamento
5. Script único por agente, sem parâmetro de fase
   — idempotente

**O script sempre existe.** O `editor-mapa-produto` cria
um script para **todos** os agentes ao montar o Mapa.
Se o humano não definiu ferramentas ou regras para um
agente, o script retorna `{ "status": "pass" }` sem
verificações (pass-through). Assim o agente **sempre
chama** o script sem se preocupar se há algo
configurado ou não — a lógica fica no script, não no
agente.

**Portabilidade:** linguagem livre por projeto;
contrato é a interface (argumento + JSON + exit code).

### Arquivos afetados

| Arquivo | O que muda |
|---------|------------|
| `docs/workflow-curadoria.md` | Substituir convenção de scripts por interface padronizada |
| `docs/workflow-agentes-dev.md` | Premissas P32-36: atualizar para script único, sem fase |
| `skills/harness-catalog/SKILL.md` | Atualizar para refletir script único |

---

## Etapa 3 — Novo Agente: `editor-mapa-produto`

### Definição

Agente dedicado a entender o projeto e ajudar a criar
o Mapa do Produto para projetos que ainda não têm.

**Capacidades:**
- Analisar estrutura do repositório (dirs, linguagens,
  frameworks)
- Identificar padrões de documentação existentes
- Identificar ferramentas de build/test/lint
- Propor template do Mapa preenchido
- Propor harness inicial baseado nas ferramentas
- Gerar scaffold inicial dos scripts de harness
  baseado nas ferramentas encontradas

**Fluxo obrigatório — seção por seção com aprovação:**

O agente **não pode** montar o Mapa inteiro sozinho e
apresentar como pronto. Deve seguir este ciclo:

1. **Sugere indexação do código** — se não houver
   grafo de conhecimento (ex.: `graphify-out/`),
   sugere ao humano instalar e rodar uma ferramenta
   de indexação (ex.: Graphify) como primeiro passo.
   Isso reduz consumo de tokens e dá visibilidade.
2. Analisa o projeto (estrutura, ferramentas, docs)
3. Apresenta ao humano o que encontrou (resumo)
4. **Seção 1A (Elementos de Spec):** propõe tabela
   inicial → humano aprova/ajusta
5. **Seção 1B (Regras de Documentação):** para cada
   elemento aprovado em 1A, pergunta se o humano quer
   registrar regras específicas → humano decide
6. **Seção 1C (Harness):** primeiro pergunta ao humano
   em qual linguagem/tecnologia criar os scripts
   (bash, python, node, etc.). Depois, para cada
   agente, pergunta objetivamente: "quais ferramentas
   e/ou prompts devem compor o harness deste agente?".
   Não divagar — pergunta direta, resposta direta.
   Se o humano não quiser harness para um agente,
   registra `SEM HARNESS A PEDIDO DO HUMANO`.
7. **Cria os scripts** — para todos os agentes,
   inclusive os sem regras (pass-through). O humano
   não precisa aprovar cada script individualmente;
   o analista gera e pronto.
8. Só declara Mapa concluído após aprovação explícita
   do humano em cada seção (1A, 1B, 1C)

**Regra anti-autonomia:** o agente deve parar e
perguntar ao humano após cada seção. Nunca avançar
para a próxima seção sem aprovação da anterior. Se
o humano quiser pular uma seção, registrar como
`(não definido)` e seguir.

**Quando usar:**
- Curador detecta ausência de Mapa → para o fluxo →
  pede ao humano usar `editor-mapa-produto`
- O humano roda, aprova o Mapa, volta ao fluxo dev

**Limites:**
- Não executa código de produção
- Não cria requisitos — apenas entende o projeto
- Propõe, não decide — o humano aprova

### Arquivos afetados

| Arquivo | O que muda |
|---------|------------|
| `agents/editor-mapa-produto.md` | **(novo)** — prompt do agente |

---

## Etapa 4 — Refatorar `curador-produto`

### Definição

Remover validação de requisitos, focar exclusivamente
no Mapa do Produto.

**Remover:**
- Capacidade 1: "Validar requisitos antes de iniciar
  um desenvolvimento"
- Toda menção a "validar entrada/requisitos"
- Trecho "verifica se a entrada (requisitos, histórias,
  pedidos) é consistente com a documentação existente"

**Alterar:**
- Capacidade principal: guardião do Mapa do Produto
  (especificações, documentação, harness)
- Na validação: verifica existência do Mapa; se ausente,
  para o fluxo e pede `editor-mapa-produto`
- Na revisão: verifica aderência ao Mapa (elementos
  de spec preenchidos), não valida requisitos
- Limites: adicionar "Não valida requisitos — valida
  aderência ao Mapa"

**Manter:**
- Guardião do Mapa (criar, atualizar, sincronizar)
- Co-confecção de harness com especialistas
- Revisão de documentação nos loops
- Finalização (verificar artefatos com Destino)
- Exclusão do plano ao final

### Arquivos afetados

| Arquivo | O que muda |
|---------|------------|
| `agents/curador-produto.md` | Refatorar conforme acima |

---

## Etapa 5 — Atualizar Workflow Dev

### Definição

Ajustar fases, premissas e diagrama do workflow de
desenvolvimento.

**Fase 1 — VALIDAÇÃO:**
- Curador valida apenas existência/completude do Mapa
- Se Mapa não existe: para o fluxo, pede
  `editor-mapa-produto`
- Se incompleto: curador ajuda a completar
- Não valida requisitos

**Fase 2 — PLANEJAMENTO:**
- Se requisitos não fornecidos, `eng-software`
  pergunta ao humano
- Todos os agentes consultam o Mapa para saber quais
  elementos de spec preencher
- Especificação desenvolvida incrementalmente

**Fase 3 — REVISÃO DO PLANO:**
- Curador verifica apenas aderência ao Mapa (elementos
  de spec preenchidos)
- Não opina sobre requisitos

**Fases 4-6 — Sem mudança conceitual:**
- Harness usa nova interface (Etapa 2)

**Fase 7 — FINALIZAÇÃO:**
- Curador lê coluna "Destino" do Mapa:
  - Caminho definido → verifica existência no local
  - `nenhum` → ignora (descartado com o plano)

**Premissas a alterar:**

| Premissa | Mudança |
|----------|---------|
| P21 | Remover menção a curador validando requisitos |
| P21.2 | Manter (especificação evolutiva — agora mais relevante) |
| P25 | Reformular: "curador valida aderência ao Mapa, não requisitos" |
| P32-36 | Já coberto pela Etapa 2 |
| Diagrama | Atualizar fase VALIDAÇÃO |

### Arquivos afetados

| Arquivo | O que muda |
|---------|------------|
| `docs/workflow-agentes-dev.md` | Fases 1/2/3/7, premissas P21/P25, diagrama Mermaid |

---

## Etapa 6 — Atualizar Workflow Curadoria

### Definição

Alinhar o workflow de curadoria com as mudanças das
etapas anteriores.

**Adicionar:**
- Template default do Mapa (da Etapa 1)
- Interface padronizada de harness (da Etapa 2)
- Referência ao `editor-mapa-produto` como pré-requisito

**Alterar:**
- Curador não executa curadoria inline na validação —
  para e pede `editor-mapa-produto`
- Premissa 2: "livre" → "template default, customizável"
- Convenção de scripts: script único por agente

**Remover:**
- Referências a validação de requisitos pelo curador

### Arquivos afetados

| Arquivo | O que muda |
|---------|------------|
| `docs/workflow-curadoria.md` | Conforme acima (acumula mudanças das Etapas 1 e 2) |

---

## Etapa 7 — Atualizar Agentes Dependentes

### Definição

Propagar mudanças para agentes que referenciam o
comportamento antigo do curador.

**`orq.md`:** atualizar referência à fase de validação
(curador verifica Mapa, não requisitos)

**`eng-software.md`:** adicionar responsabilidade de
levantar requisitos se ausentes na entrada

### Arquivos afetados

| Arquivo | O que muda |
|---------|------------|
| `agents/orq.md` | Referência à validação |
| `agents/eng-software.md` | Responsabilidade de requisitos |

---

## Etapa 8 — Sincronizar Regras Globais

### Definição

`AGENTS.md` e `.github/copilot-instructions.md` devem
refletir as mudanças se referenciam curador como
validador de requisitos.

### Arquivos afetados

| Arquivo | O que muda |
|---------|------------|
| `AGENTS.md` | Remover referência (se existir) |
| `.github/copilot-instructions.md` | Idem |

---

## Etapa 9 — Testes

### Definição

Criar ou atualizar testes para as mudanças.

- Testes do `editor-mapa-produto` (novo agente)
- Verificar que testes existentes não referenciam
  curador como validador de requisitos

### Arquivos afetados

| Arquivo | O que muda |
|---------|------------|
| `tests/agents/` | Novos testes para `editor-mapa-produto` |
| Testes existentes | Verificar/ajustar referências |

---

## Decisões Resolvidas

- [x] Nome do agente: `editor-mapa-produto`
- [x] Argumento do harness: sem argumentos — paths
  e configs definidos internamente no script
- [x] Indexação do código: `editor-mapa-produto` sugere
  ferramenta de indexação (ex.: Graphify) como
  primeiro passo, para reduzir tokens e dar
  visibilidade ao humano e aos agentes

---

## Ordem de Execução

```
Etapa 1 (Template Mapa) ──┐
Etapa 2 (Interface Harness)┤
Etapa 3 (Novo Agente)     ─┤── podem ser paralelas
                            │
Etapa 4 (Curador)     ─────┤── depende de 1-3
Etapa 5 (Workflow Dev) ────┤── depende de 1-2-4
Etapa 6 (Workflow Curadoria)── depende de 1-2-4
Etapa 7 (Agentes Depend.) ─── depende de 4-5
Etapa 8 (Regras Globais) ──── depende de 4
Etapa 9 (Testes) ──────────── depende de tudo
```
