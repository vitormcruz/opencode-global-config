---
applyTo: "**"
---

Regras gerais de desenvolvimento estão no `AGENTS.md` (lido nativamente).

## Arquitetura MCP no Copilot

O GitHub Copilot suporta MCP nativamente, mas nao e possivel utiliza-lo no ambiente
de uso. Para acessar os servidores MCP configurados neste repo, usamos o wrapper CLI
`avelino/mcp` instalado em `~/.local/bin/mcp`.

Fluxo de acesso:
  1. Copilot recebe instrucao para usar uma tool MCP
  2. Copilot executa `mcp --list` para descobrir servidores disponiveis
  3. Copilot executa `mcp <servidor> <tool> --arg valor`
  4. O wrapper `mcp` traduz a chamada CLI para protocolo MCP
  5. O servidor MCP responde e o resultado e retornado ao Copilot

Servidores acessiveis via `mcp`:
  - crawl4ai (SSE, localhost:11235)
  - codebase-memory (local process)
  - doctree (local process via bunx)

# Ferramentas MCP via CLI

Use o comando `mcp` para acessar servidores MCP pelo terminal.

## Como usar

1. Descubra o que está disponível: `mcp --list`
2. Chame a ferramenta: `mcp <servidor> <tool> --arg valor`
3. Para argumentos JSON complexos: `mcp <servidor> <tool> --schema`

## Servidor disponível

- `crawl4ai` — crawl e extração de páginas web (localhost:11235)

## Exemplos

```bash
mcp crawl4ai crawl4ai_md --url "https://example.com"
mcp crawl4ai crawl4ai_md --url "https://example.com" > page.md
mcp crawl4ai crawl4ai_md --url "https://example.com" | jq '.markdown'
```

Prefira pipes com `jq` para filtrar saída JSON.

## Ferramentas de Indexação

Este projeto utiliza `codebase-memory-mcp` e `doctree-mcp` como servidores MCP.
O acesso pelo Copilot é feito via CLI `mcp` (avelino/mcp), não por MCP nativo.

### Como usar pelo Copilot

1. Listar servidores disponíveis: `mcp --list`
2. Chamar ferramenta: `mcp <servidor> <tool> --arg valor`
3. Para argumentos JSON complexos: `mcp <servidor> <tool> --schema`

### Servidores disponíveis

- `codebase-memory` — grafo de conhecimento do código-fonte
  - `search_graph` — busca BM25 + semântica no grafo
  - `search_code` — grep aumentado com grafo
  - `trace_path` — rastreia chamadas e dependências
  - `get_code_snippet` — lê fonte de função/classe
  - `query_graph` — consultas Cypher
  - `get_architecture` — visão de arquitetura
  - `detect_changes` — mapeia impacto de git diff

- `doctree` — índice de documentos Markdown
  - `search_documents` — busca full-text BM25
  - `get_tree` — retorna árvore de seções
  - `get_node_content` — lê conteúdo de seção
  - `navigate_tree` — navega seção + filhos

### Skills instaladas (comandos `/` no chat)

As seguintes skills estão disponíveis como comandos de barra no chat do Copilot:

- `/codebase-memory-exploring` — orientação no codebase
- `/codebase-memory-tracing` — cadeias de chamada, impacto
- `/codebase-memory-quality` — dead code, refactor candidates
- `/codebase-memory-reference` — sintaxe das tools, exemplos Cypher
- `/doc-read` — busca estruturada em documentos
- `/doc-write` — escrita no wiki
- `/doc-lint` — auditoria de documentação

Prefira usar as skills acima em vez de grep/glob para exploração de código e
documentos — elas consomem menos tokens e retornam resultados estruturados.
