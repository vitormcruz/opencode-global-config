# ==========================================================================
# Dockerfile - Crawl4AI com sanitizador MCP
#
# Resolve problemas de compatibilidade entre o MCP do Crawl4AI e backends
# de API que rejeitam tools com description vazia ou $ref/$defs no schema
# (ex: GitHub Copilot + claude-sonnet-4.5/4.6).
#
# Build:  docker build -t crawl4ai-sanitized:latest .
# Run:    docker run -d -p 11235:11235 crawl4ai-sanitized:latest
# ==========================================================================

FROM unclecode/crawl4ai:latest

# Copia o patch de sanitizacao para /app (mesmo dir do server.py)
COPY sanitize_mcp.py /app/sanitize_mcp.py

# Copia sitecustomize.py para site-packages do Python do sistema
# Isso garante que o patch e importado automaticamente em qualquer
# processo Python (gunicorn workers, scripts, etc.)
COPY sitecustomize.py /usr/local/lib/python3.12/site-packages/sitecustomize.py

# Garante que /app esta no PYTHONPATH (para o import sanitize_mcp funcionar)
ENV PYTHONPATH="/app:${PYTHONPATH}"
