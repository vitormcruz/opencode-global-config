# Regras Globais

## Idioma
- PT-BR (ASCII ok).

## Concisao
- Responda de forma curta por padrao.
- Detalhe apenas quando o humano pedir explicitamente ou quando houver risco de ambiguidade/erro.
- Prefira listas curtas a textos longos.

## Acao
- Nao execute mudancas (edicao de arquivos, comandos destrutivos) sem confirmacao explicita do humano.
- Perguntas do humano nao sao ordens de execucao; responda a pergunta e aguarde instrucao explicita para agir.

### Atalho: "configure este repo"

- Se o humano pedir explicitamente "configure este repo" (ou equivalente), isso conta como confirmacao para executar o bootstrap.
- Comando canonico:

```bash
bash ./scripts/opencode-link --yes
```

## Configuracao Global via Links Simbolicos

- Este repo `opencode-config` e o fonte de verdade das configs globais do OpenCode.
- Para o OpenCode enxergar estes arquivos de forma global, usamos links simbolicos a partir de `~/.config/opencode`.

Padrao de links (exemplo neste ambiente WSL):

```bash
mkdir -p ~/.config/opencode

ln -s /mnt/c/Users/<usr>/Projetos/opencode-config/AGENTS.md \
      ~/.config/opencode/AGENTS.md

ln -s /mnt/c/Users/<usr>/Projetos/opencode-config/agents \
      ~/.config/opencode/agents

ln -s /mnt/c/Users/<usr>/Projetos/opencode-config/opencode.json \
      ~/.config/opencode/opencode.json

ln -s /mnt/c/Users/<usr>/Projetos/opencode-config/skills \
      ~/.config/opencode/skills

ln -s /mnt/c/Users/<usr>/Projetos/opencode-config/scripts \
      ~/.config/opencode/scripts
```

- Assim voce mantem estas configs versionadas em um repo Git separado (`opencode-config`), mas o OpenCode continua lendo tudo a partir de `~/.config/opencode`.

## Imagens e diagramas

- Quando o humano pedir para criar, visualizar ou converter imagens, diagramas, fluxogramas ou similares:
   - Se o pedido envolver SVG (fornecido pelo humano ou gerado pelo agente):
      - Envie o SVG completo via stdin para a skill `svg-to-image` (`~/.config/opencode/scripts/opencode-svgtoimage`).
      - Leia o JSON de resposta.
      - Use o campo `markdown` diretamente na resposta ao humano para exibir a imagem.
   - Nao tente converter SVG em PNG manualmente; sempre prefira a skill `svg-to-image`.

## Skills disponiveis

- svg-to-image
   - Converte um SVG recebido via stdin em PNG salvo em `/tmp`.
   - Implementacao: script `~/.config/opencode/scripts/opencode-svgtoimage`.
   - Saida: JSON com `imagePath` (caminho do PNG) e `markdown` (`![](<caminho_png>)`).
   - Agentes devem usar esta skill sempre que o humano pedir para criar ou converter imagens/diagramas baseados em SVG.
  
## MCPs


## Pesquisa Web

### REGRA PRINCIPAL: Sempre use MCP Crawl4AI para pesquisas na web

Quando o usuário pedir para fazer uma pesquisa, busca, ou obter informações da internet (ex: "pesquise sobre X", "busque informações de Y", "qual o preço de Z", "notícias sobre W", "melhores produtos de 2025/2026"), você **DEVE**:

1. **Usar APENAS o MCP Crawl4AI** - Nunca usar websearch, curl, ou outras ferramentas de busca
2. **Ferramentas disponíveis do Crawl4AI:**
  - `crawl4ai_md` - Extrai conteúdo de páginas web em formato markdown (MAIS IMPORTANTE)
  - `crawl4ai_html` - Retorna HTML processado da página
  - `crawl4ai_screenshot` - Captura screenshot PNG da página
  - `crawl4ai_pdf` - Gera PDF da página
  - `crawl4ai_crawl` - Crawl de múltiplas URLs retornando JSON
  - `crawl4ai_execute_js` - Executa JavaScript na página

#### Se o MCP Crawl4AI não estiver disponível

Se ao tentar usar o MCP Crawl4AI você receber erro (container não está rodando ou MCP não configurado), você **DEVE** perguntar ao usuário:

> "O MCP Crawl4AI não está disponível. Deseja que eu instale e configure agora? Isso vai baixar o Docker e configurar o ambiente automaticamente."

Se o usuário confirmar, execute o script de instalação:
```bash
bash ~/.config/opencode/scripts/crawl4ai/install-crawl4ai-mcp.sh
```

#### Exemplos de como FAZER

| Prompt do usuário | O que fazer |
|-----------------|-------------|
| "Pesquise as melhores canetas 3D de 2025" | Usar `crawl4ai_md` para buscar a página |
| "Qual o preço do 3Doodler?" | Usar `crawl4ai_md` no site oficial |
| "Busque notícias sobre IA" | Usar `crawl4ai_md` em sites de notícias |
| "Qual o preço médio de um notebook?" | Usar `crawl4ai_md` em sites de preços |

#### Exemplos de como NÃO FAZER

- **NÃO** use `websearch` - Esta ferramenta está DESATIVADA para pesquisas
- **NÃO** use `curl` ou `bash` para buscar páginas web
- **NÃO** responda com conhecimento do modelo quando o usuário pedir pesquisa

#### Quando perguntar ao usuário

**NÃO** pergunte se o usuário quer usar pesquisa web - simplesmente USE o MCP Crawl4AI.

A única exceção é se você não tiver certeza se o usuário quer uma pesquisa ou não - neste caso, pode perguntar uma vez, mas depois use sempre o MCP.

#### Como usar o Crawl4AI

Para buscar informações sobre um produto, primeiro encontre o site relevante e use `crawl4ai_md` com a URL.

Exemplo de fluxo:
1. Identificar URL relevante (ex: site oficial do produto)
2. Usar `crawl4ai_md` com a URL
3. Analisar o conteúdo retornado em markdown
4. Responder com as informações obtidas

Se o usuário informar sites específicos, como youtube, linkedin, etc; tente fazer buscas especificas nos referidos sites adicionalmente à buscas genéricas em motores de busca.  
