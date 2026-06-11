---
name: code-explorer-priority
description: >
  REGRA ABSOLUTA: use codebase-memory (search_graph, trace_path,
  query_graph) para buscas em CODIGO e DOCUMENTACAO. NUNCA use grep/glob
  antes de esgotar as ferramentas MCP. Se search_graph falhar com "project
  not found", chame list_projects e re-tente. No Copilot, use SEMPRE o CLI
  wrapper `mcp`. Esta skill existe para impedir que voce caia direto em
  grep/glob — carregue-a antes de QUALQUER busca.
  Triggers: pesquisar, procurar, buscar, encontrar, explorar, investigar,
  search, find, look for, locate, explore, investigate, onde esta, onde
  estao, procura, busca, code discovery, how does, como funciona.
---

# Descoberta MCP-First

Ao receber QUALQUER pedido de busca, siga esta ordem. Nunca pule para
grep/glob sem antes esgotar as ferramentas MCP.

## Papel de Cada Ferramenta

| Ferramenta | Use para | Nao use para |
|---|---|---|
| `codebase-memory` | Codigo E Documentacao: funcoes, classes, rotas, callers, arquitetura, workflows, specs, ADRs, agentes | Strings soltas em qualquer lugar |
| `grep` | Strings literais, erros, configs — SOMENTE fallback | Busca estrutural |
| `glob` | Arquivos por nome/padrao — SOMENTE fallback | Conteudo de arquivos |

## Acesso por Cliente

### OpenCode
Ferramentas MCP sao nativas. Use `search_graph`, `trace_path`, etc.
diretamente.

### GitHub Copilot
Ferramentas MCP NAO sao nativas. Use SEMPRE o CLI wrapper.

Para `codebase-memory`, no Copilot, prefira SEMPRE um unico JSON posicional e
inclua `project` explicitamente nas consultas ao grafo. Nao use `--query`,
`--function_name`, `--qualified_name`, `--repo_path` ou `--project`.

```bash
mcp codebase-memory list_projects
mcp codebase-memory search_graph '{"project":"<nome>","query":"termos"}'
mcp codebase-memory trace_path '{"project":"<nome>","function_name":"Foo"}'
# Para buscar em documentos (nos Section):
mcp codebase-memory query_graph '{"project":"<nome>","query":"MATCH (s:Section) WHERE s.name CONTAINS \"termo\" RETURN s"}'
```

NUNCA tente usar search_graph, trace_path, etc. como
ferramentas nativas no Copilot — elas nao existem nesse ambiente.

## Passo 0: Confirmar projeto indexado

OpenCode: `list_projects`
Copilot: `mcp codebase-memory list_projects`

Anote o nome exato. Se nao estiver indexado:
`mcp codebase-memory index_repository '{"repo_path":"/caminho/absoluto/do/repo"}'`

O `codebase-memory` indexa **codigo e documentacao** em uma unica base.
Documentos Markdown se tornam nos do tipo `Section`.

## Passo 1: Classificar a busca

| Tipo de busca | Ferramenta |
|---|---|
| Funcao, classe, rota, variavel | `search_graph` |
| Quem chama / quem e chamado | `trace_path` |
| Documentacao, workflow, spec, ADR, agentes | `search_graph` ou `query_graph` com filtros em Section |
| Conteudo de funcao/classe especifica | `get_code_snippet` |
| Conteudo de documento especifico | `read_file` (apos encontrar via search_graph) |
| Padrao complexo multi-entidade | `query_graph` |
| Visao geral da arquitetura | `get_architecture` |
| String literal, mensagem de erro | `grep` (so depois de esgotar MCP) |
| Arquivo por nome | `glob` (so depois de esgotar MCP) |

### Busca em Documentacao

Como o codebase-memory indexa Markdown como nos `Section`, use Cypher:

```cypher
MATCH (s:Section) WHERE s.name CONTAINS "termo" RETURN s.file, s.name
```

Ou via `search_graph` com descricao semantica:
`mcp codebase-memory search_graph '{"project":"nome","query":"workflow multi-agente"}'`

## Passo 2: Executar com recovery

### codebase-memory (CODIGO + DOCUMENTACAO)

1. `search_graph(project="<nome>", query="<descricao>")`
2. "project not found"? → `list_projects` → retentar
3. Vazio? → reformular termos da busca
4. Para docs: `query_graph` com pattern em Section
5. Em `search_code`, use `pattern`, nao `query`
6. So entao → `grep`

## Passo 3: Navegar resultados

- `search_graph` → `get_code_snippet` ou `read_file`
- `trace_path` → siga trilha com `depth=3`
- `query_graph` → refine pattern Cypher se necessario
- `get_code_snippet` → leia trecho especifico
