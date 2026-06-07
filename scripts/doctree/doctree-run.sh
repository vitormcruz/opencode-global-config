#!/usr/bin/env bash
# scripts/doctree/run.sh
# Wrapper generico para doctree-mcp com suporte a .env-doctree por projeto.
# Descobre a raiz do projeto via .git walk-up, source .env-doctree se existir,
# exec bunx doctree-mcp.
#
# Uso: opencode-doctree-run (symlink em ~/.local/bin)

set -euo pipefail

# Descobre raiz do projeto (walk-up a partir do CWD ate encontrar .git)
PROJECT_ROOT="${OPENCODE_WORKDIR:-$(pwd)}"
while [ "$PROJECT_ROOT" != "/" ]; do
  if [ -d "${PROJECT_ROOT}/.git" ]; then
    break
  fi
  PROJECT_ROOT="$(dirname "$PROJECT_ROOT")"
done

# Source .env-doctree especifico do projeto (se existir)
if [ -f "${PROJECT_ROOT}/.env-doctree" ]; then
  set -a
  # shellcheck disable=SC1091
  source "${PROJECT_ROOT}/.env-doctree"
  set +a
fi

# Fallback: indexa apenas docs/ do projeto
export DOCS_ROOT="${DOCS_ROOT:-${PROJECT_ROOT}/docs}"

exec bunx doctree-mcp
