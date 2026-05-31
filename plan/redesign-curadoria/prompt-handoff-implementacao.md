# Prompt de Handoff — Implementação do Redesign de Curadoria

> Este prompt deve ser colado em uma nova sessão de agente
> para solicitar a criação de um planejamento detalhado de
> implementação.

---

## Contexto

Acabamos de concluir uma sessão de discovery assistido
onde redesenhamos o ecossistema de curadoria do produto.
Todas as decisões estão documentadas em:

📄 **`plan/redesign-curadoria/redesign-ecossistema-curadoria.md`**

Leia esse arquivo **inteiro** antes de prosseguir.

---

## Resumo Executivo

O **Mapa do Produto** (template tabular fixo com 3 seções
obrigatórias) morre como artefato único. O conteúdo
sobrevive distribuído em:

1. **`/doc/README.md`** — 3 seções:
   - Definição de Escopo (estrutura do que elicitar)
   - Elementos de Especificação (tabela)
   - Estratégias de Indexação de Código

2. **`AGENTS.md`** (topo):
   - Harness por Agente
   - Link para `/doc/README.md`

---

## Mudanças Principais

### Agentes

| Antes | Depois |
|-------|--------|
| `editor-mapa-produto` | `curador-produto-editor` (rename) |
| `curador-produto` | Mantém nome, muda onde olha |
| `analista` | Mais flexível, sem BACKLOG.md obrigatório |
| `val-harness` | Cruza com AGENTS.md (não Mapa) |

### Workflows

| Arquivo | Mudança |
|---------|---------|
| `docs/workflow-definicao-escopo.md` | **CRIAR** (novo workflow) |
| `docs/workflow-curadoria.md` | Revisar (novos artefatos) |
| `docs/workflow-agentes-dev.md` | Revisar (VALIDAÇÃO transferida) |

### Arquivos de Projeto

| Arquivo | Ação |
|---------|------|
| `/doc/README.md` | Criar template |
| `AGENTS.md` | Atualizar (Harness + link) |
| `agents/editor-mapa-produto.md` | Rename → `curador-produto-editor.md` |
| `agents/curador-produto.md` | Revisar referências |
| `agents/analista.md` | Revisar (mais flexível) |
| `agents/references/mensagens-curadoria.md` | Atualizar |

---

## O Que Você Deve Fazer

### 1. Leia o arquivo de redesign completo

```
plan/redesign-curadoria/redesign-ecossistema-curadoria.md
```

Entenda todas as decisões, papéis, workflows e
mapeamento de referências.

### 2. Crie um planejamento detalhado de implementação

O planejamento deve incluir:

#### A) Ordem de implementação

- Quais arquivos modificar primeiro?
- Quais dependências existem entre as mudanças?
- O que pode ser feito em paralelo?

#### B) Tarefas específicas

Para cada arquivo a modificar:
- O que exatamente mudar?
- Quais seções adicionar/remover/editar?
- Quais referências atualizar?

#### C) Validação

- Como testar que as mudanças estão corretas?
- Quais workflows precisam ser validados?
- Quais agentes precisam ser testados?

#### D) Riscos e mitigação

- O que pode quebrar?
- Como mitigar?
- Precisa de rollback plan?

### 3. Apresente o planejamento ao humano

- Mostre a ordem de implementação
- Liste as tarefas específicas
- Aguarde aprovação antes de executar

### 4. Execute o planejamento (após aprovação)

- Implemente as mudanças na ordem aprovada
- Valide cada etapa
- Reporte progresso ao humano

---

## Restrições Importantes

1. **Não execute nada sem aprovação do humano** — este
   é um redesign grande que afeta múltiplos workflows e
   agentes. Cada mudança precisa ser validada.

2. **Mantenha a separação de responsabilidades**:
   - `curador-produto` NUNCA edita `/doc/README.md`
   - `analista` NUNCA edita `/doc/README.md`
   - `curador-produto-editor` é o ÚNICO que edita

3. **Workflow de curadoria é autônomo** — NUNCA chama
   `analista`. Mantém separação clara.

4. **VALIDAÇÃO do dev é transferida** — não removida.
   Vai para o workflow de Definição de Escopo.

5. **Referências devem ser consistentes**:
   - "Mapa do Produto" → `/doc/README.md`
   - "editor-mapa-produto" → `curador-produto-editor`
   - Ver mapeamento completo no arquivo de redesign

---

## Perguntas?

Se algo não estiver claro no arquivo de redesign,
pergunte ao humano antes de assumir. Melhor validar do
que implementar errado.

---

## Pronto?

Leia o arquivo de redesign e comece pelo planejamento.
