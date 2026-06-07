#!/usr/bin/env bash
# wsl-copilot-sync.sh
# Sincroniza prompts, agents, skills e mcp.json para GitHub Copilot (WSL).
#
# Uso: ./scripts/bootstrap_repo/wsl-copilot-sync.sh [--yes]

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd "${script_dir}/../.." && pwd -P)"

copilot_dir="${HOME}/.vscode-server/data/User"
backup_dir="${HOME}/.vscode-server/data/User/.backups/$(date +%Y%m%d-%H%M%S)"

assume_yes=0
quiet=0

deployed_any=0

while [ $# -gt 0 ]; do
  case "$1" in
    --yes)   assume_yes=1 ;;
    --quiet) quiet=1 ;;
    --help|-h)
      cat <<'EOF'
wsl-copilot-sync

Sincroniza prompts, agents, skills e mcp.json para GitHub Copilot (WSL).

Uso:
  ./scripts/bootstrap_repo/wsl-copilot-sync.sh [--yes] [--quiet]

Opcoes:
  --yes      Nao pede confirmacao
  --quiet    Suprime saidas detalhadas
  --help     Mostra esta ajuda

Destino:
  ~/.copilot/
    prompts/
    agents/
    skills/
    mcp.json
EOF
      exit 0
      ;;
    *) echo "Opcao desconhecida: $1" >&2; exit 2 ;;
  esac
  shift
done

say()  { [ "$quiet" -eq 0 ] && printf '%s\n' "$*" || true; }
warn() { printf '%s\n' "$*" >&2; }

resolve_path() {
  if command -v realpath >/dev/null 2>&1; then
    realpath -m "$1" 2>/dev/null || true
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    python3 - "$1" <<'PY' 2>/dev/null || true
import os,sys
print(os.path.realpath(sys.argv[1]))
PY
    return 0
  fi
  printf '%s\n' "$1"
}

current_target() {
  local dest="$1"
  if [ ! -L "$dest" ]; then
    printf '%s' ""
    return 0
  fi
  local t
  t="$(readlink "$dest" 2>/dev/null || true)"
  if [ -z "$t" ]; then
    printf '%s' ""
    return 0
  fi
  if [ "${t#/}" = "$t" ]; then
    t="$(dirname "$dest")/$t"
  fi
  resolve_path "$t"
}

ensure_dir() {
  mkdir -p "$1"
}

backup_if_exists() {
  local dest="$1"
  if [ ! -e "$dest" ] && [ ! -L "$dest" ]; then
    return 0
  fi

  ensure_dir "$backup_dir"

  local base
  base="$backup_dir/$(basename "$dest")"

  local out="$base"
  local i=1
  while [ $i -lt 100 ]; do
    if [ ! -e "${base}.${i}" ] && [ ! -L "${base}.${i}" ]; then
      out="${base}.${i}"
      break
    fi
    i=$((i + 1))
  done

  mv "$dest" "$out"
  say "BK  $dest -> $out"
}

link_one() {
  local source="$1"
  local dest="$2"

  local src_abs
  src_abs="$(resolve_path "$source")"
  [ -z "$src_abs" ] && src_abs="$source"

  local cur
  cur="$(current_target "$dest")"
  local src_res
  src_res="$(resolve_path "$src_abs")"

  if [ -n "$cur" ] && [ -n "$src_res" ] && [ "$cur" = "$src_res" ]; then
    say "OK  $dest (ja aponta para $src_abs)"
    return 0
  fi

  deployed_any=1
  backup_if_exists "$dest"
  ln -s "$src_abs" "$dest"
  say "LN  $dest -> $src_abs"
}

confirm() {
  if [ "$assume_yes" -eq 1 ]; then
    return 0
  fi

  if ! [ -t 0 ] || ! [ -t 1 ]; then
    echo "Sem TTY para confirmao; use --yes" >&2
    exit 2
  fi

  printf 'Aplicar estas alteracoes em ~/.copilot/? [y/N] '
  read -r ans || true
  case "$ans" in y|Y|yes|YES) return 0 ;; esac
  say "Cancelado."
  exit 1
}

plan() {
  say "Repo:    $repo_root"
  say "Destino: $copilot_dir"
  say "Backup:  $backup_dir"
  say ""
  say "Plano:"

  ensure_dir "$copilot_dir"

  # Criar links simbolicos
  local src dest
  for src in "$repo_root"/prompts "$repo_root"/agents "$repo_root"/skills "$repo_root"/commands; do
    if [ -e "$src" ]; then
      dest="$copilot_dir/$(basename "$src")"
      link_desc="LN  $dest -> $src"

      local abs cur
      abs="$(resolve_path "$src")"
      cur="$(current_target "$dest")"

      if [ -n "$cur" ] && [ -n "$abs" ] && [ "$cur" = "$abs" ]; then
        say "OK  $dest (ja configurado)"
      elif [ -e "$dest" ] || [ -L "$dest" ]; then
        say "BK  $dest (sera backupeado)"
        say "LN  $dest -> $src"
      else
        say "LN  $dest -> $src"
      fi
    fi
  done

  # mcp.json
  local mcp_src="$repo_root/mcp.json"
  local mcp_dest="$copilot_dir/mcp.json"
  if [ -f "$mcp_src" ]; then
    if [ -e "$mcp_dest" ] || [ -L "$mcp_dest" ]; then
        say "CP  $mcp_dest (sera backupeado e substituido)"
    else
        say "CP  $mcp_dest (copiado de $mcp_src)"
    fi
  fi
}

deploy_mcp_json() {
  local mcp_src="$repo_root/mcp.json"
  local mcp_dest="$copilot_dir/mcp.json"

  if [ ! -f "$mcp_src" ]; then
    return 0
  fi

  local cmp_src cmp_dest need_update=1

  if [ -f "$mcp_dest" ]; then
    if cmp -s "$mcp_src" "$mcp_dest" 2>/dev/null; then
      need_update=0
    fi
  fi

  if [ "$need_update" -eq 0 ]; then
    say "OK  mcp.json (identico)"
    return 0
  fi

  deployed_any=1
  backup_if_exists "$mcp_dest"
  cp "$mcp_src" "$mcp_dest"
  say "CP  $mcp_dest"
}

apply() {
  say ""
  say "Aplicando..."

  deployed_any=0

  ensure_dir "$copilot_dir"

  # Links simbolicos
  local src dest
  for src in "$repo_root"/prompts "$repo_root"/agents "$repo_root"/skills "$repo_root"/commands; do
    if [ -e "$src" ]; then
      dest="$copilot_dir/$(basename "$src")"
      link_one "$src" "$dest"
    fi
  done

  # mcp.json (copiado, nao linkado)
  deploy_mcp_json

  if [ "$deployed_any" -eq 1 ]; then
    say ""
    say "Reinicie o Copilot para aplicar as mudancas."
  else
    say ""
    say "Tudo ja estava sincronizado."
  fi
}

main() {
  plan
  confirm
  apply
}

main
