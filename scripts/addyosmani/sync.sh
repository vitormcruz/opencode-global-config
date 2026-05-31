#!/usr/bin/env bash
# sync - Importa/atualiza as 12 skills do addyosmani/agent-skills
# Uso: ./scripts/addyosmani/sync [--yes] [--check-only]
set -euo pipefail

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd -P)/sync-common.sh"
# shellcheck source=../lib/sync-common.sh
source "$LIB"

UPSTREAM_REPO="https://github.com/addyosmani/agent-skills.git"
UPSTREAM_BRANCH="main"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
SKILLS_DIR="$REPO_ROOT/skills"
TMPDIR_WORK=""
UPSTREAM_DIR=""

# Mapa skill → arquivo de referência (raiz do repo upstream → references/ local)
declare -A SKILL_REFS=(
  ["test-driven-development"]="testing-patterns.md"
  ["security-and-hardening"]="security-checklist.md"
  ["performance-optimization"]="performance-checklist.md"
  ["frontend-ui-engineering"]="accessibility-checklist.md"
)

# 12 skills a sincronizar
SKILLS=(
  "test-driven-development"
  "code-review-and-quality"
  "code-simplification"
  "security-and-hardening"
  "documentation-and-adrs"
  "debugging-and-error-recovery"
  "git-workflow-and-versioning"
  "spec-driven-development"
  "planning-and-task-breakdown"
  "api-and-interface-design"
  "performance-optimization"
  "frontend-ui-engineering"
)

usage() {
  cat <<'EOF'
sync - Sincroniza 12 skills addyosmani com o upstream

Uso:
  ./scripts/addyosmani/sync [--yes] [--check-only]

Opcoes:
  --yes          Nao pede confirmacao
  --check-only   Apenas verifica se ha atualizacoes (nao copia nada)
  --help         Mostra esta ajuda

O que faz:
  1. Clona o repo upstream em diretorio temporario
  2. Valida que a licenca ainda e MIT (aborta se nao for)
  3. Para cada skill, copia corpo upstream para skills/<nome>/
     - NAO sobrescreve SKILL.md se ja existir
  4. Copia references/ upstream para skills/<nome>/references/
     (apenas as 4 skills com referencias 1:1)
  5. Registra metadados em UPSTREAM.md de cada skill
EOF
}

trap sync_cleanup EXIT

sync_parse_args "$@" || { [ $? -eq 1 ] && { usage; exit 0; } || { usage >&2; exit 2; }; }
sync_require_git
sync_confirm "Isso vai sincronizar 12 skills do upstream: $UPSTREAM_REPO
SKILL.md existentes NAO serao sobrescritos."
sync_clone_upstream "$UPSTREAM_REPO" "$UPSTREAM_BRANCH"
sync_validate_mit_license "$UPSTREAM_DIR"
sync_capture_metadata "$UPSTREAM_DIR"
sync_exit_if_check_only "scripts/addyosmani/sync"

# --- Sincroniza cada skill ---
for skill in "${SKILLS[@]}"; do
  UPSTREAM_SKILL="$UPSTREAM_DIR/skills/$skill"
  LOCAL_SKILL="$SKILLS_DIR/$skill"

  if [ ! -d "$UPSTREAM_SKILL" ]; then
    info "AVISO: skill '$skill' nao encontrada no upstream, pulando."
    continue
  fi

  info "Sincronizando: $skill"
  sync_copy_skill_md "$UPSTREAM_SKILL" "$LOCAL_SKILL"

  # Copia references/ 1:1 se esta skill tiver uma
  if [ -n "${SKILL_REFS[$skill]+_}" ]; then
    ref_file="${SKILL_REFS[$skill]}"
    UPSTREAM_REF="$UPSTREAM_DIR/references/$ref_file"
    if [ -f "$UPSTREAM_REF" ]; then
      mkdir -p "$LOCAL_SKILL/references"
      cp "$UPSTREAM_REF" "$LOCAL_SKILL/references/$ref_file"
      info "  Copiado references/$ref_file"
    else
      info "  AVISO: references/$ref_file nao encontrado no upstream"
    fi
  fi

  # Gera/atualiza UPSTREAM.md
  cat > "$LOCAL_SKILL/UPSTREAM.md" <<UPSTREAMEOF
# Metadados do Upstream

repositorio: https://github.com/addyosmani/agent-skills
branch: main
commit: ${UPSTREAM_SHA}
data_commit: ${UPSTREAM_DATE}
sincronizado_em: ${SYNC_DATE}

## Arquivos sincronizados

- skills/${skill}/SKILL.md  (corpo — copiado apenas na criacao inicial)
UPSTREAMEOF

  if [ -n "${SKILL_REFS[$skill]+_}" ]; then
    echo "- references/${SKILL_REFS[$skill]}" >> "$LOCAL_SKILL/UPSTREAM.md"
  fi

  cat >> "$LOCAL_SKILL/UPSTREAM.md" <<'UPSTREAMEOF'

## Nao sincronizado

- SKILL.md  (versao adaptada para OpenCode - mantenha manualmente)

## Como atualizar

Execute a partir da raiz do repo:

    bash scripts/addyosmani/sync

Para verificar se ha atualizacoes sem sincronizar:

    bash scripts/addyosmani/sync --check-only

## Licenca

MIT License - Copyright (c) Addy Osmani
https://github.com/addyosmani/agent-skills/blob/main/LICENSE
UPSTREAMEOF

done

info ""
info "Sincronizacao concluida com sucesso!"
info "  ${#SKILLS[@]} skills processadas"
info "  Commit upstream: $UPSTREAM_SHA"
