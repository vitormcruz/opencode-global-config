---
applyTo: "**"
---

## Knowledge-RAG por repo no Copilot

- Neste repo, nao use a entrada global antiga `knowledge-rag`.
- Use a entrada MCP materializada para este projeto em `~/.config/mcp/servers.json`.
- Nome preferencial deste repo: `knowledge-rag-opencode-config`.
- Se essa entrada nao existir e houver somente uma entrada generica `knowledge-rag`, use a generica.

### Ferramentas disponiveis do knowledge-rag:

- `search_knowledge` - Busca hibrida combinando busca semantica, BM25 e reranking por cross-encoder.
  - Args: `query` (obrigatorio), `max_results` (opcional, default: 5), `category` (opcional), `hybrid_alpha` (opcional, default: 0.3)
  - Exemplo: `{"query": "termos de busca", "max_results": 5}`

- `get_document` - Obter conteudo completo de um documento por filepath.
  - Args: `filepath` (obrigatorio)
  - Exemplo: `{"filepath": "docs/workflow.md"}`

- `list_documents` - Listar documentos indexados.
  - Args: `category` (opcional)
  - Exemplo: `{}` ou `{"category": "docs"}`

- `list_categories` - Listar categorias disponiveis com contagem de documentos.
  - Exemplo: `{}`

- `get_index_stats` - Estatisticas do indice (documentos, chunks, cache hit rate).
  - Exemplo: `{}`

- `reindex_documents` - Reindexar documentos.
  - Args: `force` (opcional, smart reindex), `full_rebuild` (opcional, rebuild completo)
  - Exemplo: `{"force": true}` ou `{"full_rebuild": true}`

- `add_document` - Adicionar novo documento.
  - Args: `content` (obrigatorio), `filepath` (obrigatorio), `category` (opcional)
  - Exemplo: `{"content": "# Titulo\\n\\nConteudo", "filepath": "docs/novo.md", "category": "docs"}`

- `update_document` - Atualizar documento existente.
  - Args: `filepath` (obrigatorio), `content` (obrigatorio)
  - Exemplo: `{"filepath": "docs/existente.md", "content": "# Novo conteudo"}`

- `remove_document` - Remover documento.
  - Args: `filepath` (obrigatorio), `delete_file` (opcional, default: false)
  - Exemplo: `{"filepath": "docs/remover.md"}` ou `{"filepath": "docs/remover.md", "delete_file": true}`

- `add_from_url` - Adicionar documento de URL.
  - Args: `url` (obrigatorio), `category` (opcional), `title` (opcional)
  - Exemplo: `{"url": "https://exemplo.com/doc", "category": "docs"}`

- `search_similar` - Buscar documentos semanticamente similares.
  - Args: `filepath` (obrigatorio), `max_results` (opcional, default: 5)
  - Exemplo: `{"filepath": "docs/referencia.md", "max_results": 5}`

- `evaluate_retrieval` - Avaliar qualidade da busca.
  - Args: `test_cases` (obrigatorio, array JSON)
  - Exemplo: `{"test_cases": "[{\"query\": \"termo\", \"expected_filepath\": \"docs/resultado.md\"}]"}`

### Exemplos de uso pelo CLI `mcp`:

```bash
# Buscar conhecimento
mcp knowledge-rag-opencode-config search_knowledge '{"query": "workflow de agentes", "max_results": 5}'

# Obter documento completo
mcp knowledge-rag-opencode-config get_document '{"filepath": "agents/eng-software.md"}'

# Listar documentos por categoria
mcp knowledge-rag-opencode-config list_documents '{"category": "agents"}'

# Reindexar apos alteracoes
mcp knowledge-rag-opencode-config reindex_documents '{"force": true}'
```
