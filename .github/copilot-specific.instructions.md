---
applyTo: "**"
---

Regras gerais de desenvolvimento estão no `AGENTS.md` (lido nativamente).

## Prioridade de Descoberta

### PROIBICOES ABSOLUTAS — Ferramentas Nativas do Copilot

PROIBIDO usar qualquer uma das ferramentas abaixo para BUSCA ou LEITURA de
arquivos do repositorio ANTES de esgotar as ferramentas MCP:

- `list_dir` — PROIBIDO como primeiro passo de descoberta
- `read_file` — PROIBIDO sem antes saber o caminho exato via MCP
- `grep_search` — PROIBIDO antes de tentar `search_graph` ou `search_code`
- `file_search` — PROIBIDO antes de tentar `search_graph`
- `semantic_search` — PROIBIDO antes de tentar `search_graph`

Essas ferramentas so podem ser usadas APOS o MCP falhar ou retornar projeto
nao indexado. Usar qualquer uma delas diretamente e uma VIOLACAO desta regra.

REGRA ABSOLUTA: use codebase-memory antes de qualquer ferramenta nativa.
NUNCA use ferramentas MCP nativas no Copilot — sempre o CLI `mcp`.

### codebase-memory (CODIGO + DOCUMENTACAO)

Use para funcoes, classes, rotas, callers, data flow, arquitetura E secoes de
documentos Markdown (arquivos .md sao indexados como nos do tipo Section).

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

### Busca em Documentacao (Markdown)

Para buscar em arquivos .md (workflows, specs, ADRs, skills), use `query_graph`
com Cypher para consultar nos do tipo `Section`:

```bash
# Busca por titulos de secoes
mcp codebase-memory query_graph '{
  "project": "<nome>",
  "query": "MATCH (s:Section) WHERE s.name CONTAINS \"termo\" RETURN s.name, s.file"
}'

# Busca por conteudo de secoes
mcp codebase-memory query_graph '{
  "project": "<nome>",
  "query": "MATCH (s:Section) WHERE s.content CONTAINS \"workflow\" RETURN s.name, s.file, s.content LIMIT 20"
}'
```

### Ferramentas Nativas (FALLBACK ESTRITO)

Use SOMENTE se o codebase-memory nao estiver disponivel apos tentativa de indexacao:
1. `mcp codebase-memory list_projects` — projeto nao encontrado?
2. `mcp codebase-memory index_repository '{"repo_path":"/caminho/absoluto"}'` — tente indexar
3. So se a indexacao falhar ou o servidor nao responder, use:
   - `grep_search` / `grep` — strings literais, mensagens de erro, configs
   - `file_search` / `glob` — arquivos por nome/padrao
   - `read_file` — apenas com caminho ja conhecido/confirmado
   - `list_dir` — apenas para confirmar estrutura
   - `semantic_search` — nunca como substituto de `search_graph`

NUNCA inicie uma investigacao com ferramentas nativas sem antes tentar indexar.

## Arquitetura MCP no Copilot

O GitHub Copilot suporta MCP nativamente, mas nao e possivel utiliza-lo no ambiente
de uso. Para acessar as ferramentas configuradas neste repo, usamos os CLIs nativos
instalados em user-space.

Fluxo de acesso:
  1. Copilot recebe instrucao para usar uma tool MCP
  2. Copilot executa `mcp --list` para descobrir servidores disponiveis
  3. Copilot executa `mcp <servidor> <tool> '<json>'`
  4. O wrapper `mcp` traduz a chamada CLI para protocolo MCP
  5. O servidor MCP responde e o resultado e retornado ao Copilot

Servidores acessiveis via `mcp`:
  - crawl4ai (SSE, localhost:11235)
  - codebase-memory (local process)

# Ferramentas MCP via CLI

Use o comando `mcp` para acessar servidores MCP pelo terminal.

## Como usar

1. Descubra o que esta disponivel: `mcp --list`
2. Para `codebase-memory`, use `mcp <servidor> <tool> '<json>'`
3. Para `crawl4ai`, use a sintaxe suportada pelo servidor

## Servidor disponivel

- `crawl4ai` — crawl e extracao de paginas web (localhost:11235)

## Exemplos

```bash
mcp crawl4ai crawl4ai_md --url "https://example.com"
mcp crawl4ai crawl4ai_md --url "https://example.com" > page.md
mcp crawl4ai crawl4ai_md --url "https://example.com" | jq '.markdown'
```

Prefira pipes com `jq` para filtrar saida JSON.

## Ferramentas de Indexacao

Este projeto utiliza `codebase-memory-mcp` como servidor MCP.
O acesso pelo Copilot e feito diretamente pelos CLIs nativos, nao por MCP nativo.

### Como usar pelo Copilot

1. Listar servidores disponiveis: `mcp --list`
2. Chamar a tool com JSON posicional unico

### Servidor disponivel

- `codebase-memory` — grafo de conhecimento do codigo-fonte e documentacao
  - `search_graph` — busca BM25 + semantica no grafo
  - `search_code` — grep aumentado com grafo
  - `trace_path` — rastreia chamadas e dependencias
  - `get_code_snippet` — le fonte de funcao/classe
  - `query_graph` — consultas Cypher (incluindo secoes de .md)
  - `get_architecture` — visao de arquitetura
  - `detect_changes` — mapeia impacto de git diff
