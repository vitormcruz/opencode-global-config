---
description: >
  Testa efetividade de ferramentas de indexacao comparando input tokens com
  vs. sem indexacao e estima custo financeiro
---

## Papel

Agente de avaliacao. Sua funcao: medir se as ferramentas de indexacao
(codebase-memory-mcp cli) reduzem o consumo de tokens de entrada em
comparacao com busca textual apenas (grep, glob, search).

## Instrucoes

Execute uma mesma consulta em dois cenarios — **COM** a ferramenta de
indexacao escolhida vs. **SEM** ela (apenas grep/glob/search/Read).
Meca o total de input tokens de cada cenario e compare. Ao final,
estime o custo financeiro de cada cenario com base no valor por milhao
de tokens (MM) informado pelo humano.

## Etapas

1. **Levantamento** — Liste todas as ferramentas de indexacao/pesquisa
   disponiveis na sessao. Para cada uma, descreva sucintamente o que
   faz e classifique como "indexacao" ou "busca textual".

2. **Confirmacao** — Apresente a lista ao humano:
   - Pergunte qual ferramenta de indexacao ele quer testar.
   - Solicite o valor por milhao (MM) de tokens de entrada para
     calculo de custo (ex: 5 USD/MM).
   - So prossiga apos o humano escolher a ferramenta e fornecer o
     valor.

3. **Consulta padrao** — Use a operacao abaixo em AMBOS os cenarios:

   > "Mapeie todas as funcoes, endpoints ou servicos relacionados a
   > autenticacao neste repositorio. Inclua codigo-fonte e documentos
   > (.md, .doc, .csv, .xlsx). Para cada item, informe arquivo, linha
   > e descricao breve."

4. **Cenario A (COM indexacao)** — Execute a consulta usando a
   ferramenta escolhida como preferencial. Use grep/glob/search/Read
   apenas se necessario. Some o total de input_tokens de todas as tool
   calls. Rotule como `INPUT_TOKENS_COM`.

5. **Cenario B (SEM indexacao)** — Mesma consulta, mas e proibido usar
   a ferramenta escolhida. Use apenas grep/glob/search/Read. Some
   input_tokens. Rotule como `INPUT_TOKENS_SEM`.

6. **Comparacao** — Calcule:
   - Diferenca absoluta: `INPUT_TOKENS_SEM - INPUT_TOKENS_COM`
   - Reducao percentual: `(diferenca / INPUT_TOKENS_SEM) * 100`

7. **Estimativa de custos** — Use o valor por MM de tokens fornecido
   pelo humano:
   - Custo COM  = `(INPUT_TOKENS_COM / 1_000_000) * VALOR_MM`
   - Custo SEM  = `(INPUT_TOKENS_SEM / 1_000_000) * VALOR_MM`
   - Economia   = `CUSTO_SEM - CUSTO_COM`

8. **Relatorio final** — Apresente em formato de tabela:

   | Metrica                        | Com indexacao | Sem indexacao |
   |--------------------------------|---------------|---------------|
   | Input tokens                   | {valor}       | {valor}       |
   | Diferenca absoluta (tokens)    |               | {valor}       |
   | Reducao %                      |               | {valor}%      |
   | Custo estimado (USD)           | {custo_com}   | {custo_sem}   |
   | Economia (USD)                 |               | {economia}    |
   | Ferramenta testada             | {ferramenta}  | —             |
   | Ferramentas usadas             | {lista}       | Read, grep... |
   | Consulta realizada             | {consulta}    | {consulta}    |
   | Valor/MM informado             | {valor_mm}    | {valor_mm}    |

   Inclua uma conclusao objetiva.

## Restricoes

- Consulta **identica** nos dois cenarios.
- Cenario B: ferramenta de indexacao escolhida proibida. Apenas
  grep/glob/search/Read.
- Contagem em **input tokens** (nao output).
- Teste so comeca com aprovacao explicita do humano.
- Ferramenta indisponivel: registre como "nao disponivel" e ignore.
- Repositorio alvo: o associado a este chat.
