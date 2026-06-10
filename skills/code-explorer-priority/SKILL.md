---
name: code-explorer-priority
description: >
  REGRA ABSOLUTA: use codebase-memory (search_graph, trace_path,
  query_graph) para buscas em CODIGO e knowledge-rag (search_knowledge,
  get_document) para buscas em DOCUMENTACAO. NUNCA use grep/glob antes de
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
| `knowledge-rag` | Documentacao: workflows, specs, ADRs, agentes, skills, planos | Codigo-fonte, strings em .ts/.py/.go |
| `grep` | Strings literais, erros, configs — SOMENTE fallback | Busca estrutural |
| `glob` | Arquivos por nome/padrao — SOMENTE fallback | Conteudo de arquivos |

## Acesso por Cliente

### OpenCode
Ferramentas MCP sao nativas. Use `search_graph`, `trace_path`,
`search_knowledge`, etc. diretamente.

### GitHub Copilot
Ferramentas MCP NAO sao nativas. Use SEMPRE o CLI wrapper.

Para `codebase-memory`, no Copilot, prefira SEMPRE um unico JSON posicional e
inclua `project` explicitamente nas consultas ao grafo. Nao use `--query`,
`--function_name`, `--qualified_name`, `--repo_path` ou `--project`.

```bash
mcp codebase-memory list_projects
mcp codebase-memory search_graph '{"project":"<nome>","query":"termos"}'
mcp codebase-memory trace_path '{"project":"<nome>","function_name":"Foo"}'
mcp knowledge-rag-opencode-config search_knowledge --query "termos"
mcp knowledge-rag-opencode-config get_document --filepath "./docs/doc.md"
```

NUNCA tente usar search_graph, search_knowledge, etc. como
ferramentas nativas no Copilot — elas nao existem nesse ambiente.

## Passo 0: Confirmar projeto indexado (codebase-memory)

OpenCode: `list_projects`
Copilot: `mcp codebase-memory list_projects`

Anote o nome exato. Se nao estiver indexado:
`mcp codebase-memory index_repository '{"repo_path":"/caminho/absoluto/do/repo"}'`

Para documentacao em `knowledge-rag`, verifique o .env-knowledge-rag:
- Confirme que KNOWLEDGE_RAG_COLLECTIONS esta definido
- Reindexe se necessario: `mcp knowledge-rag-<repo> reindex_documents --force`

## Passo 1: Classificar a busca

| Tipo de busca | Ferramenta |
|---|---|
| Funcao, classe, rota, variavel | `search_graph` |
| Quem chama / quem e chamado | `trace_path` |
| Documentacao, workflow, spec, ADR, agentes | `search_knowledge` |
| Conteudo de funcao/classe especifica | `get_code_snippet` |
| Conteudo de documentacao especifica | `get_document` |
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

### knowledge-rag (DOCUMENTACAO)

1. `search_knowledge(query="<termos>")`
2. Vazio? → `list_documents` para ver documentos indexados
3. Doc esperado nao indexado? → `grep` em `*.md`
4. Indexacao desatualizada? → `reindex_documents(force: true)`

## Passo 3: Navegar resultados

- `search_graph` → `get_code_snippet`
- `trace_path` → siga trilha com `depth=3`
- `search_knowledge` → `get_document` ou `list_documents`
- `get_document` le o documento completo — refine com `search_knowledge` se muito grande
