---
name: code-explorer-priority
description: >
  REGRA ABSOLUTA: use codebase-memory-mcp cli para buscas em CÓDIGO e
  DOCUMENTAÇÃO. NUNCA use grep/glob antes de esgotar o CLI. Se o CLI retornar
  "project not found", execute list_projects e retente. Triggers: pesquisar,
  procurar, buscar, encontrar, explorar, investigar, search, find, look for,
  locate, explore, investigate, onde está, onde estão, procura, busca, code
  discovery, how does, como funciona.
---

# Descoberta CLI-first

Ao receber QUALQUER pedido de busca, siga esta ordem. Nunca pule para
grep/glob sem antes esgotar o `codebase-memory-mcp cli`.

## Papel de cada ferramenta

| Ferramenta | Use para | Não use para |
|---|---|---|
| `codebase-memory-mcp cli` | Código, docs, símbolos e arquitetura | Strings soltas |
| `grep` | Strings literais, erros e configs — SOMENTE fallback | Busca estrutural |
| `glob` | Arquivos por nome ou padrão — SOMENTE fallback | Conteúdo de arquivos |

## Acesso por Cliente

### OpenCode

No OpenCode, execute o CLI nativo no WSL:
`codebase-memory-mcp cli <tool> '<json>'`.

### GitHub Copilot

No Copilot, execute o mesmo CLI nativo no Windows:
`codebase-memory-mcp cli <tool> '<json>'`.

Exemplos:

```bash
codebase-memory-mcp cli list_projects '{}'
codebase-memory-mcp cli search_graph '{"project":"<nome>","query":"termos"}'
codebase-memory-mcp cli trace_path '{"project":"<nome>","function_name":"Foo"}'
codebase-memory-mcp cli query_graph '{"project":"<nome>","query":"MATCH ..."}'
```

## Passo 0: confirmar projeto indexado

Execute `codebase-memory-mcp cli list_projects '{}'` e anote o nome exato.
Se o CLI retornar `"project not found"`, use `list_projects` novamente,
confirme o projeto e retente a consulta.

O codebase-memory indexa código e documentação em uma única base. Documentos
Markdown tornam-se nós do tipo `Section`.

## Passo 1: classificar a busca

| Tipo de busca | Ferramenta |
|---|---|
| Função, classe, rota ou variável | `search_graph` |
| Quem chama ou é chamado | `trace_path` |
| Documento, workflow, spec, ADR ou agente | `search_graph` ou `query_graph` |
| Conteúdo de função ou classe | `get_code_snippet` |
| Conteúdo de documento específico | `get_code_snippet` após localizar |
| Padrão complexo multi-entidade | `query_graph` |
| Visão geral da arquitetura | `get_architecture` |
| String literal ou mensagem de erro | `grep` somente após esgotar o CLI |
| Arquivo por nome | `glob` somente após esgotar o CLI |

### Busca em documentação

Como o codebase-memory indexa Markdown como nós `Section`, use:

```bash
codebase-memory-mcp cli query_graph \
  '{"project":"<nome>","query":"MATCH (s:Section) WHERE s.name CONTAINS \"termo\" RETURN s.file, s.name"}'
```

## Passo 2: executar com recovery

1. Execute `search_graph` com o projeto confirmado.
2. Se houver `"project not found"`, execute
   `codebase-memory-mcp cli list_projects '{}'`.
3. Retente `search_graph` com o nome exato retornado.
4. Se o CLI falhar ou o projeto não estiver indexado, use grep/glob como
   fallback e registre essa limitação.

## Passo 3: navegar resultados

- `search_graph` → `get_code_snippet` para ler o símbolo localizado.
- `trace_path` → siga a trilha de chamadas até o limite necessário.
- `query_graph` → refine a consulta Cypher quando houver muitas entidades.
- `get_architecture` → use para uma visão geral antes de detalhar símbolos.
