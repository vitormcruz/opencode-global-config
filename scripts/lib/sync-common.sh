#!/usr/bin/env bash
# scripts/lib/sync-common.sh — funções compartilhadas pelos scripts de sync
# Uso: source "$(dirname "${BASH_SOURCE[0]}")/../lib/sync-common.sh"
#
# Requer que o script chamador defina antes do source:
#   TMPDIR_WORK=""   (será gerenciado pelo cleanup)

# ---------------------------------------------------------------------------
# Utilitários básicos
# ---------------------------------------------------------------------------

die()  { echo "ERRO: $*" >&2; exit 1; }
info() { echo "[sync] $*"; }

# ---------------------------------------------------------------------------
# Cleanup de diretório temporário
# Registre com: trap sync_cleanup EXIT
# ---------------------------------------------------------------------------

sync_cleanup() {
  if [ -n "${TMPDIR_WORK:-}" ] && [ -d "$TMPDIR_WORK" ]; then
    rm -rf "$TMPDIR_WORK"
  fi
}

# ---------------------------------------------------------------------------
# Parse de argumentos padrão: --yes / --check-only / --help
# Uso: sync_parse_args "$@"
# Exporta: assume_yes, check_only; retorna args não reconhecidos via exit 2
# ---------------------------------------------------------------------------

sync_parse_args() {
  assume_yes=0
  check_only=0

  while [ $# -gt 0 ]; do
    case "$1" in
      --yes)        assume_yes=1 ;;
      --check-only) check_only=1 ;;
      --help|-h)    return 1 ;;  # sinaliza: chamar usage e sair
      *) echo "Opcao desconhecida: $1" >&2; return 2 ;;
    esac
    shift
  done
}

# ---------------------------------------------------------------------------
# Confirmação interativa (no-op se assume_yes=1 ou check_only=1)
# Uso: sync_confirm "<mensagem descritiva do que sera feito>"
# ---------------------------------------------------------------------------

sync_confirm() {
  local msg="$1"
  if [ "${check_only:-0}" -eq 1 ] || [ "${assume_yes:-0}" -eq 1 ]; then
    return 0
  fi
  echo ""
  echo "$msg"
  echo ""
  printf "Confirma? [s/N] "
  read -r resp
  case "$resp" in
    [sS]*) ;;
    *) echo "Cancelado."; exit 0 ;;
  esac
}

# ---------------------------------------------------------------------------
# Verifica dependência git
# ---------------------------------------------------------------------------

sync_require_git() {
  command -v git >/dev/null 2>&1 || die "git nao encontrado"
}

# ---------------------------------------------------------------------------
# Clona upstream em diretório temporário
# Uso: sync_clone_upstream <repo_url> <branch>
# Exporta: UPSTREAM_DIR, TMPDIR_WORK
# ---------------------------------------------------------------------------

sync_clone_upstream() {
  local repo="$1"
  local branch="$2"

  TMPDIR_WORK="$(mktemp -d)"
  info "Clonando upstream em $TMPDIR_WORK ..."
  GIT_SSL_NO_VERIFY=true git clone --depth=1 \
    --branch "$branch" \
    "$repo" \
    "$TMPDIR_WORK/upstream" \
    2>&1 | grep -v "^$" || true

  UPSTREAM_DIR="$TMPDIR_WORK/upstream"
  [ -d "$UPSTREAM_DIR" ] || die "Clone falhou"
}

# ---------------------------------------------------------------------------
# Valida que a licença no upstream contém "MIT"
# Uso: sync_validate_mit_license <upstream_dir>
# ---------------------------------------------------------------------------

sync_validate_mit_license() {
  local upstream_dir="$1"
  local license_file="$upstream_dir/LICENSE"

  if [ ! -f "$license_file" ]; then
    die "LICENSE nao encontrado no upstream — abortando por seguranca."
  fi
  if ! grep -qi "MIT" "$license_file"; then
    die "Licenca nao e MIT — abortando por seguranca. Revise manualmente."
  fi
  info "Licenca MIT confirmada."
}

# ---------------------------------------------------------------------------
# Captura metadados do commit upstream
# Uso: sync_capture_metadata <upstream_dir>
# Exporta: UPSTREAM_SHA, UPSTREAM_DATE, SYNC_DATE
# ---------------------------------------------------------------------------

sync_capture_metadata() {
  local upstream_dir="$1"
  UPSTREAM_SHA="$(git -C "$upstream_dir" rev-parse HEAD)"
  UPSTREAM_DATE="$(git -C "$upstream_dir" log -1 --format='%ci' HEAD)"
  SYNC_DATE="$(date -u '+%Y-%m-%d %H:%M UTC')"
  info "Commit upstream: $UPSTREAM_SHA ($UPSTREAM_DATE)"
}

# ---------------------------------------------------------------------------
# Exibe mensagem e sai no modo check-only
# Uso: sync_exit_if_check_only "<script_path_para_hint>"
# ---------------------------------------------------------------------------

sync_exit_if_check_only() {
  local script_hint="$1"
  if [ "${check_only:-0}" -eq 1 ]; then
    echo ""
    echo "Modo check-only — nenhum arquivo foi alterado."
    echo "Para sincronizar: bash $script_hint --yes"
    exit 0
  fi
}

# ---------------------------------------------------------------------------
# Copia SKILL.md apenas se não existir localmente
# Uso: sync_copy_skill_md <upstream_skill_dir> <local_skill_dir>
# ---------------------------------------------------------------------------

sync_copy_skill_md() {
  local upstream_skill="$1"
  local local_skill="$2"

  mkdir -p "$local_skill"
  if [ ! -f "$local_skill/SKILL.md" ]; then
    cp "$upstream_skill/SKILL.md" "$local_skill/SKILL.md"
    info "  Criado SKILL.md (upstream)"
  else
    info "  SKILL.md ja existe — mantendo versao local"
  fi
}
