---
name: web-research-exa-crawl4ai
description: >
  Use quando o humano pedir pesquisa, busca ou levantamento na web sem URL específica, notícias atuais, comparação de
  produtos, ferramentas ou fontes, ou verificação de preço, documentação ou informação pública online. Usa websearch
  como busca padrão e o CLI crwl (crawl4ai) para extração, validação e aprofundamento progressivo; prioriza fontes
  oficiais e delega documentos binários (PDF, DOCX, XLSX) para a skill doc-extract. Triggers: "pesquisa web",
  "pesquisar na web", "busca web", "pesquisa atual", "notícias", "verificar preço", "pesquisar na internet", "web
  research", "crawlar", "URL", "documentos binários", "doc-extract".
---

# Pesquisa Web Híbrida (websearch + crwl)

Respostas atuais com boa cobertura, alta precisão e consumo controlado de
tokens: websearch descobre fontes; `crwl` (crawl4ai) extrai e valida.

## Cadeia de descoberta

Use `websearch` como busca padrão — é uma capacidade: cada ambiente a
traduz para o melhor recurso de busca disponível. No OpenCode, `websearch`
usa a Exa AI (MCP hospedado, ativado por `OPENCODE_ENABLE_EXA=1`, sem
chave); sem Exa, cai para a busca padrão do ambiente. No Copilot e
similares, usa o equivalente nativo de busca web.

Não troque `websearch` por outra ferramenta por preferência de cliente.
Sem busca disponível: peça uma URL ao humano ou use fontes conhecidas
explicitamente.

## Regras principais

1. URL específica fornecida pelo humano: vá direto para `crwl`, sem busca.
2. Pesquisa aberta: siga a cadeia de descoberta.
3. Primeira passada: até 5 URLs relevantes.
4. Priorize fontes oficiais, documentação original e fontes primárias.
5. Incorpore sites sugeridos pelo humano quando pertinentes.
6. Combine busca geral com busca orientada por site quando melhorar
   cobertura, confiabilidade ou velocidade.
7. Valide as URLs escolhidas; não responda só com resultado bruto de busca.
8. Não use `curl` nem `bash` para buscar páginas quando as ferramentas
   desta skill forem suficientes.
9. Não responda pesquisa atual apenas com conhecimento do modelo.

## Fluxo padrão

1. **Classifique**: URL específica → extração direta; sem URL → cadeia de
   descoberta.
2. **Descoberta**: no máximo 2 buscas; selecione até 5 URLs; priorize
   fonte oficial, fontes primárias e sites sugeridos.
3. **Extração**: `crwl` conforme os exemplos abaixo; URL de arquivo
   binário → skill `doc-extract`.
4. **Validação**: fatos sensíveis, preço e notícia atual confirmados em
   2 fontes quando possível; em conflito, priorize a fonte oficial e
   declare a divergência.
5. **Resposta**: objetiva, com as principais fontes citadas; explicite
   incerteza; não despeje conteúdo bruto das páginas.

## Exemplos de operações `crwl`

Alvo reproduzível: `https://example.com`.

### Markdown
```bash
crwl crawl https://example.com -o md-fit
```

### HTML estruturado
```bash
crwl crawl https://example.com -o all -O page.json
```

### JavaScript
```bash
crwl crawl https://example.com -c 'js_code=document.title' -o md-fit
```

### Screenshot
```bash
crwl crawl https://example.com -c screenshot=true -o all -O saida.json
```

### Deep crawl
```bash
crwl crawl https://example.com --deep-crawl bfs --max-pages 10
```

URL que aponta direto para PDF, DOCX, XLSX ou PPTX → skill `doc-extract`:
a versão 0.9.2 do `crwl` não serializa PDF binário no JSON.

## Aprofundamento progressivo

Entre em aprofundamento quando as informações forem insuficientes, houver
conflito relevante ou o humano pedir mais investigação.

Regras:

1. Nada de avançar um nível sem confirmar com o humano.
2. Antes de cada iteração, informe: o que foi feito, por que não basta, o
   próximo passo e o esforço incremental estimado.
3. Só continue após confirmação.
4. Pare com confiança suficiente, pedido do humano ou ganho baixo frente
   ao custo.

Níveis:

| Nível | Escopo |
|---|---|
| 1 — padrão forte | até 5 URLs, foco em fontes oficiais e primárias |
| 2 — aprofundado | até 7 URLs, buscas refinadas, possível JS |
| 3 — investigação pesada | até 10 URLs, triangulação forte, confirmação explícita |

Mensagem padrão de checkpoint:

> "Já consultei <resumo>. Ainda faltam <lacunas ou conflitos>. Posso subir
> do <nível atual> para o <próximo nível>, fazendo <ações> e gastando
> <esforço incremental>. Quer que eu aprofunde?"

## Critérios de eficiência

- Pare com evidência suficiente para responder com confiança.
- Qualidade de fonte acima de quantidade.
- Sem HTML, screenshot e PDF por padrão; JS só com forte indício de
  conteúdo dinâmico relevante.
- Não crawle URLs redundantes quando a cobertura já basta.

## Resiliencia a rate limits (429)

`crwl` falha com exit code diferente de zero em 429, timeout ou bloqueio.
Erro com evidência de rate limit é temporário, não resposta final.

Comportamento obrigatório ao receber 429:

1. **NUNCA desista da pesquisa** por causa de 429; nunca responda
   incompleto sem informar a limitação.
2. **Aplique backoff progressivo**: espere 3-5 s e repita; persistindo,
   espere 10-15 s e tente mais uma vez.
3. **Reduza a carga** se o limite persistir: URLs em chamadas sequenciais
   (não paralelas); menos buscas; omita operações secundárias.
4. **Fallback por ferramenta**: falha do `crwl` → `webfetch` na mesma URL
   quando adequado; falha do `websearch` → busca padrão do ambiente.
5. **Ajuste o escopo da resposta**: informe o exit code, o timeout ou o
   bloqueio e quantas fontes foram validadas.
6. Depois de um 429, prefira chamadas sequenciais a paralelas.

## Fallback

Sem `websearch`: informe em uma linha e use a busca padrão do ambiente ou
peça uma URL específica.

Documentos binários (PDF, DOCX, PPTX, XLSX, imagens) com URL direta ao
arquivo: use a skill `doc-extract`, que baixa e extrai texto e tabelas via
Docling — não use `crwl` diretamente.
