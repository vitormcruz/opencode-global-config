#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
list-updatable

Lista, em ordem alfabetica, as skills atualizaveis deste repo.

Uso:
  ./scripts/skills/list-updatable

Criterio:
  - considera apenas skills com `skills/<nome>/UPSTREAM.md`
EOF
}

case "${1:-}" in
  --help|-h)
    usage
    exit 0
    ;;
  "") ;;
  *)
    echo "Opcao desconhecida: $1" >&2
    usage >&2
    exit 2
    ;;
esac

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd "${script_dir}/../.." && pwd -P)"

shopt -s nullglob

for upstream_md in "${repo_root}"/skills/*/UPSTREAM.md; do
  [ -f "$upstream_md" ] || continue
  basename "$(dirname "$upstream_md")"
done | LC_ALL=C sort
