#!/usr/bin/env bash
# opencode-md-export
# Converte arquivo Markdown para docx, pptx ou xlsx via Pandoc.
# Entrada: JSON via stdin
# Saida:   1 linha JSON via stdout
set -euo pipefail

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
die_json() {
  local msg="$1"
  local hint="${2:-}"
  printf '{"ok":false,"engine":"pandoc","artifacts":[],"stdout":"","stderr":"%s","hint":"%s"}\n' \
    "$(printf '%s' "$msg" | sed 's/"/\\"/g')" \
    "$(printf '%s' "$hint" | sed 's/"/\\"/g')"
  exit 0
}

PANDOC_INSTALL_HINT="Ubuntu/WSL: sudo apt-get update && sudo apt-get install -y pandoc | macOS: brew install pandoc | Windows: winget install JohnMacFarlane.Pandoc | Docs: https://pandoc.org/installing.html"

# --------------------------------------------------------------------------
# Verificar pandoc
# --------------------------------------------------------------------------
if ! command -v pandoc >/dev/null 2>&1; then
  die_json "pandoc nao encontrado no PATH" "$PANDOC_INSTALL_HINT"
fi

# --------------------------------------------------------------------------
# Ler JSON do stdin
# --------------------------------------------------------------------------
input="$(cat)"

read_json() {
  local key="$1"
  printf '%s' "$input" | python3 -c "
import sys,json
d=json.load(sys.stdin)
v=d.get('$key')
if v is None:
    sys.exit(0)
if isinstance(v,(dict,list)):
    print(json.dumps(v))
else:
    print(v)
" 2>/dev/null || true
}

source_file="$(read_json source)"
to="$(read_json to)"
output_dir="$(read_json outputDir)"
output_path="$(read_json outputPath)"
template="$(read_json template)"
from_fmt="$(read_json from)"
toc="$(read_json toc)"
metadata_json="$(read_json metadata)"
extra_args_json="$(read_json extraArgs)"

# --------------------------------------------------------------------------
# Validacoes basicas
# --------------------------------------------------------------------------
if [ -z "$source_file" ]; then
  die_json "Campo 'source' e obrigatorio"
fi

if [ -z "$to" ]; then
  die_json "Campo 'to' e obrigatorio (docx | pptx | xlsx)"
fi

case "$to" in
  docx|pptx|xlsx) ;;
  *) die_json "Formato 'to' invalido: '$to'. Use: docx, pptx ou xlsx" ;;
esac

if [ ! -f "$source_file" ]; then
  die_json "Arquivo fonte nao encontrado: $source_file"
fi

# --------------------------------------------------------------------------
# Resolver outputPath
# --------------------------------------------------------------------------
if [ -z "$output_path" ]; then
  if [ -z "$output_dir" ]; then
    timestamp="$(date +%Y%m%d-%H%M%S)"
    output_dir="./out/md-export/${timestamp}"
  fi
  mkdir -p "$output_dir"
  base="$(basename "$source_file" .md)"
  output_path="${output_dir}/${base}.${to}"
fi

# Nao sobrescrever sem --force (checa se esta em extraArgs)
force=0
if printf '%s' "$extra_args_json" | python3 -c "import sys,json; a=json.load(sys.stdin); sys.exit(0 if '--force' in a or '--overwrite' in a else 1)" 2>/dev/null; then
  force=1
fi

if [ -f "$output_path" ] && [ "$force" -eq 0 ]; then
  die_json "Arquivo de saida ja existe: $output_path. Passe extraArgs: [\"--overwrite\"] para sobrescrever." ""
fi

mkdir -p "$(dirname "$output_path")"

# --------------------------------------------------------------------------
# Montar argumentos do pandoc
# --------------------------------------------------------------------------
args=()

# formato de entrada
if [ -n "$from_fmt" ]; then
  args+=("--from=$from_fmt")
else
  args+=("--from=gfm")
fi

# formato de saida
args+=("--to=$to")

# output
args+=("--output=$output_path")

# template (reference-doc)
if [ -n "$template" ]; then
  if [ ! -f "$template" ]; then
    die_json "Template nao encontrado: $template"
  fi
  args+=("--reference-doc=$template")
fi

# toc
if [ "$toc" = "true" ] || [ "$toc" = "True" ] || [ "$toc" = "1" ]; then
  args+=("--toc")
fi

# metadata
if [ -n "$metadata_json" ]; then
  while IFS= read -r kv; do
    args+=("-M" "$kv")
  done < <(python3 -c "
import json,sys
d=json.loads(sys.argv[1])
for k,v in d.items():
    print(f'{k}={v}')
" "$metadata_json" 2>/dev/null || true)
fi

# extra args (exceto --force/--overwrite que sao flags internas)
if [ -n "$extra_args_json" ]; then
  while IFS= read -r arg; do
    case "$arg" in
      --force|--overwrite) continue ;;
      *) args+=("$arg") ;;
    esac
  done < <(python3 -c "
import json,sys
for a in json.loads(sys.argv[1]):
    print(a)
" "$extra_args_json" 2>/dev/null || true)
fi

# arquivo fonte
args+=("$source_file")

# --------------------------------------------------------------------------
# Executar pandoc
# --------------------------------------------------------------------------
stdout_file="$(mktemp)"
stderr_file="$(mktemp)"

trap 'rm -f "$stdout_file" "$stderr_file"' EXIT

pandoc_ok=0
pandoc "${args[@]}" >"$stdout_file" 2>"$stderr_file" && pandoc_ok=1 || pandoc_ok=0

stdout_content="$(cat "$stdout_file")"
stderr_content="$(cat "$stderr_file")"

if [ "$pandoc_ok" -eq 0 ] || [ ! -f "$output_path" ]; then
  printf '{"ok":false,"engine":"pandoc","artifacts":[],"stdout":%s,"stderr":%s,"hint":""}\n' \
    "$(python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$stdout_content")" \
    "$(python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$stderr_content")"
  exit 0
fi

# --------------------------------------------------------------------------
# Saida de sucesso
# --------------------------------------------------------------------------
printf '{"ok":true,"engine":"pandoc","artifacts":[%s],"stdout":%s,"stderr":%s,"hint":""}\n' \
  "$(python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$output_path")" \
  "$(python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$stdout_content")" \
  "$(python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$stderr_content")"
