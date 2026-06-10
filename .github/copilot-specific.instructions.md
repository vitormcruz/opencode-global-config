---
applyTo: "**"
---

Regras gerais de desenvolvimento estão no `AGENTS.md` (lido nativamente).

## Prioridade de Descoberta

REGRA ABSOLUTA: use codebase-memory e knowledge-rag antes de grep/glob.
NUNCA use ferramentas MCP nativas no Copilot — sempre o CLI `mcp`.

### codebase-memory (CODIGO)

Use para funcoes, classes, rotas, callers, data flow, arquitetura.

No GitHub Copilot, para `codebase-memory`, prefira SEMPRE um unico argumento
JSON posicional. Nao use sintaxe com flags como `--query`, `--function_name`,
`--qualified_name`, `--repo_path` ou `--project`, pois ela falha neste
ambiente com o wrapper `mcp`.

Fluxo seguro:
1. Rode `mcp codebase-memory list_projects`
2. Copie o nome exato do projeto indexado
3. Passe `{"project":"<nome>", ...}` nas tools que consultam o grafo
4. Para indexacao, use `repo_path` absoluto
5. Em `search_code`, use `pattern`, nao `query`

```bash
mcp codebase-memory list_projects
mcp codebase-memory index_repository '{"repo_path":"/caminho/absoluto/do/repo"}'
mcp codebase-memory search_graph '{"project":"<nome>","query":"descricao"}'
mcp codebase-memory trace_path '{"project":"<nome>","function_name":"Foo"}'
mcp codebase-memory get_code_snippet '{"project":"<nome>","qualified_name":"pkg.Foo"}'
mcp codebase-memory query_graph '{"project":"<nome>","query":"MATCH ..."}'
mcp codebase-memory search_code '{"project":"<nome>","pattern":"termo"}'
mcp codebase-memory get_architecture '{"project":"<nome>"}'
```

### knowledge-rag (DOCUMENTACAO)

Use para workflows, specs, ADRs, agentes, skills, planos, docs Markdown.

Use a instruction local por repo em `.github/copilot-knowledge-rag.instructions.md`,
gerada pelo fluxo `commands/index-codebase.md`, para descobrir o nome exato da
entrada MCP deste projeto em `~/.config/mcp/servers.json`.

```bash
# Buscar documentos
mcp <knowledge-rag-do-repo> search_knowledge '{"query": "termos", "max_results": 5}'

# Obter documento completo
mcp <knowledge-rag-do-repo> get_document '{"filepath": "docs/workflow.md"}'

# Listar documentos
mcp <knowledge-rag-do-repo> list_documents
mcp <knowledge-rag-do-repo> list_documents '{"category": "docs"}'

# Estatisticas
mcp <knowledge-rag-do-repo> get_index_stats

# Reindexar (após mudanças)
mcp <knowledge-rag-do-repo> reindex_documents '{"force": true}'
```

### grep/glob (FALLBACK)

Use APENAS quando MCP nao resolve:
- `grep` — strings literais, mensagens de erro, configs
- `glob` — arquivos por nome/padrao

## Arquitetura MCP no Copilot

O GitHub Copilot suporta MCP nativamente, mas nao e possivel utiliza-lo no ambiente
de uso. Para acessar os servidores MCP configurados neste repo, usamos o wrapper CLI
`avelino/mcp` instalado em `~/.local/bin/mcp`.

Fluxo de acesso:
  1. Copilot recebe instrucao para usar uma tool MCP
  2. Copilot executa `mcp --list` para descobrir servidores disponiveis
  3. Copilot executa `mcp <servidor> <tool> '<json>'`
  4. O wrapper `mcp` traduz a chamada CLI para protocolo MCP
  5. O servidor MCP responde e o resultado e retornado ao Copilot

Servidores acessiveis via `mcp`:
  - crawl4ai (SSE, localhost:11235)
  - codebase-memory (local process)
  - knowledge-rag do repo atual (entrada materializada por repo em `servers.json`)

# Ferramentas MCP via CLI

Use o comando `mcp` para acessar servidores MCP pelo terminal.

## Como usar

1. Descubra o que está disponível: `mcp --list`
2. Para `codebase-memory`, use `mcp <servidor> <tool> '<json>'`
3. Para `doctree` e `crawl4ai`, use a sintaxe suportada pelo servidor

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

Este projeto utiliza `codebase-memory-mcp` e `knowledge-rag` como servidores MCP.
O acesso pelo Copilot é feito via CLI `mcp` (avelino/mcp), não por MCP nativo.

### Como usar pelo Copilot

1. Listar servidores disponíveis: `mcp --list`
2. Em `codebase-memory`, chamar a tool com JSON posicional único
3. Em `knowledge-rag`, usar a sintaxe suportada pelo servidor

### Servidores disponíveis

- `codebase-memory` — grafo de conhecimento do código-fonte
  - `search_graph` — busca BM25 + semântica no grafo
  - `search_code` — grep aumentado com grafo
  - `trace_path` — rastreia chamadas e dependências
  - `get_code_snippet` — lê fonte de função/classe
  - `query_graph` — consultas Cypher
  - `get_architecture` — visão de arquitetura
  - `detect_changes` — mapeia impacto de git diff

- `knowledge-rag` — índice de documentos Markdown
  - `search_knowledge` — busca híbrida semântica + BM25 + reranking
  - `get_document` — obtém documento completo por filepath
  - `list_documents` — lista documentos indexados
  - `list_categories` — lista categorias disponíveis
  - `get_index_stats` — estatísticas do índice
  - `reindex_documents` — reindexa documentos (force, full_rebuild)
  - `add_document` — adiciona novo documento
  - `update_document` — atualiza documento existente
  - `remove_document` — remove documento
  - `add_from_url` — adiciona documento de URL
  - `search_similar` — busca documentos semanticamente similares
  - `evaluate_retrieval` — avalia qualidade da busca

A entrada concreta de `knowledge-rag` depende do repo atual e deve ser obtida na
instruction local `.github/copilot-knowledge-rag.instructions.md`.

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
