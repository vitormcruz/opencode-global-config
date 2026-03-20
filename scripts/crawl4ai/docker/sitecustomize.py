# sitecustomize.py - Auto-import do sanitizador MCP
# Colocado em site-packages para ser importado automaticamente pelo Python.
try:
    import sanitize_mcp  # noqa: F401
except Exception:
    pass  # Nao quebrar o startup se o patch falhar
