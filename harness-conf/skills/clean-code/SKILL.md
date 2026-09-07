---
name: clean-code
description: >
  Regras de Clean Code para escrever código de produção. Use sempre que
  construir, implementar, alterar ou revisar código (TDD, feature, bugfix,
  UI, script). Não substitui code-simplification: esta skill define como
  escrever; aquela define como simplificar sem mudar comportamento.
  Triggers: "clean code", "Clean Code", "código limpo", "escrever código",
  "construir código", "implementar função", "produção", "TDD green",
  "dependência temporal", "acoplamento temporal", "temporal coupling",
  "CQS", "command query", "efeito colateral", "Law of Demeter",
  "Demeter", "SOLID", "SRP", "um nível de abstração", "não retornar null",
  "argumento de saída", "feature envy", "passo-a-passo da classe".
---

# Clean Code

Padrão de escrita. Carregar **antes** de produzir código. Depois que os
testes passam, use também `code-simplification` para reduzir complexidade
sem mudar comportamento.

## Relação com outras skills

| Skill | Papel |
|---|---|
| `clean-code` | Como escrever (nomes, funções, efeitos, limites) |
| `code-simplification` | Como aliviar código que já funciona |
| `test-driven-development` | Ciclo red-green-refactor |
| `code-review-and-quality` | Como revisar o resultado |

Não use esta skill para enxugar diff depois do fato — isso é
`code-simplification`. Não use para desenhar API pública — isso é
`api-and-interface-design`.

## Regras

### Nomes

- Nome revela intenção. Proibido `data`, `temp`, `result`, `info` sem
  contexto.
- Função é verbo (`calcularTotal`); booleano é predicado (`estaVencido`).
- Não abrevie salvo idioma universal (`id`, `url`, `api`).
- Se o nome precisa de comentário, o nome está errado.

### Funções

- Uma função faz **uma coisa**, num **único nível de abstração**.
- Leitura top-down: a função de cima narra; as de baixo executam
  (step-down).
- Poucos argumentos. 0–2 é o alvo; 3 exige justificativa; 4+ vira objeto.
- Sem flag booleana (`processar(x, true)`). Divida em funções ou use
  objeto de opções.
- Sem argumentos de saída. A função devolve o resultado; não muta
  parâmetro para comunicar.

### Efeitos e CQS

- **Command-Query Separation**: ou altera estado, ou devolve valor. Não
  os dois.
- Efeito colateral deve ser óbvio no nome (`salvarPedido`, não
  `obterPedido` que também grava).
- Não esconda I/O, rede ou mutação global no meio de cálculo.

### Dependência temporal

- Ordem de chamadas não pode ser um ritual secreto
  (`init()` antes de `run()`, senão explode).
- Se A precisa rodar antes de B, a API deve impedir o uso invertido:
  um objeto já válido, um construtor que recebe o pré-requisito, ou um
  único método que executa a sequência.
- Estado parcial compartilhado entre métodos públicos é cheiro. Prefira
  dados imutáveis ou um objeto que só existe depois de completo.

### Objetos e limites

- **Law of Demeter**: fale só com amigos próximos. Evite
  `pedido.cliente.endereco.cep`.
- Sem inveja de funcionalidade: a regra vive no objeto que tem os dados.
- Trate módulos externos (SDK, HTTP, arquivo) atrás de um limite. Não
  espalhe tipos e exceções deles pelo domínio.

### Erros e null

- Não retorne `null` para “não achei” se o chamador pode esquecer o
  teste. Prefira tipo opcional explícito, resultado, ou exceção no
  limite.
- Não passe `null` para dentro. Valide na borda.
- Erro de domínio é explícito (tipo/resultado), não código mágico
  (`-1`, `""`).

### SOLID (mínimo operacional)

- **SRP**: um motivo para mudar.
- **OCP**: estenda sem editar o núcleo estável.
- **DIP**: dependa de abstração estável do projeto, não de detalhe
  volátil.

Não invente interface para um único implementador.

### Comentários e formato

- Não comente o óbvio. Comente **porquê** (restrição, bug histórico).
- Código comentado morto: apague.
- Arquivo e função cabem na cabeça. Se a história não fecha sem scroll
  longo, extraia.

## Checklist antes de concluir código

- [ ] Nomes dizem o que o código faz
- [ ] Funções com uma responsabilidade e poucos argumentos
- [ ] Sem flag / argumento de saída
- [ ] Sem CQS quebrado
- [ ] Sem dependência temporal implícita
- [ ] Sem cadeia longa de Demeter
- [ ] Sem `null` escondido na API interna
- [ ] Comentários só de intenção

Se algum item falhar, corrija **antes** de declarar a construção
pronta. Depois rode `code-simplification` no código que você acabou
de escrever.
