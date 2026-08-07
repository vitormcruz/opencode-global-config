---
name: web-research-exa-crawl4ai
description: >
  Pesquisa web sem URL específica - usa web_search_exa, websearch ou a busca
  padrão do ambiente para descobrir fontes e o CLI crwl (crawl4ai) para
  extração, validação e aprofundamento progressivo. Prioriza fontes oficiais e
  delega documentos binários para a skill doc-extract.
---

Você é uma skill de pesquisa web híbrida.

## Objetivo
Obter respostas atuais com boa cobertura, alta precisão e consumo controlado de
tokens, combinando descoberta de fontes com extração e validação confiáveis.

## Quando usar
Use esta skill quando o humano pedir:
- pesquisa, busca ou levantamento na web
- notícias atuais
- comparação de produtos, serviços, ferramentas ou fontes
- verificação de preço, documentação ou informações públicas online
- aprofundamento progressivo sobre um tema pesquisável na internet

## Quando não usar
- Se o humano fornecer uma URL específica como alvo principal, não use busca;
  vá direto para `crwl`.
- Se a tarefa não exigir pesquisa atual na web, não carregue esta skill.

## Cadeia de descoberta
Use a primeira opção disponível nesta ordem:
1. `web_search_exa`, se a ferramenta remota Exa estiver disponível.
2. `websearch`, se a busca nativa do OpenCode estiver disponível.
3. a busca padrão do ambiente, como fallback final.

Não troque essa ordem por preferência de cliente. Se nenhuma busca estiver
disponível, peça uma URL ao humano ou use fontes conhecidas explicitamente.

## Ferramentas
- `crwl`: CLI do crawl4ai para extração de Markdown, HTML, JS, screenshot,
  PDF e deep crawl.
- `web_search_exa`: descoberta inicial de fontes, quando disponível.
- `websearch`: descoberta alternativa, quando disponível.
- `doc-extract`: extração de documentos binários.

## Regras principais
1. Se o humano fornecer URL específica, vá direto para `crwl`.
2. Em pesquisa aberta, siga a cadeia de descoberta declarada acima.
3. Na primeira passada, consulte até 5 URLs relevantes.
4. Priorize fontes oficiais, documentação original e fontes primárias.
5. Incorpore sites sugeridos pelo humano quando forem pertinentes.
6. Combine busca geral com busca orientada por site quando isso melhorar
   cobertura, confiabilidade ou velocidade.
7. Valide as URLs escolhidas; não responda apenas com o resultado bruto da busca.
8. Não use `curl` ou `bash` para buscar páginas quando as ferramentas desta
   skill forem suficientes.
9. Não responda pesquisa atual apenas com conhecimento do modelo.

## Fluxo padrão
1. Classifique o pedido:
   - com URL específica: vá direto para extração
   - sem URL específica: siga a cadeia de descoberta
2. Descoberta:
   - faça no máximo 2 buscas
   - selecione até 5 URLs
   - priorize fonte oficial, fontes primárias e sites sugeridos
3. Extração:
   - use `crwl` conforme os exemplos executáveis abaixo
   - para URL binária, use a skill `doc-extract`
4. Validação:
   - para fatos sensíveis, preço e notícia atual, confirme em 2 fontes quando
     possível
   - em conflito, priorize fonte oficial e declare a divergência
5. Resposta:
   - responda de forma objetiva e cite as principais fontes
   - explicite incerteza e não despeje conteúdo bruto das páginas

## Exemplos de operações `crwl`
Os comandos abaixo usam `https://example.com` como alvo reproduzível.

### Markdown
```bash
crwl https://example.com -o md-fit
```

### HTML estruturado
```bash
crwl https://example.com -o json > page.json
```

### JavaScript
```bash
crwl https://example.com -c 'js_code=document.title' -o md-fit
```

### Screenshot
```bash
crwl https://example.com -c screenshot=true -O saida.json
```

### PDF
```bash
crwl https://example.com -c pdf=true -O saida.json
```

### Deep crawl
```bash
crwl https://example.com --deep-crawl bfs --max-pages 10
```

## Aprofundamento progressivo
Entre em modo de aprofundamento quando as informações estiverem insuficientes,
houver conflito relevante ou o humano pedir mais investigação.

### Regras do aprofundamento
1. Não avance mais de um nível sem confirmar com o humano.
2. Antes de cada iteração, informe o que foi feito, por que não basta, o próximo
   passo e o esforço adicional estimado.
3. Só continue após confirmação do humano.
4. Pare quando houver confiança suficiente, o humano pedir para parar ou o ganho
   esperado for baixo frente ao custo.

### Níveis
- Nível 1 - padrão forte: até 5 URLs, com foco em fontes oficiais e primárias.
- Nível 2 - aprofundado: até 7 URLs, buscas refinadas e possível JS.
- Nível 3 - investigação pesada: até 10 URLs, triangulação forte e confirmação
  explícita.

## Mensagem padrão de checkpoint
Use este formato:
"Já consultei <resumo>. Ainda faltam <lacunas ou conflitos>. Posso subir do
<nível atual> para o <próximo nível>, fazendo <ações> e gastando
<esforço incremental>. Quer que eu aprofunde?"

## Critérios de eficiência
- Pare quando houver evidência suficiente para responder com confiança.
- Prefira qualidade de fonte a quantidade.
- Evite HTML, screenshot e PDF por padrão.
- Use JS somente quando houver forte indício de conteúdo dinâmico relevante.
- Não faça crawl de URLs redundantes quando já houver cobertura suficiente.

## Resiliencia a rate limits (429)
O `crwl` pode retornar falha com exit code diferente de zero quando o site
responde 429, o timeout expira ou há bloqueio. O erro deve ser tratado como
temporário quando houver evidência de rate limit, não como resposta final.

### Comportamento obrigatório ao receber 429
1. **NUNCA desista da pesquisa** por causa de 429 e não retorne resposta
   incompleta sem informar a limitação.
2. **Aplique backoff progressivo**:
   - espere 3-5 segundos e repita o comando
   - se persistir, espere 10-15 segundos e tente mais uma vez
3. **Reduza a carga** se o limite persistir:
   - processe URLs em chamadas sequenciais, não em paralelo
   - reduza o número de buscas e omita operações secundárias
4. **Use fallback por ferramenta**:
   - em falha do `crwl`, tente `webfetch` na mesma URL quando for adequado
   - em falha de `websearch`, tente `web_search_exa` ou a busca padrão
5. **Ajuste o escopo da resposta**:
   - informe o exit code, timeout ou bloqueio e quantas fontes foram validadas
6. Quando um 429 já ocorreu, prefira chamadas sequenciais a chamadas paralelas.

## Fallback
Se `web_search_exa` e `websearch` não estiverem disponíveis, informe isso
brevemente e use a busca padrão do ambiente ou peça uma URL específica.

**Fallback para documentos binários**: não use `crwl` diretamente para PDF,
DOCX, PPTX, XLSX ou imagens quando a URL apontar para o arquivo. Use a skill
`doc-extract`, que baixa o arquivo e extrai texto e tabelas via Docling.
