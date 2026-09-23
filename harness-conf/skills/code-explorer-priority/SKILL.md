---
name: code-explorer-priority
description: >
  Use para qualquer pedido de descoberta de código, documentação, símbolos
  ou arquitetura. Detecta o projeto com list_projects; em repo indexado,
  usa o codebase-memory CLI antes de grep/glob; sem índice, usa grep/glob
  após a detecção. Triggers: pesquisar, procurar, buscar, descobrir,
  descoberta, encontrar, localizar, explorar, investigar, search, find,
  look for, locate, explore, investigate, onde está, onde fica, onde estão,
  procura, busca, quem chama, como funciona, code discovery, how does.
---

# Descoberta por detecção

Para qualquer pedido sobre onde algo está, quem chama ou como algo funciona, comece pelo
Passo 0 (`list_projects`). Não comece por `find`, `grep`, `ripgrep` ou `glob`.

REGRA ABSOLUTA: em repo indexado, use o codebase-memory CLI antes de grep/glob. A indicação no
`AGENTS.md` local não substitui a detecção.

- Repo indexado: fluxo CLI-first com o nome exato do projeto retornado.
- Repo não indexado: use grep/glob normalmente. Não invente nome de projeto nem bloqueie a
  descoberta por causa do índice ausente.
- Consulta retornou `project not found`: rode `list_projects` de novo, confirme o nome exato e
  retente. Repo fora da lista: use grep/glob.

## Papel de cada ferramenta

| Ferramenta | Use para | Não use para |
|---|---|---|
| `codebase-memory-mcp cli` | Código, docs, símbolos e arquitetura | Strings soltas |
| `grep` | Strings literais, erros e configs, no fallback | Busca estrutural |
| `glob` | Arquivos por nome ou padrão, no fallback | Conteúdo de arquivos |

## Invocação do CLI

O comando é o mesmo no WSL e no Windows, sem prefixo `wsl` no Windows:
`codebase-memory-mcp cli <tool> '<json>'`. Um único argumento JSON posicional. Sem flags como
`--query`, `--function_name` ou `--project`.

```bash
codebase-memory-mcp cli list_projects '{}'
codebase-memory-mcp cli index_repository '{"repo_path":"/caminho/absoluto/do/repo"}'
codebase-memory-mcp cli search_graph '{"project":"<nome-exato>","name_pattern":".*Foo.*"}'
codebase-memory-mcp cli trace_path '{"project":"<nome-exato>","function_name":"Foo","direction":"inbound"}'
codebase-memory-mcp cli trace_path '{"project":"<nome-exato>","function_name":"Foo","direction":"outbound"}'
codebase-memory-mcp cli get_code_snippet '{"project":"<nome-exato>","qualified_name":"pkg.Foo"}'
codebase-memory-mcp cli query_graph '{"project":"<nome-exato>","query":"MATCH ..."}'
codebase-memory-mcp cli search_code '{"project":"<nome-exato>","pattern":"termo"}'
codebase-memory-mcp cli get_architecture '{"project":"<nome-exato>"}'
```

O CLI é execução local. Não configure nem inicie servidor MCP para buscas.

## Ordem das ferramentas

Depois do Passo 0, em repo indexado:

1. `search_graph`: localiza função, classe, rota, variável, documento, workflow, spec ou ADR por
   nome/padrão.
2. `trace_path`: descobre quem chama o símbolo ou o que ele chama.
3. `get_code_snippet`: lê o conteúdo localizado.
4. `query_graph`: padrões complexos multi-entidade e busca em documentação.
5. `get_architecture`: visão geral antes de detalhar símbolos.

## Passo 0: detectar o projeto indexado

```bash
codebase-memory-mcp cli list_projects '{}'
```

Compare o `root_path` retornado com o caminho absoluto do repo atual. Copie o nome exato do
projeto correspondente. Não traduza, normalize nem invente o valor de `project`.

- Repo atual na lista: está indexado. Siga CLI-first com o nome copiado.
- Repo atual fora da lista: não está indexado. Use grep/glob normalmente para a descoberta; o
  comando extra termina aqui.
- Consulta respondeu `project not found`: rode `list_projects` de novo, confirme o nome e
  retente. Repo fora da lista: use grep/glob.

## Receita anti-erro

| Ferramenta | Parâmetro-chave | Detalhe |
|---|---|---|
| `search_graph` | `name_pattern` | Expressão regular |
| `trace_path` | `function_name` + `direction` | `inbound` chamadores, `outbound` chamadas |
| `get_code_snippet` | `qualified_name` | Forma `pkg.Foo` |
| `query_graph` | `query` | Consulta Cypher |
| `search_code` | `pattern` | use `pattern`, não `query` |
| `get_architecture` | só o projeto | — |

Em `index_repository`, use `repo_path` absoluto para evitar ambiguidades.

### Regras de aspas

- Envolva o JSON inteiro em aspas simples do shell.
- Use aspas duplas nos nomes e valores JSON.
- Não use aspas simples dentro do JSON. Escape aspas duplas internas como `\"`.
- Passe o projeto exatamente como saiu de `list_projects`, sem interpolação de flags ou
  argumentos posicionais adicionais.

## Busca em documentação

O codebase-memory indexa código e documentação numa base única: arquivos Markdown viram nós do
tipo `Section`. Para buscar seções, use Cypher no `query_graph`:

```bash
codebase-memory-mcp cli query_graph \
  '{"project":"<nome-exato>","query":"MATCH (s:Section) WHERE s.name CONTAINS \"termo\" RETURN s.file, s.name"}'
```

## Fallback estrito: grep/glob

Em repo indexado, grep e glob só entram depois do CLI e do recovery de `list_projects`, para
strings literais, mensagens de erro, valores de config ou nomes de arquivo. NUNCA inicie
investigação estrutural com grep/glob em repo indexado.

Em repo não indexado, o fallback é o caminho normal após o Passo 0: grep para strings, mensagens
e configs; glob para nomes e padrões de arquivos.
