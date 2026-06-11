---
applyTo: "**"
---

## Codebase-Memory Neste Repo

Este repositorio esta indexado no `codebase-memory`. Use as ferramentas disponiveis
para explorar **codigo e documentacao** em uma unica base de conhecimento.

### Por que codebase-memory unificado?

O `codebase-memory` indexa tanto o codigo-fonte quanto os documentos Markdown do repo.
Arquivos `.md` se tornam nos do tipo `Section`, permitindo buscas semanticas na
documentacao usando as mesmas ferramentas usadas para codigo.

### Ferramentas disponiveis

#### Busca em Codigo
- `search_graph` - Busca hibrida (semantica + BM25) no grafo de codigo
- `trace_path` - Rastreia chamadas e dependencias entre funcoes
- `get_code_snippet` - Obtem codigo de funcao/classe especifica
- `query_graph` - Consultas Cypher personalizadas
- `get_architecture` - Visao geral da arquitetura do projeto

#### Busca em Documentacao (via nos Section)

Documentos Markdown sao indexados como nos `Section`. Para buscar:

```bash
# Buscar secoes que contem termo no nome
mcp codebase-memory query_graph '{"project":"opencode-config","query":"MATCH (s:Section) WHERE s.name CONTAINS \"agente\" RETURN s.file, s.name"}'

# Busca semantica em documentos
mcp codebase-memory search_graph '{"project":"opencode-config","query":"workflow multi-agente"}'
```

### Nome do Projeto

No GitHub Copilot, use o wrapper `mcp`. Nome do projeto:
**`mnt-c-Users-ur5y-Projetos-opencode-config`** (ou descubra com `list_projects`)

### Exemplos de uso

```bash
# Listar projetos indexados
mcp codebase-memory list_projects

# Buscar funcoes relacionadas a agentes
mcp codebase-memory search_graph '{"project":"opencode-config","query":"funcao que gerencia agentes"}'

# Rastrear dependencias
mcp codebase-memory trace_path '{"project":"opencode-config","function_name":"createAgent"}'

# Obter codigo de funcao
mcp codebase-memory get_code_snippet '{"project":"opencode-config","qualified_name":"src.utils.createAgent"}'

# Buscar documentacao sobre workflows
mcp codebase-memory search_graph '{"project":"opencode-config","query":"workflow de curadoria"}'

# Consulta Cypher para documentos
mcp codebase-memory query_graph '{"project":"opencode-config","query":"MATCH (s:Section) WHERE s.file CONTAINS \"workflow\" RETURN s.file, s.name LIMIT 10"}'

# Visao geral da arquitetura
mcp codebase-memory get_architecture '{"project":"opencode-config"}'
```

### Sintaxe importante: JSON posicional unico

No Copilot, sempre use JSON posicional unico (nao flags como `--query`):

✅ Correto:
```bash
mcp codebase-memory search_graph '{"project":"opencode-config","query":"termos"}'
```

❌ Incorreto (falha no wrapper mcp):
```bash
mcp codebase-memory search_graph --query "termos"
```

### Recuperacao de erros

Se `search_graph` retornar "project not found":
1. Execute `mcp codebase-memory list_projects`
2. Copie o nome exato do projeto
3. Re-tente com o nome correto

Se o projeto nao estiver indexado:
```bash
mcp codebase-memory index_repository '{"repo_path":"/mnt/c/Users/ur5y/Projetos/opencode-config"}'
```
