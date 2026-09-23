---
name: clean-code
description: >
  Use sempre que construir, implementar, alterar ou revisar código de produção (TDD, feature, bugfix, UI,
  script). Não substitui code-simplification: esta define como escrever; aquela, como simplificar sem mudar
  comportamento. Triggers:
  "clean code", "Clean Code", "código limpo", "escrever código", "construir código", "implementar função",
  "produção", "TDD green", "dependência temporal", "acoplamento temporal", "temporal coupling", "CQS",
  "command query", "efeito colateral", "Law of Demeter", "Demeter", "SOLID", "SRP", "um nível de abstração",
  "não retornar null", "argumento de saída", "feature envy", "passo-a-passo da classe".
---

# Clean Code

Padrão de escrita. Carregue **antes** de produzir código. Enxugar o que já funciona é papel de
`code-simplification`; o ciclo red-green-refactor é do `test-driven-development`; desenhar API
pública é do `api-and-interface-design`.

## Nomes

- Nome revela intenção. Proibido `data`, `temp`, `result`, `info` sem contexto.
- Função é verbo (`calcularTotal`); booleano é predicado (`estaVencido`).
- Não abrevie salvo idioma universal (`id`, `url`, `api`).
- Nome que precisa de comentário está errado.

## Funções

- Uma função faz **uma coisa**, num **único nível de abstração**.
- Leitura top-down: a função de cima narra, as de baixo executam (step-down).
- Poucos argumentos: 0-2 é o alvo, 3 exige justificativa, 4+ vira objeto.
- Sem flag booleana (`processar(x, true)`): divida em funções ou use objeto de opções.
- Sem argumento de saída: devolva o resultado, não mute parâmetro para comunicar.

## Efeitos e CQS

- Command-Query Separation: ou altera estado, ou devolve valor. Nunca os dois.
- Efeito colateral aparece no nome (`salvarPedido`, não `obterPedido` que também grava).
- Não esconda I/O, rede ou mutação global dentro de cálculo.

## Dependência temporal

- Ordem de chamadas não pode ser ritual secreto (`init()` antes de `run()`, senão explode).
- Se A precisa rodar antes de B, a API impede o uso invertido: objeto já válido, construtor que
  recebe o pré-requisito, ou um único método que executa a sequência.
- Estado parcial compartilhado entre métodos públicos é cheiro: prefira dados imutáveis ou um
  objeto que só existe depois de completo.

## Objetos e limites

- **Law of Demeter**: fale só com amigos próximos. Evite `pedido.cliente.endereco.cep`.
- Sem feature envy: a regra vive no objeto que tem os dados.
- Módulo externo (SDK, HTTP, arquivo) fica atrás de um limite; não espalhe os tipos e exceções
  dele pelo domínio.

### Erros e null

- Não retorne `null` para "não achei" se o chamador pode esquecer o teste: prefira tipo opcional
  explícito, resultado ou exceção no limite.
- Não passe `null` para dentro. Valide na borda.
- Erro de domínio é explícito (tipo/resultado), não código mágico (`-1`, `""`).

## SOLID (mínimo operacional)

- **SRP**: um motivo para mudar.
- **OCP**: estenda sem editar o núcleo estável.
- **DIP**: dependa de abstração estável do projeto, não de detalhe volátil.
- Não invente interface para um único implementador.

### Comentários e formato

- Não comente o óbvio. Comente o **porquê** (restrição, bug histórico).
- Código comentado morto: apague.
- Arquivo e função cabem na cabeça; história que não fecha sem scroll longo pede extração.

## Checklist antes de concluir código

- [ ] Nomes dizem o que o código faz
- [ ] Funções com uma responsabilidade e poucos argumentos
- [ ] Sem flag nem argumento de saída
- [ ] Sem CQS quebrado
- [ ] Sem dependência temporal implícita
- [ ] Sem cadeia longa de Demeter
- [ ] Sem `null` escondido na API interna
- [ ] Comentários só de intenção

Item falhou? Corrija **antes** de declarar a construção pronta. Depois rode
`code-simplification` no código recém-escrito.
