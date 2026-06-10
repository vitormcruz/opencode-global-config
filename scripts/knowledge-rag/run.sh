#!/usr/bin/env bash
# scripts/knowledge-rag/run.sh
# Wrapper para executar o servidor MCP knowledge-rag.
# Descobre a raiz do projeto e le .env-knowledge-rag para configurar collections.
#
# Este script eh chamado pelo avelino/mcp como entrypoint do servidor MCP.

set -euo pipefail

# -----------------------------------------------------------------------------
# Descobrir raiz do projeto
# -----------------------------------------------------------------------------

find_project_root() {
    local current="$PWD"
    while [ "$current" != "/" ]; do
        if [ -d "$current/.git" ] || [ -f "$current/.env-knowledge-rag" ]; then
            echo "$current"
            return 0
        fi
        current="$(dirname "$current")"
    done
    echo "$PWD"
}

PROJECT_ROOT="$(find_project_root)"

# -----------------------------------------------------------------------------
# Ler configuracao do projeto
# -----------------------------------------------------------------------------

ENV_FILE="$PROJECT_ROOT/.env-knowledge-rag"

if [ -f "$ENV_FILE" ]; then
    # Sourceia o arquivo de configuracao
    # shellcheck source=/dev/null
    source "$ENV_FILE"
fi

# -----------------------------------------------------------------------------
# Configurar collections
# -----------------------------------------------------------------------------

# KNOWLEDGE_RAG_COLLECTIONS define multiplas collections no formato:
#   path1:collection1,path2:collection2,...
# Ou via variaveis individuais definidas em .env-knowledge-rag

if [ -n "${KNOWLEDGE_RAG_COLLECTIONS:-}" ]; then
    export KNOWLEDGE_RAG_COLLECTIONS
elif [ -n "${DOCS_ROOTS:-}" ]; then
    # Fallback: converter formato legacy DOCS_ROOTS para KNOWLEDGE_RAG_COLLECTIONS
    # DOCS_ROOTS="./docs:1.0,./agents:0.9,..." -> KNOWLEDGE_RAG_COLLECTIONS
    # Nota: knowledge-rag usa nomes de collection, nao pesos
    _converted=""
    IFS=',' read -ra entries <<< "$DOCS_ROOTS"
    for entry in "${entries[@]}"; do
        path="${entry%%:*}"
        # Extrai nome da pasta como nome da collection
        collection="$(basename "$path")"
        if [ -n "$_converted" ]; then
            _converted="${_converted},${PROJECT_ROOT}/${path}:${collection}"
        else
            _converted="${PROJECT_ROOT}/${path}:${collection}"
        fi
    done
    export KNOWLEDGE_RAG_COLLECTIONS="$_converted"
fi

# -----------------------------------------------------------------------------
# Executar servidor knowledge-rag
# -----------------------------------------------------------------------------

# Verificar se knowledge-rag esta disponivel
if command -v knowledge-rag >/dev/null 2>&1; then
    exec knowledge-rag mcp-server "${@}"
elif [ -x "$HOME/.local/bin/knowledge-rag" ]; then
    exec "$HOME/.local/bin/knowledge-rag" mcp-server "${@}"
else
    echo "ERRO: knowledge-rag nao encontrado no PATH" >&2
    echo "Execute primeiro: pipx install knowledge-rag" >&2
    exit 1
fi
