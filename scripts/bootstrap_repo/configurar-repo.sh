#!/usr/bin/env bash
# configurar-repo.sh
# Entrypoint principal para configurar o repo opencode-config.
# Orquestra: deps (WSL), adapters de plataforma e ferramentas globais.
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
  4. Instala ferramentas globais (codebase-memory CLI)

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
  OPENCODE_SKIP_CODEBASE_MEMORY=1 Pula configuracao do codebase-memory CLI
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

cleanup_legacy_crawl4ai_bashrc() {
  local bashrc_file="${HOME}/.bashrc"
  [ -f "$bashrc_file" ] || return 0

  local cleaned_file
  cleaned_file="$(mktemp)"
  awk '
    /^# Crawl4AI MCP - INICIO$/ { removing=1; next }
    /^# Crawl4AI MCP - FIM$/ { removing=0; next }
    !removing { print }
  ' "$bashrc_file" > "$cleaned_file"
  mv "$cleaned_file" "$bashrc_file"
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

  section "Configurando OpenCode"

  local args=()
  [ "$assume_yes" -eq 1 ] && args+=("--yes")

  if ! command -v python3 >/dev/null 2>&1; then
    warn "ERRO: Python 3 nao encontrado para executar o adapter OpenCode"
    return 1
  fi

  PYTHONPATH="${repo_root}/src${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 -m opencode_config.adapters.opencode \
    "${args[@]}" --repo-root "$repo_root"
}

# ---------------------------------------------------------------------------
# Fase 4: Instalar ferramentas globais
# ---------------------------------------------------------------------------
run_codebase_memory() {
  if [ "${OPENCODE_SKIP_CODEBASE_MEMORY:-0}" = "1" ]; then
    say "SKIP: codebase-memory CLI (OPENCODE_SKIP_CODEBASE_MEMORY=1)"
    return 0
  fi

  check_script "$codebase_memory_script" "codebase-memory/install" || return 1

  section "Instalando codebase-memory CLI"

  local args=()
  [ "$assume_yes" -eq 1 ] && args+=("--yes")
  [ "$quiet" -eq 1 ] && args+=("--quiet")

  bash "$codebase_memory_script" "${args[@]}"
}

# ---------------------------------------------------------------------------
# Main: Orquestra as fases
# ---------------------------------------------------------------------------
main() {
  cleanup_legacy_crawl4ai_bashrc

  say ""
  say "╔══════════════════════════════════════════════════════════╗"
  say "║       Configurando repositorio opencode-config           ║"
  say "╚══════════════════════════════════════════════════════════╝"
  say ""

  run_deps || warn "Falha na instalacao de dependencias (continuando...)"
  run_copilot_adapter || warn "Falha no adapter Copilot CLI (continuando...)"
  run_opencode_adapter || warn "Falha no adapter OpenCode (continuando...)"
  run_codebase_memory || warn "Falha na instalacao do codebase-memory (continuando...)"

  section "Concluido"
  say "Repositorio configurado."
  say ""
  say "Verifique:"
  say "  ls -la ~/.config/opencode/"
  say "  ls -la ~/.copilot/agents/ 2>/dev/null || true"
  say "  ls -la ~/.copilot/instructions/ 2>/dev/null || true"
  say "  ls -la ~/.copilot/skills/ 2>/dev/null || true"
  say ""
}

main
