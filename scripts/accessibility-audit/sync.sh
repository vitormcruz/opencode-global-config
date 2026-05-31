#!/usr/bin/env bash
# sync - Importa/atualiza a skill accessibility-audit do upstream
# Upstream: sickn33/antigravity-awesome-skills
# Uso: ./scripts/accessibility-audit/sync [--yes] [--check-only]
set -euo pipefail

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd -P)/sync-common.sh"
# shellcheck source=../lib/sync-common.sh
source "$LIB"

UPSTREAM_REPO="https://github.com/sickn33/antigravity-awesome-skills.git"
UPSTREAM_BRANCH="main"
UPSTREAM_SKILL_PATH="skills/accessibility-compliance-accessibility-audit"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
LOCAL_SKILL="$REPO_ROOT/skills/accessibility-audit"
TMPDIR_WORK=""
UPSTREAM_DIR=""

usage() {
  cat <<'EOF'
sync - Sincroniza skill accessibility-audit com o upstream

Uso:
  ./scripts/accessibility-audit/sync [--yes] [--check-only]

Opcoes:
  --yes          Nao pede confirmacao
  --check-only   Apenas verifica se ha atualizacoes (nao copia nada)
  --help         Mostra esta ajuda

O que faz:
  1. Clona o repo upstream em diretorio temporario
  2. Valida que a licenca e MIT (aborta se nao for)
  3. Copia resources/implementation-playbook.md para skills/accessibility-audit/
  4. NAO sobrescreve SKILL.md (versao adaptada localmente)
  5. Atualiza UPSTREAM.md com metadados do commit
EOF
}

trap sync_cleanup EXIT

sync_parse_args "$@" || { [ $? -eq 1 ] && { usage; exit 0; } || { usage >&2; exit 2; }; }
sync_require_git
sync_confirm "Isso vai sincronizar skill accessibility-audit do upstream: $UPSTREAM_REPO
SKILL.md existente NAO sera sobrescrito."
sync_clone_upstream "$UPSTREAM_REPO" "$UPSTREAM_BRANCH"
sync_validate_mit_license "$UPSTREAM_DIR"
sync_capture_metadata "$UPSTREAM_DIR"
sync_exit_if_check_only "scripts/accessibility-audit/sync"

UPSTREAM_SKILL="$UPSTREAM_DIR/$UPSTREAM_SKILL_PATH"
[ -d "$UPSTREAM_SKILL" ] || die "Path upstream nao encontrado: $UPSTREAM_SKILL_PATH"

# --- Copia recursos ---
mkdir -p "$LOCAL_SKILL/resources"
PLAYBOOK="$UPSTREAM_SKILL/resources/implementation-playbook.md"
if [ -f "$PLAYBOOK" ]; then
  cp "$PLAYBOOK" "$LOCAL_SKILL/resources/implementation-playbook.md"
  info "Copiado resources/implementation-playbook.md"
else
  info "AVISO: implementation-playbook.md nao encontrado no upstream"
fi

sync_copy_skill_md "$UPSTREAM_SKILL" "$LOCAL_SKILL"

# --- Atualiza UPSTREAM.md ---
cat > "$LOCAL_SKILL/UPSTREAM.md" <<UPSTREAMEOF
# Metadados do Upstream

repositorio: https://github.com/sickn33/antigravity-awesome-skills
branch: main
commit: ${UPSTREAM_SHA}
data_commit: ${UPSTREAM_DATE}
sincronizado_em: ${SYNC_DATE}
path_upstream: ${UPSTREAM_SKILL_PATH}/

## Arquivos sincronizados

- resources/implementation-playbook.md

## Nao sincronizado

- SKILL.md  (versao adaptada para OpenCode - mantenha manualmente)

## Como atualizar

Execute a partir da raiz do repo:

    bash scripts/accessibility-audit/sync

Para verificar se ha atualizacoes sem sincronizar:

    bash scripts/accessibility-audit/sync --check-only

## Licenca

MIT License + CC BY 4.0
- MIT: Copyright (c) sickn33/antigravity-awesome-skills
- CC BY 4.0 se aplica ao conteudo das skills
- https://github.com/sickn33/antigravity-awesome-skills/blob/main/LICENSE
UPSTREAMEOF

info "Sincronizacao concluida!"
info "  Commit upstream: $UPSTREAM_SHA"
