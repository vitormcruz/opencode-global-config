---
applyTo: "**"
---

Regras gerais de desenvolvimento estão no `AGENTS.md` (lido nativamente).

## Prioridade de Descoberta

REGRA ABSOLUTA: use codebase-memory e doctree antes de grep/glob.
NUNCA use ferramentas MCP nativas no Copilot — sempre o CLI `mcp`.

### codebase-memory (CODIGO)

Use para funcoes, classes, rotas, callers, data flow, arquitetura.

```bash
mcp codebase-memory search_graph --query "descricao"
mcp codebase-memory trace_path --function_name "Foo"
mcp codebase-memory get_code_snippet --qualified_name "pkg.Foo"
mcp codebase-memory query_graph --query "MATCH ..."
mcp codebase-memory get_architecture
```

### doctree (DOCUMENTACAO)

Use para workflows, specs, ADRs, agentes, skills, planos, docs Markdown.

```bash
mcp doctree search_documents --query "termos"
mcp doctree get_tree --doc_id "<id>"
mcp doctree navigate_tree --doc_id "<id>" --node_id "<id>"
mcp doctree get_node_content --doc_id "<id>" --node_ids '["<id>"]'
```

### grep/glob (FALLBACK)

Use APENAS quando MCP nao resolve:
- `grep` — strings literais, mensagens de erro, configs
- `glob` — arquivos por nome/padrao

### Wrapper doctree

O script `scripts/doctree/doctree-run.sh` e um wrapper que faz source de
`.env-doctree` do projeto e executa `bunx doctree-mcp`. Ele permite indexar
multiplas pastas (`docs/`, `agents/`, `skills/`, `plan/`) com pesos diferentes.

Para usa-lo via MCP, use o comando `doctree-run` ou o caminho completo do
script. Para configura-lo em `~/.config/mcp/servers.json`, aponte
`doctree.command` para `doctree-run` em vez de `bunx doctree-mcp`.

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
- `/code-explorer-priority` — tutorial de descoberta MCP-first

Prefira usar as skills acima em vez de grep/glob para exploração de código e
documentos — elas consomem menos tokens e retornam resultados estruturados.
