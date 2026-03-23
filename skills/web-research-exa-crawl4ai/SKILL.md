---
name: web-research-exa-crawl4ai
description: Pesquisa web sem URL especifica - usa websearch/Exa para descoberta de fontes e Crawl4AI para extracao, validacao e aprofundamento progressivo com confirmacao do humano; incorpora sites sugeridos pelo humano e prioriza fontes oficiais.
---

Voce e uma skill de pesquisa web hibrida.

## Objetivo
Obter respostas atuais com boa cobertura, alta precisao e consumo controlado de token, combinando descoberta rapida de fontes com extracao e validacao confiaveis.

## Quando usar
Use esta skill quando o humano pedir:
- pesquisa, busca ou levantamento na web
- noticias atuais
- comparacao de produtos, servicos, ferramentas ou fontes
- verificacao de preco, documentacao ou informacoes publicas online
- aprofundamento progressivo sobre um tema pesquisavel na internet

## Quando nao usar
- Se o humano fornecer uma URL especifica como alvo principal da leitura, nao use `websearch`; va direto para `Crawl4AI`.
- Se a tarefa nao exigir pesquisa atual na web, nao carregue esta skill desnecessariamente.

## Ferramentas
- `websearch`: descoberta inicial de fontes, apenas quando o pedido NAO trouxer URL especifica
- `crawl4ai_md`: extracao principal de conteudo
- `crawl4ai_execute_js`: usar quando a pagina depender de JS ou o conteudo estiver incompleto
- `crawl4ai_html`: usar apenas se o markdown perder estrutura importante
- `crawl4ai_screenshot` e `crawl4ai_pdf`: usar apenas se o humano pedir evidencia visual ou arquivo

## Regras principais
1. Se o humano fornecer URL especifica, nao use `websearch`; va direto para `Crawl4AI`.
2. Se o pedido for uma pesquisa aberta sem URL especifica, use `websearch` para descoberta.
3. Na primeira passada, faca um esforco inicial robusto: consulte ate 5 URLs relevantes.
4. Priorize fontes oficiais, documentacao original, fontes primarias e os sites sugeridos pelo humano.
5. Se o humano sugerir sites, dominios, portais, motores de busca ou plataformas especificas, incorpore esses alvos na estrategia de busca e priorize-os quando pertinentes.
6. Combine busca geral com busca orientada por site quando isso melhorar cobertura, confiabilidade ou velocidade.
7. Nao baseie a resposta apenas no resultado bruto da busca; valide nas URLs escolhidas.
8. Nao use `curl` ou `bash` para buscar paginas web quando `websearch` ou `Crawl4AI` forem suficientes.
9. Nao responda pesquisa atual apenas com conhecimento do modelo quando houver necessidade real de busca.

## Fluxo padrao
1. Classifique o pedido:
   - com URL especifica -> ir direto para extracao
   - sem URL especifica -> usar `websearch`
2. Descoberta:
   - fazer 1-2 buscas no maximo
   - selecionar ate 5 URLs
   - priorizar fonte oficial, fontes primarias e fontes sugeridas pelo humano
3. Extracao:
   - usar `crawl4ai_md` nas URLs selecionadas
   - se necessario, usar `crawl4ai_execute_js`
   - usar `crawl4ai_html` apenas em caso de perda de estrutura relevante
4. Validacao:
   - para fatos sensiveis, preco e noticia atual, confirmar em pelo menos 2 fontes quando possivel
   - em caso de conflito, priorizar fonte oficial e declarar divergencia
5. Resposta:
   - responder de forma objetiva
   - citar as principais fontes usadas
   - explicitar incerteza quando houver
   - resumir achados sem despejar conteudo bruto das paginas

## Aprofundamento progressivo
Entre em modo de aprofundamento quando:
- as informacoes estiverem insuficientes
- houver conflito relevante entre fontes
- o humano pedir para aprofundar, pesquisar mais ou ir mais fundo

### Regras do aprofundamento
1. Nao avance mais de um nivel sem confirmar com o humano.
2. Antes de cada nova iteracao, informe:
   - o que ja foi feito
   - por que ainda nao basta
   - o que sera feito na proxima iteracao
   - quanto mais de esforco sera gasto
3. So continue apos confirmacao do humano.
4. Pare quando houver confianca suficiente, quando o humano pedir para parar, ou quando o ganho esperado for baixo frente ao custo.

### Niveis
- Nivel 1 - padrao forte:
  - ate 5 URLs totais
  - foco em fonte oficial, sites sugeridos e fontes complementares
- Nivel 2 - aprofundado:
  - ate 7 URLs totais
  - buscas refinadas adicionais
  - pode usar `crawl4ai_execute_js`
- Nivel 3 - investigacao pesada:
  - ate 10 URLs totais
  - triangulacao ampla e verificacao cruzada forte
  - requer confirmacao explicita do humano

## Mensagem padrao de checkpoint
Use um texto neste formato:
"Ja consultei <resumo curto do que foi feito>. Ainda faltam <lacunas ou conflitos>. Na proxima iteracao posso subir do <nivel atual> para o <proximo nivel>, fazendo <acoes planejadas>. Isso adiciona aproximadamente <esforco incremental: buscas, URLs e possivel JS>. Quer que eu aprofunde?"

## Criterios de eficiencia
- Pare assim que houver evidencia suficiente para responder com confianca.
- Prefira qualidade de fonte a quantidade de fontes.
- Evite `html`, `screenshot` e `pdf` por padrao.
- Use JS apenas quando houver forte indicio de conteudo dinamico relevante.
- Nao faca crawl de URLs claramente redundantes ou de baixa qualidade se ja houver cobertura suficiente.

## Fallback
Se `websearch` nao estiver disponivel, informe isso brevemente e execute a melhor estrategia possivel apenas com `Crawl4AI`, deixando claro que a descoberta de fontes pode ficar menos eficiente.
