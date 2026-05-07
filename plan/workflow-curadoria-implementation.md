# Plano — Separação do Workflow de Curadoria

Status: EM DISCUSSÃO COM O HUMANO

---

## 1. Resumo

Separar o fluxo de Mapa do Produto + Harness do workflow de
desenvolvimento em um processo independente (`workflow-curadoria`),
liderado pelo `curador-produto` (sem `orq`). O workflow de dev
(`workflow-agentes-dev`) continua funcionando como hoje — o curador
detecta ausência de Mapa/Harness na fase de VALIDAÇÃO e executa o
fluxo de curadoria inline antes de devolver controle ao `orq`.

---

## 2. Decisões consolidadas

| # | Decisão | Resolução |
|---|---------|-----------|
| D1 | Orquestração do fluxo de curadoria | Curador orquestra sozinho, sem `orq` |
| D2 | Onde fica o catálogo de harness | No curador (referência de domínio, não conhecimento de workflow) |
| D3 | P6 e o curador | O curador NÃO conhece nenhum workflow. O processo de curadoria é capacidade interna dele (como TDD é do eng) |
| D4 | Nomes | `workflow-curadoria` (novo) + `workflow-agentes-dev` (renomeado) |
| D5 | Pré-condição formal no dev? | Não. Curador detecta ausência e aciona curadoria inline |
| D6 | Referências entre workflows | Unidirecional: dev → curadoria (onde buscar). Curadoria não referencia dev |
| D7 | Script de instalação de harness | Por projeto, dentro de `harness/`. Se não existir, curador ajuda a criar |
| D8 | Permissão bash do curador | `bash: allow` com restrição no corpo do prompt (opção B) |
| D9 | Curador spawna especialistas? | Sim, diretamente. Precisa de `task` permissions no frontmatter |
| D10 | Planos de orq/sec precisam atualizar? | Não — P33-P35 (runtime) ficam no workflow de dev |

---

## 3. Etapas de implementação

### Fase A — Criar o documento de design (`workflow-curadoria`)

**Arquivo:** `docs/workflow-curadoria.md`

**Conteúdo a incluir (movido do workflow atual + novo):**

1. Objetivo e escopo do fluxo de curadoria
2. Premissas de Mapa do Produto (atuais P21-P24 — movidas
   integralmente)
3. Premissas de definição/criação de Harness (parte de P32 —
   tudo que trata de como criar/definir harness)
   - NÃO mover P33-P35 (runtime — ficam no workflow de dev)
4. Convenção recomendada de scripts (`harness/<agente>/<fase>.sh`)
   — mover integralmente da seção atual (linha ~371 do workflow)
5. Catálogo de sugestões de harness por agente (~150 linhas) —
   mover integralmente
6. Fases do processo de curadoria:
   - DIAGNÓSTICO → analisa repo, identifica lacunas
   - MAPA → propõe Mapa → humano aprova
   - HARNESS → coordena com especialistas, humano aprova cada
   - INSTALAÇÃO → cria/atualiza script, humano executa `sudo`
   - VALIDAÇÃO → verifica que tudo funciona
7. Diagrama mermaid do fluxo de curadoria
8. Nota: o curador é o agente que implementa este processo
   como capacidade interna (sem conhecer fases de outros
   workflows)

**Referências a usar como modelo:** estrutura do
`workflow-agentes.md` atual (premissas numeradas,
tabelas, diagrama mermaid)

**Dependências:** nenhuma — é aditivo

---

### Fase B — Atualizar o agente `curador-produto`

**Arquivo:** `agents/curador-produto.md`

**Mudanças no frontmatter:**

```yaml
# DE:
permission:
  bash: deny
  task:
    "*": deny

# PARA:
permission:
  bash: allow
  task:
    eng-software: allow
    dba: allow
    sec: allow
    qa: allow
    "*": deny
```

**Mudanças no corpo:**

