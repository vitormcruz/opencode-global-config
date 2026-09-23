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

Para qualquer pedido sobre onde algo está, quem chama ou como algo funciona,
comece a resposta com `codebase-memory-mcp cli list_projects '{}'`. Não comece
com `find`, `grep`, `ripgrep` ou `glob`.

Para localizar quem chama uma função, use `trace_path` com `direction` igual a
`inbound`, depois de confirmar o projeto.

O caminho de descoberta depende do estado de indexação do repo atual. A
indicação no `AGENTS.md` local não substitui essa detecção.

## Regra operacional

REGRA ABSOLUTA: em repo indexado, use o codebase-memory CLI antes de grep/glob.

Se o pedido for de descoberta, a primeira ferramenta e a primeira indicação na
resposta devem ser `codebase-memory-mcp cli list_projects '{}'`. Não proponha
grep/glob antes dessa detecção, mesmo quando não puder executar o CLI.

Quando o pedido exigir localizar código ou documentação:

1. Execute o **Passo 0** para detectar a indexação do repo atual.
2. Se o repo estiver indexado, siga o fluxo CLI-first e use o nome exato do
   projeto retornado pelo CLI.
3. Se o repo não estiver indexado, use grep/glob normalmente. Não invente um
   nome de projeto e não bloqueie a descoberta por causa da ausência do índice.

## Papel de cada ferramenta

| Ferramenta | Use para | Não use para |
|---|---|---|
| `codebase-memory-mcp cli` | Código, docs, símbolos e arquitetura | Strings soltas |
| `grep` | Strings literais, erros e configs, no fallback | Busca estrutural |
| `glob` | Arquivos por nome ou padrão, no fallback | Conteúdo de arquivos |

## Invocação do CLI (idêntica em qualquer ambiente)

O comando é o mesmo no WSL e no Windows, sem prefixo `wsl` no Windows:
`codebase-memory-mcp cli <tool> '<json>'`. Use um único argumento JSON
posicional. Não use flags como `--query`, `--function_name` ou `--project`.

```bash
codebase-memory-mcp cli list_projects '{}'
codebase-memory-mcp cli index_repository '{"repo_path":"/caminho/absoluto/do/repo"}'
codebase-memory-mcp cli search_graph '{"project":"<nome-exato>","name_pattern":".*Foo.*"}'
codebase-memory-mcp cli trace_path '{"project":"<nome-exato>","function_name":"Foo","direction":"inbound"}'
codebase-memory-mcp cli get_code_snippet '{"project":"<nome-exato>","qualified_name":"pkg.Foo"}'
codebase-memory-mcp cli query_graph '{"project":"<nome-exato>","query":"MATCH ..."}'
codebase-memory-mcp cli search_code '{"project":"<nome-exato>","pattern":"termo"}'
codebase-memory-mcp cli get_architecture '{"project":"<nome-exato>"}'
```

Notas:

- Em `search_graph`, use `name_pattern` com uma expressão regular.
- Em `trace_path`, informe `direction` como `inbound` (chamadores) ou
  `outbound` (chamadas).
- Em `search_code`, use `pattern`, não `query`.
- Em `index_repository`, use `repo_path` absoluto para evitar ambiguidades.
- O CLI é execução local. Não configure nem inicie servidor MCP para buscas.

## Ordem das ferramentas

Depois do Passo 0, em repo indexado, siga esta ordem:

1. `search_graph`, para localizar função, classe, rota, variável, documento,
   workflow, spec ou ADR pelo nome/padrão.
2. `trace_path`, para descobrir quem chama o símbolo ou o que ele chama.
3. `get_code_snippet`, para ler o conteúdo localizado.
4. `query_graph`, para padrões complexos multi-entidade e busca em documentação.
5. `get_architecture`, para obter a visão geral antes de detalhar símbolos.

## Passo 0: detectar o projeto indexado

Execute sempre este comando antes de escolher outra ferramenta:

```bash
codebase-memory-mcp cli list_projects '{}'
```

Compare o `root_path` retornado com o caminho absoluto do repo atual. Copie o
nome exato do projeto correspondente. Não traduza, normalize nem invente o
valor de `project`.

- Se o repo atual aparecer, ele está indexado. Use o CLI-first e passe o nome
  copiado em todas as chamadas seguintes.
- Se o repo atual não aparecer, ele não está indexado. Use grep/glob normalmente
  para a descoberta. O comando extra termina no Passo 0.
- Se uma consulta retornar `project not found`, execute `list_projects` de novo,
  confirme o nome exato e retente. Se o repo não aparecer, use grep/glob.

## Receita anti-erro

Use estes templates prontos. Substitua somente os placeholders e preserve os
parâmetros mostrados:

- `search_graph` recebe `name_pattern`, que é uma expressão regular:
  `codebase-memory-mcp cli search_graph '{"project":"<nome-exato>","name_pattern":".*Foo.*"}'`
- `trace_path` recebe `direction`, com `inbound` para chamadores ou `outbound`
  para chamadas:
  `codebase-memory-mcp cli trace_path '{"project":"<nome-exato>","function_name":"Foo","direction":"inbound"}'`
  `codebase-memory-mcp cli trace_path '{"project":"<nome-exato>","function_name":"Foo","direction":"outbound"}'`
- `get_code_snippet` recebe o símbolo em `qualified_name`:
  `codebase-memory-mcp cli get_code_snippet '{"project":"<nome-exato>","qualified_name":"pkg.Foo"}'`
- `query_graph` recebe uma consulta Cypher no parâmetro `query`:
  `codebase-memory-mcp cli query_graph '{"project":"<nome-exato>","query":"MATCH ..."}'`
- `search_code` recebe texto ou regex no parâmetro `pattern`, nunca `query`:
  `codebase-memory-mcp cli search_code '{"project":"<nome-exato>","pattern":"termo"}'`
- `get_architecture` recebe apenas o projeto:
  `codebase-memory-mcp cli get_architecture '{"project":"<nome-exato>"}'`

### Regras de aspas

- Envolva o JSON inteiro em aspas simples do shell.
- Use aspas duplas nos nomes e valores JSON.
- Não use aspas simples dentro do JSON. Escape aspas duplas internas como `\"`.
- Passe o projeto exatamente como saiu de `list_projects`, sem interpolação de
  flags ou argumentos posicionais adicionais.

## Busca em documentação

O codebase-memory indexa código e documentação em uma única base: arquivos
Markdown tornam-se nós do tipo `Section`. Para buscar seções, use Cypher no
`query_graph`:

```bash
codebase-memory-mcp cli query_graph \
  '{"project":"<nome-exato>","query":"MATCH (s:Section) WHERE s.name CONTAINS \"termo\" RETURN s.file, s.name"}'
```

## Fallback estrito: grep/glob

Em repo indexado, grep e glob só entram depois do CLI e do recovery de
`list_projects`, para strings literais, mensagens de erro, valores de config ou
nomes de arquivo. Nunca inicie uma investigação estrutural com grep/glob em
repo indexado.

Em repo não indexado, o fallback é o caminho normal após o Passo 0. Use grep
para strings, mensagens e configs, e glob para nomes ou padrões de arquivos.
