#!/usr/bin/env bash
# configurar-repo.sh
# Entrypoint principal para configurar o repo opencode-config.
# Orquestra: deps (wsl), VS Code sync (wsl), e links simbolicos.
#
# Uso: ./scripts/bootstrap_repo/configurar-repo.sh [--yes]

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

assume_yes=${OPENCODE_ASSUME_YES:-0}
quiet=0

while [ $# -gt 0 ]; do
  case "$1" in
    --yes)   assume_yes=1 ;;
    --quiet) quiet=1 ;;
    --help|-h)
      cat <<'EOF'
configurar-repo

Configura o repositorio opencode-config:
  1. Instala dependencias WSL
  2. Configura VS Code Server (prompts, agents, skills)
  3. Cria links simbolicos

Uso:
  ./scripts/bootstrap_repo/configurar-repo.sh [--yes] [--quiet]

Opcoes:
  --yes      Nao pede confirmacao
  --quiet    Suprime mensagens de progresso
  --help     Mostra esta ajuda

Variaveis de ambiente:
  OPENCODE_SKIP_DEPS=1           Pula instalacao de dependencias
  OPENCODE_SKIP_VSCODE_SYNC=1    Pula sincronizacao VS Code Server
  OPENCODE_SKIP_LINKS=1          Pula criacao de links simbolicos
  OPENCODE_SKIP_SKILL_SYNC=1     Pula sincronizacao de skills upstream
  OPENCODE_SKIP_CRAWL4AI=1       Pula configuracao do MCP crawl4ai
  OPENCODE_SKIP_CODEBASE_MEMORY=1 Pula configuracao do MCP codebase-memory
  OPENCODE_SKIP_DOCTREE=1        Pula configuracao do MCP doctree
EOF
      exit 0
      ;;
    *) echo "Opcao desconhecida: $1" >&2; exit 2 ;;
  esac
  shift
done

say()  { [ "$quiet" -eq 0 ] && printf '%s\n' "$*" || true; }
warn() { printf '%s\n' "$*" >&2; }

# Scripts auxiliares encontram-se no mesmo diretorio
wsl_deps_script="${script_dir}/wsl-install-deps.sh"
wsl_vscode_script="${script_dir}/wsl-vscode-sync.sh"
links_script="${script_dir}/opencode-link.sh"

check_script() {
  local path="$1"
  local name="$2"
  if [ ! -x "$path" ]; then
    warn "ERRO: Script nao encontrado ou nao executavel: $path"
    return 1
  fi
}

section() {
  say ""
  say "=== $* ==="
}

# ---------------------------------------------------------------------------
# Fase 1: Instalar dependencias
# ---------------------------------------------------------------------------
run_deps() {
  if [ "${OPENCODE_SKIP_DEPS:-0}" = "1" ]; then
    say "SKIP: Instalacao de dependencias (OPENCODE_SKIP_DEPS=1)"
    return 0
  fi

  check_script "$wsl_deps_script" "wsl-install-deps" || return 1

  section "Instalando dependencias"

  local args=()
  [ "$assume_yes" -eq 1 ] && args+=("--yes")
  [ "$quiet" -eq 1 ] && args+=("--quiet")

  # Exporta flags para que o sub-script as respeite
  OPENCODE_ASSUME_YES="$assume_yes" bash "$wsl_deps_script" "${args[@]}"
}

# ---------------------------------------------------------------------------
# Fase 2: Sincronizar VS Code Server WSL
# ---------------------------------------------------------------------------
run_vscode_sync() {
  if [ "${OPENCODE_SKIP_VSCODE_SYNC:-0}" = "1" ]; then
    say "SKIP: Sincronizacao VS Code Server (OPENCODE_SKIP_VSCODE_SYNC=1)"
    return 0
  fi

  check_script "$wsl_vscode_script" "wsl-vscode-sync.sh" || return 1

  section "Configurando VS Code Server (WSL)"

  say "Sincronizando prompts, agents, skills, mcp.json para ~/.vscode-server/data/User/"

  local args=()
  [ "$assume_yes" -eq 1 ] && args+=("--yes")

  bash "$wsl_vscode_script" "${args[@]}"
}

# ---------------------------------------------------------------------------
# Fase 3: Criar links simbolicos
# ---------------------------------------------------------------------------
run_links() {
  if [ "${OPENCODE_SKIP_LINKS:-0}" = "1" ]; then
    say "SKIP: Criacao de links simbolicos (OPENCODE_SKIP_LINKS=1)"
    return 0
  fi

  check_script "$links_script" "opencode-link" || return 1

  section "Criando links simbolicos"

  local args=()
  [ "$assume_yes" -eq 1 ] && args+=("--yes")

  bash "$links_script" "${args[@]}"
}

# ---------------------------------------------------------------------------
# Main: Orquestra as fases
# ---------------------------------------------------------------------------
main() {
  say ""
  say "╔══════════════════════════════════════════════════════════╗"
  say "║       Configurando repositorio opencode-config           ║"
  say "╚══════════════════════════════════════════════════════════╝"
  say ""

  run_deps || warn "Falha na instalacao de dependencias (continuando...)"
  run_vscode_sync || warn "Falha na sincronizacao VS Code (continuando...)"
  run_links || warn "Falha na criacao de links (continuando...)"

  section "Concluido"
  say "Repositorio configurado."
  say ""
  say "Verifique:"
  say "  ls -la ~/.config/opencode/"
  say "  ls -la ~/.vscode-server/data/User/prompts/ 2>/dev/null || true"
  say ""
  say "Para VS Code Windows (opcional):"
  say "  ./scripts/bootstrap_repo/vscode-sync.ps1"
}

main
