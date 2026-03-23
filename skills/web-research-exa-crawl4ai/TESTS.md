# Testes da skill `web-research-exa-crawl4ai`

Use esta suite para comparar o comportamento antes e depois da ativacao da skill.

## Como medir

Para cada prompt, registre:
- tempo total de resposta
- quantidade de buscas feitas
- quantidade de URLs consultadas
- uso ou nao de fonte oficial
- uso ou nao de JS
- clareza sobre incerteza
- qualidade factual da resposta
- se houve aprofundamento progressivo com confirmacao humana

## Bloco A - descoberta, validacao e eficiencia

1. Pesquisa aberta de produto

Prompt:
```text
Pesquise as melhores canetas 3D de 2026 e resuma os 3 modelos mais citados.
```

Esperado:
- usar descoberta inicial sem URL especifica
- consultar ate 5 URLs na primeira passada
- priorizar fontes confiaveis

2. Preco atual em fonte oficial

Prompt:
```text
Qual e o preco atual do produto X no site oficial?
```

Esperado:
- localizar rapidamente a pagina oficial
- validar o valor em conteudo extraido da URL

3. Documentacao tecnica oficial

Prompt:
```text
Pesquise como configurar MCP servers no OpenCode com base na documentacao oficial.
```

Esperado:
- descoberta da documentacao correta
- resposta baseada em fonte oficial

4. Noticias atuais

Prompt:
```text
Busque noticias desta semana sobre IA open source e resuma os principais anuncios.
```

Esperado:
- boa cobertura de noticias recentes
- triangulacao entre fontes quando necessario

5. URL especifica

Prompt:
```text
Leia esta URL e extraia os pontos principais: <url>
```

Esperado:
- nao usar descoberta geral
- ir direto para extracao da URL

## Bloco B - sites sugeridos pelo humano

6. Priorizacao de docs e GitHub

Prompt:
```text
Pesquise sobre MCP no OpenCode. Priorize docs oficiais e GitHub.
```

Esperado:
- incorporar os sites sugeridos na busca
- priorizar fontes oficiais

7. Priorizacao de portais de noticia

Prompt:
```text
Pesquise noticias sobre IA. Priorize Reuters e The Verge.
```

Esperado:
- incluir os portais sugeridos na estrategia
- complementar com outras fontes se necessario

8. Mistura de site oficial, GitHub e comunidade

Prompt:
```text
Pesquise sobre biblioteca X. Use site oficial, GitHub e Reddit.
```

Esperado:
- combinar fontes primarias e comunitarias
- sinalizar divergencias se houver

## Bloco C - aprofundamento progressivo

9. Aprofundar apos primeira resposta

Prompt inicial:
```text
Pesquise o preco medio do produto Y em lojas brasileiras.
```

Prompt seguinte:
```text
Aprofunde.
```

Esperado:
- explicar o que ja foi feito
- explicar por que ainda nao basta
- informar o esforco adicional da proxima rodada
- pedir confirmacao antes de seguir alem de um nivel

10. Ir o mais fundo possivel com checkpoints

Prompt:
```text
Pesquise W e va o mais fundo possivel, mas me pergunte antes de cada rodada.
```

Esperado:
- aprofundamento progressivo em etapas
- confirmacao humana antes de cada escalada

11. Conflito entre fontes

Prompt:
```text
Pesquise sobre Z e me diga se a informacao e confiavel.
```

Esperado:
- detectar conflito ou insuficiencia de evidencias
- propor proxima iteracao com custo incremental claro

12. Conteudo dinamico por JS

Prompt:
```text
Pesquise a pagina X, e se faltar conteudo carregado por JS aprofunde.
```

Esperado:
- usar JS apenas se houver indicio forte de necessidade
- nao gastar esse esforco cedo demais

## Criterios de sucesso

- menor latencia media em pesquisas abertas
- melhor uso de fontes oficiais
- menos consultas desnecessarias
- melhor equilibrio entre cobertura e custo
- respostas mais confiaveis em temas atuais
- aprofundamento progressivo claro e controlado
