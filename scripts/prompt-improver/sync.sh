#!/usr/bin/env bash
# sync - Importa/atualiza arquivos do upstream ckelsoe/prompt-architect
# Uso: ./scripts/prompt-improver/sync [--yes] [--check-only]
set -euo pipefail

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd -P)/sync-common.sh"
# shellcheck source=../lib/sync-common.sh
source "$LIB"

UPSTREAM_REPO="https://github.com/ckelsoe/prompt-architect.git"
UPSTREAM_BRANCH="main"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../skills/prompt-improver" && pwd -P)"
TMPDIR_WORK=""
UPSTREAM_DIR=""
UPSTREAM_SKILL_DIR=""
COUNT_REFS=0
COUNT_ASSETS=0
COUNT_PY=0

usage() {
  cat <<'EOF'
sync - Sincroniza skill prompt-improver com o upstream

Uso:
  ./scripts/prompt-improver/sync [--yes] [--check-only]

Opcoes:
  --yes          Nao pede confirmacao
  --check-only   Apenas verifica se ha atualizacoes (nao copia nada)
  --help         Mostra esta ajuda

O que faz:
  1. Clona o repo upstream em diretorio temporario
  2. Valida que a licenca ainda e MIT (aborta se nao for)
  3. Localiza a skill upstream compativel (layout v2 ou v3)
  4. Copia references/, assets/, scripts/ e LICENSE
  5. Registra metadados em UPSTREAM.md
  6. NAO sobrescreve SKILL.md (versao adaptada)
EOF
}

resolve_upstream_skill_dir() {
  local base_dir="$1"
  for candidate in \
    "$base_dir/skills/prompt-architect" \
    "$base_dir/prompt-architect"; do
    if [ -d "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

trap sync_cleanup EXIT

sync_parse_args "$@" || { [ $? -eq 1 ] && { usage; exit 0; } || { usage >&2; exit 2; }; }
sync_require_git
sync_confirm "Este script ira sincronizar os arquivos de framework do upstream:
  $UPSTREAM_REPO
Destino: $SKILL_DIR
O SKILL.md adaptado NAO sera sobrescrito."
sync_clone_upstream "$UPSTREAM_REPO" "$UPSTREAM_BRANCH"
sync_validate_mit_license "$UPSTREAM_DIR"

UPSTREAM_SKILL_DIR="$(resolve_upstream_skill_dir "$UPSTREAM_DIR")" || \
  die "Nao encontrei o diretorio da skill upstream. Layout nao reconhecido."
info "Skill upstream localizada em $UPSTREAM_SKILL_DIR"

# Versão via package.json (específico deste upstream)
UPSTREAM_VERSION=""
if [ -f "$UPSTREAM_DIR/package.json" ]; then
  UPSTREAM_VERSION=$(grep '"version"' "$UPSTREAM_DIR/package.json" | head -1 \
    | sed 's/.*"version": *"\([^"]*\)".*/\1/')
fi

sync_capture_metadata "$UPSTREAM_DIR"

# check-only: compara commit atual vs upstream
if [ "${check_only:-0}" -eq 1 ]; then
  UPSTREAM_MD="$SKILL_DIR/UPSTREAM.md"
  if [ -f "$UPSTREAM_MD" ]; then
    CURRENT_COMMIT=$(grep "^commit:" "$UPSTREAM_MD" 2>/dev/null | awk '{print $2}' || echo "desconhecido")
    if [ "$CURRENT_COMMIT" = "$UPSTREAM_SHA" ]; then
      info "Ja esta atualizado (commit $UPSTREAM_SHA)"
    else
      info "Atualizacao disponivel: local=$CURRENT_COMMIT upstream=$UPSTREAM_SHA"
    fi
  else
    info "UPSTREAM.md nao encontrado - sync inicial necessario"
  fi
  exit 0
fi

# --- Copia arquivos (específico deste upstream: refs + assets + scripts + LICENSE) ---
info "Copiando arquivos do upstream ..."

SRC_REFS="$UPSTREAM_SKILL_DIR/references"
DST_REFS="$SKILL_DIR/references"
if [ -d "$SRC_REFS" ]; then
  rm -rf "$DST_REFS"
  cp -r "$SRC_REFS" "$DST_REFS"
  COUNT_REFS=$(find "$DST_REFS" -name "*.md" | wc -l | tr -d ' ')
  info "  references/: $COUNT_REFS arquivos .md copiados"
else
  info "  AVISO: references/ nao encontrado no upstream"
fi

SRC_ASSETS="$UPSTREAM_SKILL_DIR/assets"
DST_ASSETS="$SKILL_DIR/assets"
if [ -d "$SRC_ASSETS" ]; then
  rm -rf "$DST_ASSETS"
  cp -r "$SRC_ASSETS" "$DST_ASSETS"
  COUNT_ASSETS=$(find "$DST_ASSETS" -name "*.txt" | wc -l | tr -d ' ')
  info "  assets/: $COUNT_ASSETS arquivos .txt copiados"
else
  info "  AVISO: assets/ nao encontrado no upstream"
fi

SRC_PY="$UPSTREAM_SKILL_DIR/scripts"
DST_PY="$SKILL_DIR/scripts"
if [ -d "$SRC_PY" ]; then
  rm -rf "$DST_PY"
  cp -r "$SRC_PY" "$DST_PY"
  COUNT_PY=$(find "$DST_PY" -name "*.py" | wc -l | tr -d ' ')
  info "  scripts/: $COUNT_PY scripts Python copiados"
else
  info "  AVISO: scripts/ nao encontrado no upstream"
fi

cp "$UPSTREAM_DIR/LICENSE" "$SKILL_DIR/LICENSE"
info "  LICENSE copiado"

# --- Atualiza UPSTREAM.md ---
info "Atualizando UPSTREAM.md ..."
cat > "$SKILL_DIR/UPSTREAM.md" <<UPSTREAMEOF
# Metadados do Upstream

repositorio: https://github.com/ckelsoe/prompt-architect
branch: $UPSTREAM_BRANCH
versao: $UPSTREAM_VERSION
commit: $UPSTREAM_SHA
data_commit: $UPSTREAM_DATE
sincronizado_em: $SYNC_DATE

## Arquivos sincronizados

- references/frameworks/  ($COUNT_REFS arquivos)
- assets/templates/       ($COUNT_ASSETS arquivos)
- scripts/                ($COUNT_PY scripts Python)
- LICENSE

## Nao sincronizado

- SKILL.md  (versao adaptada para OpenCode - mantenha manualmente)

## Como atualizar

Execute a partir da raiz do repo:

    bash scripts/prompt-improver/sync

Para verificar se ha atualizacoes sem sincronizar:

    bash scripts/prompt-improver/sync --check-only

## Licenca

MIT License - Copyright (c) 2025-2026 prompt-architect contributors
Autoria original: Charles Kelsoe <charles@kelsoe.com>
UPSTREAMEOF

info "Sincronizacao concluida."
info "  Upstream: $UPSTREAM_VERSION @ $UPSTREAM_SHA"
info "  Skill:    $SKILL_DIR"
info ""
info "SKILL.md nao foi alterado. Se houver mudancas relevantes no upstream,"
info "revise o diff e atualize manualmente o SKILL.md se necessario."