1. **Restrição de bash** — adicionar no Contrato Operacional:
   "Só execute scripts dentro de `harness/`, `scripts/` ou
   comandos de instalação de dependências de harness.
   Não execute comandos arbitrários."

2. **Reestruturar capacidade 8** (co-confecção de harness) para
   incluir o processo completo de curadoria como capacidade
   interna. Não mencionar fases de workflow — descrever como
   capacidade:
   - Diagnosticar ausência de Mapa/Harness
   - Criar/atualizar Mapa do Produto
   - Coordenar criação de Harness com especialistas
     (spawnar agentes para consultar sobre regras do domínio)
   - Criar/atualizar script de instalação em `harness/`
   - Validar que scripts funcionam

3. **Mover catálogo de sugestões de harness** para dentro do
   agente como referência de domínio (seção de referência).
   O curador usa isso para orientar o humano, não como regra
   obrigatória. Isso é conhecimento de domínio, não
   conhecimento de workflow.

4. **Adicionar capacidade de spawnar especialistas** —
   documentar que pode chamar eng-software, dba, sec, qa
   para consultar sobre regras de harness do domínio deles.

**Dependências:** Fase A (para que o workflow de curadoria
exista como referência de design, mesmo que o agente não o
leia diretamente)

---

### Fase C — Reduzir o workflow de dev

**Arquivo:** `docs/workflow-agentes.md` (antes da renomeação)

**O que reduzir:**

1. **P21-P24 (Mapa do Produto)** → substituir por 1 premissa:
   > "O workflow exige um Mapa do Produto. A definição,
   > criação e manutenção do Mapa são responsabilidade do
   > `curador-produto` conforme descrito em
   > `workflow-curadoria.md`. O `curador-produto` detecta
   > ausência do Mapa na fase de VALIDAÇÃO e aciona o
   > processo de curadoria inline antes de devolver
   > controle ao `orq`."

2. **P32 (definição de harness)** → reduzir a:
   > "Harness é definido no Mapa do Produto. A criação e
   > manutenção do harness são responsabilidade do
   > `curador-produto` conforme descrito em
   > `workflow-curadoria.md`."
   Manter P33-P35 intactos (runtime).

3. **Remover** seção "Convenção recomendada de scripts"
   (~linhas 371-395)

4. **Remover** seção "Catálogo de sugestões de harness por
   agente" (~linhas 397-530)

5. **Atualizar diagrama mermaid** — na fase VALIDAÇÃO,
   adicionar alt/else para o cenário de curadoria inline:
   ```
   alt Mapa/Harness ausente
     prod ->> prod: Executa fluxo de curadoria
     prod ->> Humano: Interage para criar Mapa/Harness
     prod -->> orq: Curadoria concluída (resumo curto)
   end
   ```

6. **Atualizar seção Contratos do Workflow** — ajustar
   referências dos contratos 1 (Mapa) e 2 (Harness) para
   apontar ao workflow de curadoria para definição,
   mantendo que o workflow de dev os consome.

**Dependências:** Fase A (novo arquivo deve existir antes
de referenciar)

---

### Fase D — Renomear o workflow de dev

**Ação:** `git mv docs/workflow-agentes.md docs/workflow-agentes-dev.md`

**Atualizar após o mv:**
- Título: "Workflow de Agentes — Desenvolvimento (`dev`)"
- Referências internas em:
  - `plan/orq-implementation.md`
  - `plan/sec-implementation.md`
  - `plan/rev-implementation.md`
  - `AGENTS.md`
  - `README.md` (se houver referência)
  - Testes em `tests/`

**Dependências:** Fase C (reduzir antes de renomear para
evitar conflitos)

---

### Fase E — Atualizar testes

**Arquivos em `tests/`:**
- Verificar quais testes referenciam `workflow-agentes.md`
  e atualizar para `workflow-agentes-dev.md`
- Adicionar teste básico para `workflow-curadoria.md`
  (existência, estrutura de seções)

