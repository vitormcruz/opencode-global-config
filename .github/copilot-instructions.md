Regras gerais de desenvolvimento estão no `AGENTS.md` (lido nativamente).

# Ferramentas MCP via CLI

Use o comando `mcp` para acessar servidores MCP pelo terminal.

## Como usar

1. Descubra o que está disponível: `mcp --list`
2. Chame a ferramenta: `mcp call <servidor> <tool> --arg valor`
3. Para argumentos JSON complexos, veja o schema: `mcp call <servidor> <tool> --schema`

## Servidor disponível

- `crawl4ai` — crawl e extração de páginas web (localhost:11235)

## Exemplos

```bash
mcp call crawl4ai crawl4ai_md --url "https://example.com"
mcp call crawl4ai crawl4ai_md --url "https://example.com" > page.md
mcp call crawl4ai crawl4ai_md --url "https://example.com" | jq '.markdown'
```

Prefira pipes com `jq` para filtrar saída JSON.
