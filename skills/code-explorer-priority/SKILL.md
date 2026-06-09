---
name: code-explorer-priority
description: >
  REGRA ABSOLUTA: use codebase-memory (search_graph, trace_path,
  query_graph) para buscas em CODIGO e doctree (search_documents,
  get_tree) para buscas em DOCUMENTACAO. NUNCA use grep/glob antes de
  esgotar as ferramentas MCP. Se search_graph falhar com "project not
  found", chame list_projects e re-tente. No Copilot, use SEMPRE o CLI
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
| `codebase-memory` | Codigo: funcoes, classes, rotas, callers, arquitetura | Documentacao, strings soltas |
| `doctree` | Documentacao: workflows, specs, ADRs, agentes, skills, planos | Codigo-fonte, strings em .ts/.py/.go |
| `grep` | Strings literais, erros, configs — SOMENTE fallback | Busca estrutural |
| `glob` | Arquivos por nome/padrao — SOMENTE fallback | Conteudo de arquivos |

## Acesso por Cliente

### OpenCode
Ferramentas MCP sao nativas. Use `search_graph`, `trace_path`,
`doctree_search_documents`, etc. diretamente.

### GitHub Copilot
Ferramentas MCP NAO sao nativas. Use SEMPRE o CLI wrapper.

Para `codebase-memory`, no Copilot, prefira SEMPRE um unico JSON posicional e
inclua `project` explicitamente nas consultas ao grafo. Nao use `--query`,
`--function_name`, `--qualified_name`, `--repo_path` ou `--project`.

```bash
mcp codebase-memory list_projects
mcp codebase-memory search_graph '{"project":"<nome>","query":"termos"}'
mcp codebase-memory trace_path '{"project":"<nome>","function_name":"Foo"}'
mcp doctree search_documents --query "termos"
mcp doctree get_tree --doc_id "<id>"
```

NUNCA tente usar search_graph, doctree_search_documents, etc. como
ferramentas nativas no Copilot — elas nao existem nesse ambiente.

## Passo 0: Confirmar projeto indexado (codebase-memory)

OpenCode: `list_projects`
Copilot: `mcp codebase-memory list_projects`

Anote o nome exato. Se nao estiver indexado:
`mcp codebase-memory index_repository '{"repo_path":"/caminho/absoluto/do/repo"}'`

## Passo 1: Classificar a busca

| Tipo de busca | Ferramenta |
|---|---|
| Funcao, classe, rota, variavel | `search_graph` |
| Quem chama / quem e chamado | `trace_path` |
| Documentacao, workflow, spec, ADR, agentes | `doctree_search_documents` |
| Conteudo de funcao/classe especifica | `get_code_snippet` |
| Padrao complexo multi-entidade | `query_graph` |
| Visao geral da arquitetura | `get_architecture` |
| String literal, mensagem de erro | `grep` (so depois de esgotar MCP) |
| Arquivo por nome | `glob` (so depois de esgotar MCP) |

## Passo 2: Executar com recovery

### codebase-memory (CODIGO)

1. `search_graph(project="<nome>", query="<descricao>")`
2. "project not found"? → `list_projects` → retentar
3. Vazio? → reformular termos da busca
4. Ainda vazio? → `search_code`
5. Em `search_code`, use `pattern`, nao `query`
6. So entao → `grep`

### doctree (DOCUMENTACAO)

1. `doctree_search_documents(query="<termos>")`
2. Vazio? → `doctree_list_documents` para ver docs indexados
3. Doc esperado nao indexado? → `grep` em `*.md`

## Passo 3: Navegar resultados

- `search_graph` → `get_code_snippet`
- `trace_path` → siga trilha com `depth=3`
- `doctree_search_documents` → `get_tree` → `navigate_tree`
