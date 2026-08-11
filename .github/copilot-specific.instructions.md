---
applyTo: "**"
---

Regras gerais de desenvolvimento estão no `AGENTS.md` (lido nativamente).

## Prioridade de descoberta

### PROIBIÇÕES ABSOLUTAS — ferramentas nativas do Copilot

PROIBIDO usar qualquer uma das ferramentas abaixo para BUSCA ou LEITURA de
arquivos do repositório ANTES de esgotar o `codebase-memory-mcp cli`:

- `list_dir` — PROIBIDO como primeiro passo de descoberta
- `read_file` — PROIBIDO sem saber o caminho exato
- `grep_search` — PROIBIDO antes de tentar `search_graph` ou `search_code`
- `file_search` — PROIBIDO antes de tentar `search_graph`
- `semantic_search` — PROIBIDO antes de tentar `search_graph`

Essas ferramentas só podem ser usadas APÓS o CLI falhar ou retornar projeto não
indexado. Usar qualquer uma delas diretamente é uma VIOLAÇÃO desta regra.

REGRA ABSOLUTA: use `codebase-memory-mcp cli` antes de qualquer ferramenta
nativa. A mesma regra vale para OpenCode no WSL e Copilot no Windows.

### codebase-memory (código e documentação)

Use o CLI para funções, classes, rotas, callers, data flow, arquitetura e
seções de documentos Markdown. No Copilot, use sempre um único argumento JSON
posicional, sem flags como `--query`, `--function_name` ou `--project`.

Fluxo seguro:
1. Execute `codebase-memory-mcp cli list_projects '{}'`.
2. Copie o nome exato do projeto indexado.
3. Passe `{"project":"<nome>", ...}` nas consultas.
4. Use `repo_path` absoluto para indexação.
5. Em `search_code`, use `pattern`, não `query`.

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

### Busca em documentação Markdown

Para buscar seções, use Cypher no `query_graph`:

```bash
codebase-memory-mcp cli query_graph \
  '{"project":"<nome>","query":"MATCH (s:Section) WHERE s.name CONTAINS \"termo\" RETURN s.name, s.file"}'
```

### Recovery obrigatório

Se o CLI retornar `"project not found"`:
1. Execute `codebase-memory-mcp cli list_projects '{}'`.
2. Copie o nome exato do projeto.
3. Retente a consulta com esse nome.
4. Só então use grep/glob se o projeto não estiver indexado.

## CLIs nativos

- `codebase-memory-mcp cli`: busca de código e documentação em ambos os
  ambientes.
- `crwl`: extração web no WSL e no Windows, sem servidor local.

Para extração web, use `crwl` diretamente conforme a skill
`web-research-exa-crawl4ai`; não use transportes ou wrappers de servidor.

### Separação por ambiente

- WSL/Linux: use o OpenCode e os CLIs instalados localmente.
- Windows: use o Copilot CLI e os mesmos CLIs nativos, sem prefixar comandos
  com `wsl`.
- `codebase-memory-mcp cli` é uma execução local do CLI; não configure nem
  inicie um servidor MCP para realizar buscas.

## Comunicação obrigatória do bootstrap

Ao executar o bootstrap como agente, leia e repasse ao humano qualquer bloco
`Orientacao Docling` ou `Comandos manuais pendentes`. Para `Orientacao Docling`,
informe que o download de modelos é opcional, mostre o comando exibido e aguarde
aprovação explícita antes de executá-lo. Para erros TLS/certificado, explique
que o agente precisa confirmar com o humano uma CA PEM ou mirror aprovado;
nunca desative TLS, invente certificados ou oculte a saída do bootstrap.

## Ferramentas nativas como fallback estrito

Use `grep_search`, `file_search`, `read_file`, `list_dir` ou
`semantic_search` SOMENTE após tentar o CLI e executar o recovery de
`list_projects`. Nunca inicie uma investigação sem essa tentativa.