**Dependências:** Fases C e D

---

### Fase F — Revisar agentes existentes

**Arquivos:** todos em `agents/`

Após todas as mudanças, revisar cada agente implementado
para verificar alinhamento com as alterações:

- `eng-software.md` — contrato de harness (P33 ajustado),
  P36 (instalação de deps)
- `dba.md` — contrato de harness (P33 ajustado)
- `qa.md` — contrato de harness (P33 ajustado)
- `rev.md` — contrato de harness (P33 ajustado)
- `curador-produto.md` — já atualizado na Fase B, mas
  validar coerência com o resultado final

**Checklist por agente:**
- Referência ao Mapa do Produto está correta?
- Menção a harness está alinhada com P33 ajustado?
- Nenhuma referência a workflow ou fases?
- Contrato operacional consistente?

**Dependências:** Fases B, C e D

---

## 4. Ordem de execução

```
Fase A (criar workflow-curadoria.md)
  ↓
Fase B (atualizar curador-produto.md)  ← paralela com C
Fase C (reduzir workflow-agentes.md)   ← paralela com B
  ↓
Fase D (renomear workflow-agentes.md → workflow-agentes-dev.md)
  ↓
Fase E (atualizar testes)
  ↓
Fase F (revisar agentes existentes)
```

---

## 5. Verificação

1. `make test` — todos os testes existentes passam
2. Grep por `workflow-agentes.md` no repo — nenhuma
   referência restante (só `workflow-agentes-dev.md`)
3. P33-P35 intactos no workflow de dev
4. Catálogo de harness presente no curador E no
   workflow-curadoria (design doc), ausente do
   workflow-dev
5. Nenhuma referência a fases/sequência de workflow
   no corpo do curador-produto.md
6. Frontmatter do curador com `bash: allow` e `task`
   para especialistas
7. Agentes existentes alinhados com P33 ajustado
   (Fase F)

---

## 6. Arquivos afetados

| Arquivo | Ação |
|---------|------|
| `docs/workflow-curadoria.md` | Criar (novo) |
| `docs/workflow-agentes.md` | Reduzir → renomear para `workflow-agentes-dev.md` |
| `agents/curador-produto.md` | Atualizar frontmatter + corpo |
| `plan/orq-implementation.md` | Atualizar referência ao workflow |
| `plan/sec-implementation.md` | Atualizar referência ao workflow |
| `plan/rev-implementation.md` | Atualizar referência ao workflow |
| `AGENTS.md` | Atualizar referência se houver |
| `tests/**` | Atualizar referências + novo teste |
| `agents/eng-software.md` | Revisar alinhamento (Fase F) |
| `agents/dba.md` | Revisar alinhamento (Fase F) |
| `agents/qa.md` | Revisar alinhamento (Fase F) |
| `agents/rev.md` | Revisar alinhamento (Fase F) |

---

## 7. Pontos resolvidos (antigos "em aberto")

1. ~~Tamanho do curador~~ → **Decidido:** catálogo fica
   no corpo do curador por enquanto. Reavaliar se o prompt
   ficar pesado demais.

2. ~~P36 (instalação durante execução)~~ → **Decidido:**
   ambos podem instalar. eng-software instala deps de
   harness durante construção (P36), curador instala
   durante curadoria. São momentos diferentes.

3. ~~Comportamento fora do workflow dev~~ → **Decidido:**
   sim, curadoria é capacidade interna — funciona igual
   chamado direto ou via orq.

4. ~~Quando cada agente usa o harness~~ → **Decidido:**
   harness é **obrigatório na construção e na revisão**,
   sempre que o agente altera artefatos. Só nesses casos.
   O Mapa do Produto deve registrar quais regras se
   aplicam a cada momento (`build`, `val` ou ambos).
   P33 no workflow de dev será ajustado para refletir
   essa obrigatoriedade. O catálogo de referência no
   curador já usa essas tags.
