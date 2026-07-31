#!/usr/bin/env bash
# configurar-repo.sh
# Entrypoint principal para configurar o repo opencode-config.
# Orquestra: deps (WSL), adapters de plataforma e MCPs globais.
#
# Uso: ./scripts/bootstrap_repo/configurar-repo.sh [--yes]

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd "${script_dir}/../.." && pwd -P)"

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
  2. Executa o adapter Copilot CLI
  3. Executa o adapter OpenCode
  4. Instala MCPs e ferramentas globais (crawl4ai, codebase-memory)

Uso:
  ./scripts/bootstrap_repo/configurar-repo.sh [--yes] [--quiet]

Opcoes:
  --yes      Nao pede confirmacao
  --quiet    Suprime mensagens de progresso
  --help     Mostra esta ajuda

Variaveis de ambiente:
  OPENCODE_SKIP_DEPS=1           Pula instalacao de dependencias
  OPENCODE_SKIP_COPILOT_ADAPTER=1 Pula o adapter Copilot CLI
  OPENCODE_SKIP_OPENCODE_ADAPTER=1 Pula o adapter OpenCode
  OPENCODE_SKIP_SKILL_SYNC=1     Pula sincronizacao de skills upstream
  OPENCODE_SKIP_CRAWL4AI=1       Pula configuracao do MCP crawl4ai
  OPENCODE_SKIP_CODEBASE_MEMORY=1 Pula configuracao do MCP codebase-memory
EOF
      exit 0
      ;;
    *) echo "Opcao desconhecida: $1" >&2; exit 2 ;;
  esac
  shift
done

say()  { [ "$quiet" -eq 0 ] && printf '%s\n' "$*" || true; }
warn() { printf '%s\n' "$*" >&2; }

# Scripts auxiliares
wsl_deps_script="${script_dir}/wsl-install-deps.sh"
copilot_adapter_script="${repo_root}/adapters/copilot-cli/copilot-cli-adapter.sh"
opencode_adapter_script="${repo_root}/adapters/opencode/opencode-adapter.sh"
crawl4ai_script="${repo_root}/scripts/crawl4ai/install-crawl4ai-mcp.sh"
codebase_memory_script="${repo_root}/scripts/codebase-memory/install.sh"

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
# Fase 2: Executar adapter Copilot CLI
# ---------------------------------------------------------------------------
run_copilot_adapter() {
  if [ "${OPENCODE_SKIP_COPILOT_ADAPTER:-0}" = "1" ]; then
    say "SKIP: Adapter Copilot CLI (OPENCODE_SKIP_COPILOT_ADAPTER=1)"
    return 0
  fi

  check_script "$copilot_adapter_script" "copilot-cli-adapter.sh" || return 1

  section "Configurando Copilot CLI"

  local args=()
  [ "$assume_yes" -eq 1 ] && args+=("--yes")

  bash "$copilot_adapter_script" "${args[@]}"
}

# ---------------------------------------------------------------------------
# Fase 3: Executar adapter OpenCode
# ---------------------------------------------------------------------------
run_opencode_adapter() {
  if [ "${OPENCODE_SKIP_OPENCODE_ADAPTER:-0}" = "1" ]; then
    say "SKIP: Adapter OpenCode (OPENCODE_SKIP_OPENCODE_ADAPTER=1)"
    return 0
  fi

  check_script "$opencode_adapter_script" "opencode-adapter.sh" || return 1

  section "Configurando OpenCode"

  local args=()
  [ "$assume_yes" -eq 1 ] && args+=("--yes")

  bash "$opencode_adapter_script" "${args[@]}"
}

# ---------------------------------------------------------------------------
# Fase 4: Instalar MCPs
# ---------------------------------------------------------------------------
run_crawl4ai() {
  if [ "${OPENCODE_SKIP_CRAWL4AI:-0}" = "1" ]; then
    say "SKIP: MCP crawl4ai (OPENCODE_SKIP_CRAWL4AI=1)"
    return 0
  fi

  check_script "$crawl4ai_script" "install-crawl4ai-mcp" || return 1

  section "Instalando MCP crawl4ai"

  bash "$crawl4ai_script"
}

run_codebase_memory() {
  if [ "${OPENCODE_SKIP_CODEBASE_MEMORY:-0}" = "1" ]; then
    say "SKIP: MCP codebase-memory (OPENCODE_SKIP_CODEBASE_MEMORY=1)"
    return 0
  fi

  check_script "$codebase_memory_script" "codebase-memory/install" || return 1

  section "Instalando MCP codebase-memory"

  local args=()
  [ "$assume_yes" -eq 1 ] && args+=("--yes")
  [ "$quiet" -eq 1 ] && args+=("--quiet")

  bash "$codebase_memory_script" "${args[@]}"
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
  run_copilot_adapter || warn "Falha no adapter Copilot CLI (continuando...)"
  run_opencode_adapter || warn "Falha no adapter OpenCode (continuando...)"
  run_crawl4ai || warn "Falha na instalacao do crawl4ai (continuando...)"
  run_codebase_memory || warn "Falha na instalacao do codebase-memory (continuando...)"

  section "Concluido"
  say "Repositorio configurado."
  say ""
  say "Verifique:"
  say "  ls -la ~/.config/opencode/"
  say "  ls -la ~/.copilot/agents/ 2>/dev/null || true"
  say "  ls -la ~/.copilot/instructions/ 2>/dev/null || true"
  say "  ls -la ~/.copilot/skills/ 2>/dev/null || true"
  say "  cat ~/.config/mcp/servers.json 2>/dev/null || true"
  say ""
}

main
