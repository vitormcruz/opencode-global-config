---
name: code-simplification
description: >
  Use ao escrever ou alterar código de produção (during construction), quando o
  código funciona mas está difícil de ler ou manter, após implementar feature
  com testes passando, no review quando complexidade for apontada, ao
  encontrar aninhamento profundo, função longa ou nomes pouco claros, ao
  consolidar lógica espalhada, e em todo passo TDD green/refactor. Reduz
  complexidade preservando comportamento exato.
  Triggers: "simplify", "simplification", "refactor for clarity",
  "too complex", "hard to read", "deep nesting", "long function",
  "extract function", "remove duplication", "YAGNI", "dead code",
  "rename variable", "code smell", "cyclomatic complexity",
  "consolidate logic", "reduce cognitive load", "construir código",
  "escrever código", "implementar", "TDD", "refatorar".
---

# Code Simplification

Reduza complexidade preservando comportamento exato. O objetivo não é menos linha: é código mais
fácil de ler, entender, alterar e depurar. Teste de aceitação de cada simplificação: "um colega
novo entenderia mais rápido que o original?"

## Quando NÃO usar

- O código já está limpo e legível: não simplifique por simplificar.
- Você ainda não entende o que o código faz: compreenda antes.
- O trecho é crítico para performance e a versão "mais simples" é mensuravelmente mais lenta.
- O módulo vai ser reescrito por inteiro: simplificar código descartável é esforço perdido.

## Os cinco princípios

### 1. Preserve o comportamento exatamente

Mude como o código se expressa, nunca o que ele faz. Input, output, efeito colateral, ordem,
comportamento de erro e edge cases permanecem idênticos. Dúvida se preserva comportamento? Não
faça a mudança.

Antes de cada mudança, responda: mesma saída para todo input? Mesmo comportamento de erro?
Mesmos efeitos colaterais e ordem? Todos os testes existentes passam sem modificação?

### 2. Siga as convenções do projeto

Simplificar é aproximar o código do padrão do codebase, não importar preferência externa. Antes
de simplificar, leia as convenções do projeto, estude como o código vizinho trata o mesmo padrão e
siga o estilo local: ordenação de import, estilo de declaração de função, nomenclatura, padrão de
erro, profundidade de anotação de tipo. Simplificação que quebra consistência do projeto não é
simplificação: é churn.

### 3. Clareza acima de esperteza

Código explícito vence código compacto quando o compacto exige pausa mental para parsear.

```typescript
// DIFÍCIL: cadeia de ternários
const label = isNew ? 'New' : isUpdated ? 'Updated' : isArchived ? 'Archived' : 'Active';

// CLARO: ifs nomeados
function getStatusLabel(item: Item): string {
  if (item.isNew) return 'New';
  if (item.isUpdated) return 'Updated';
  if (item.isArchived) return 'Archived';
  return 'Active';
}
```

### 4. Mantenha o equilíbrio

A falha da simplificação é a simplificação demais:

- **Inline agressivo:** remover helper que dava nome a um conceito piora o call site.
- **Juntar lógica não relacionada:** duas funções simples virarem uma complexa não é mais simples.
- **Remover abstração "desnecessária":** parte da abstração existe para extensibilidade ou teste.
- **Otimizar contagem de linha:** a meta é compreensão, não menos linha.

### 5. Escopo no que mudou

Por padrão, simplifique código modificado recentemente. Refatoração drive-by em código não
relacionado cria ruído no diff e risco de regressão. Escopo maior só sob pedido explícito.

## O processo

### Passo 1: entenda antes de tocar (Chesterton's Fence)

Vi uma cerca na estrada e não sabe por que ela está lá? Não derrube. Primeiro entenda o motivo;
depois decida se ele ainda vale.

Antes de simplificar, responda: qual a responsabilidade deste código? Quem chama e o que ele
chama? Quais edge cases e caminhos de erro? Há testes que fixam o comportamento? Por que pode ter
sido escrito assim (performance, restrição de plataforma, razão histórica)? O `git blame` mostra
qual contexto?

Sem respostas, você ainda não pode simplificar: leia mais contexto.

### Passo 2: identifique oportunidades

**Complexidade estrutural:**

