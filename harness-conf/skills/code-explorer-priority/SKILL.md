---
name: code-explorer-priority
description: >
  Ativação condicionada: use esta skill APENAS quando o AGENTS.md do
  repositório indicar codebase-memory na descoberta de código; sem essa
  indicação, não a aplique. Quando ativa, REGRA ABSOLUTA: use o CLI
  codebase-memory-mcp para buscas em CÓDIGO e DOCUMENTAÇÃO; NUNCA use
  grep/glob antes de esgotar o CLI. Se o CLI retornar "project not found",
  execute list_projects e retente. Triggers (quando o repo usa
  codebase-memory): pesquisar, procurar, buscar, encontrar, explorar,
  investigar, search, find, look for, locate, explore, investigate, onde
  está, onde estão, procura, busca, code discovery, how does, como
  funciona.
---

# Descoberta CLI-first

Esta skill vale somente para repositórios cujo `AGENTS.md` indica
codebase-memory na descoberta de código. Fora desse caso, use as
ferramentas de busca padrão da plataforma.

Ao receber QUALQUER pedido de busca nesses repositórios, siga esta ordem.
Nunca pule para grep/glob sem antes esgotar o `codebase-memory-mcp cli`.

## Papel de cada ferramenta

| Ferramenta | Use para | Não use para |
|---|---|---|
| `codebase-memory-mcp cli` | Código, docs, símbolos e arquitetura | Strings soltas |
| `grep` | Strings literais, erros e configs — SOMENTE fallback | Busca estrutural |
| `glob` | Arquivos por nome ou padrão — SOMENTE fallback | Conteúdo de arquivos |

## Invocação do CLI (idêntica em qualquer ambiente)

O comando é o mesmo no WSL e no Windows (no Windows, execute os CLIs sem
prefixo `wsl`): `codebase-memory-mcp cli <tool> '<json>'`. Use sempre um
único argumento JSON posicional, sem flags como `--query`,
`--function_name` ou `--project`:

```bash
codebase-memory-mcp cli list_projects '{}'
codebase-memory-mcp cli index_repository '{"repo_path":"/caminho/absoluto/do/repo"}'
codebase-memory-mcp cli search_graph '{"project":"<nome>","query":"descrição"}'
codebase-memory-mcp cli trace_path '{"project":"<nome>","function_name":"Foo"}'
codebase-memory-mcp cli get_code_snippet '{"project":"<nome>","qualified_name":"pkg.Foo"}'
codebase-memory-mcp cli query_graph '{"project":"<nome>","query":"MATCH ..."}'
codebase-memory-mcp cli search_code '{"project":"<nome>","pattern":"termo"}'
codebase-memory-mcp cli get_architecture '{"project":"<nome>"}'
```

Notas:

- Em `search_code`, use `pattern`, não `query`.
- Em `index_repository`, use `repo_path` absoluto para evitar ambiguidades.
- O CLI é execução local — não configure nem inicie servidor MCP para
  buscas.

## Ordem das ferramentas

1. `search_graph` — localizar função, classe, rota, variável, documento,
   workflow, spec ou ADR pelo nome/padrão.
2. `trace_path` — descobrir quem chama e o que é chamado (chamadores e
   chamadas do símbolo localizado).
3. `get_code_snippet` — ler o conteúdo da função, classe ou seção de
   documento localizada.
4. `query_graph` (Cypher) — padrões complexos multi-entidade e busca em
   documentação (abaixo).
5. `get_architecture` — visão geral da arquitetura antes de detalhar
   símbolos.

## Passo 0: confirmar projeto indexado

Execute `codebase-memory-mcp cli list_projects '{}'` e anote o nome exato.
Passe `{"project":"<nome>", ...}` nas consultas.

Se o CLI retornar `"project not found"`, execute `list_projects`
novamente, confirme o nome exato do projeto indexado e retente a consulta.
Só então caia para grep/glob se o projeto não estiver indexado.

## Busca em documentação

O codebase-memory indexa código e documentação em uma única base: arquivos
Markdown tornam-se nós do tipo `Section`. Para buscar seções, use Cypher no
`query_graph`:

```bash
codebase-memory-mcp cli query_graph \
  '{"project":"<nome>","query":"MATCH (s:Section) WHERE s.name CONTAINS \"termo\" RETURN s.file, s.name"}'
```

## Fallback estrito: grep/glob

grep e glob são fallback SOMENTE para: strings literais, mensagens de erro
e valores de config (grep); arquivos por nome ou padrão (glob). Use-os
apenas após esgotar o CLI — incluindo o recovery de `list_projects`.
Nunca inicie uma investigação por grep/glob em repo com codebase-memory.