| Padrão | Sinal | Simplificação |
|---|---|---|
| Aninhamento profundo (3+) | Fluxo difícil de seguir | Guard clause ou helper |
| Função longa (50+) | Múltiplas responsabilidades | Divida em funções com nome descritivo |
| Ternário aninhado | Pilha mental para parsear | if/else, switch ou lookup object |
| Flag booleana | `doThing(true, false, true)` | Objeto de opções ou funções separadas |
| Condicional repetido | Mesmo `if` em vários lugares | Função predicado com nome |

**Nomenclatura e legibilidade:**

| Padrão | Sinal | Simplificação |
|---|---|---|
| Nome genérico | `data`, `result`, `temp`, `val` | Renomeie para o conteúdo: `userProfile`, `validationErrors` |
| Abreviação | `usr`, `cfg`, `btn`, `evt` | Palavra completa, salvo abreviação universal (`id`, `url`, `api`) |
| Nome enganoso | `get` que também muta estado | Renomeie para o comportamento real |
| Comentário "o quê" | `// incrementa contador` sobre `count++` | Apague o comentário |
| Comentário "porquê" | `// retry: API oscila sob carga` | Mantenha: carrega intenção que o código não expressa |

**Redundância:**

| Padrão | Sinal | Simplificação |
|---|---|---|
| Lógica duplicada | Mesmas 5+ linhas em vários lugares | Extraia função compartilhada |
| Código morto | Branch inalcançável, variável sem uso, bloco comentado | Remova (confirme que está morto) |
| Abstração sem valor | Wrapper que não acrescenta nada | Faça inline, chame direto |
| Over-engineering | Factory de factory, strategy com uma strategy | Substitua pela forma direta |
| Type assertion redundante | Cast para tipo já inferido | Remova a asserção |

### Passo 3: aplique em incrementos

Uma simplificação por vez, testes após cada mudança. Falhou? Reverta e repense; assim você sabe
qual mudança quebrou. Refatoração nunca vai no mesmo PR de feature ou bugfix.

**Regra dos 500:** refatoração que toca mais de 500 linhas merece automação (codemod, script sed,
transformação de AST). Edição manual nessa escala é propensa a erro e exaustiva de revisar.

### Passo 4: verifique o resultado

Compare antes e depois: a versão simplificada é genuinamente mais fácil de entender? Introduziu
padrão inconsistente com o codebase? O diff está limpo e revisável? Um colega aprovaria?

A versão "simplificada" ficou mais difícil de entender ou revisar? Reverta. Nem toda tentativa de
simplificação vale.

## Racionalizações comuns

| Racionalização | Realidade |
|---|---|
| "Está funcionando, não mexa" | Código funcional mas ilegível será difícil de consertar quando quebrar. |
| "Menos linha é sempre mais simples" | Ternário de 1 linha não supera if/else de 5. Simples é compreensão rápida. |
| "Aproveito e simplifico outro código" | Fora de escopo: diff ruidoso e regressão em código que não era para mudar. |
| "Os tipos se auto-documentam" | Tipos documentam estrutura, não intenção. Nome bem escolhido explica o porquê. |
| "Abstração pode ser útil depois" | Abstração especulativa é complexidade sem valor. Re-adicione quando precisar. |
| "O autor original devia ter um motivo" | Talvez: veja `git blame` (Chesterton). Às vezes é só resíduo de iteração. |
| "Refatoro junto com a feature" | Mudança mista é difícil de revisar e reverter. Separe refatoração de feature. |

## Red flags

- Simplificação que exige modificar teste para passar (você mudou comportamento).
- Versão "simplificada" maior e mais difícil de seguir que a original.
- Rename para sua preferência em vez da convenção do projeto.
- Error handling removido ou enfraquecido "para deixar o código mais limpo".
- Muitas simplificações num único commit difícil de revisar.

## Verificação

- [ ] Todos os testes existentes passam sem modificação
- [ ] Build sucede sem warning novo; linter/formatter passa
- [ ] Cada simplificação é um incremento revisável; diff sem mudança não relacionada
- [ ] Código segue as convenções do projeto
- [ ] Nenhum error handling removido ou enfraquecido
- [ ] Nenhum código morto restante (import sem uso, branch inalcançável)
- [ ] Um revisor aprovaria como melhoria líquida
