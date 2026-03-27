#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
update-upstream-skill

Atualiza exatamente uma skill atualizavel com base no `UPSTREAM.md`.

Uso:
  ./scripts/skills/update-upstream-skill <skill>

Status possiveis:
  - success
  - already-up-to-date
  - no-clear-update-flow
  - ambiguous-update-flow
  - non-interactive-mode-not-found
  - error
EOF
}

say() {
  printf '%s\n' "$*"
}

restore_upstream_md() {
  if [ -n "${upstream_backup:-}" ] && [ -f "$upstream_backup" ]; then
    cp "$upstream_backup" "$upstream_md"
  fi
}

indent_file() {
  local file_path="$1"
  [ -f "$file_path" ] || return 0

  while IFS= read -r line; do
    say "  $line"
  done < "$file_path"
}

extract_local_script_path() {
  local command="$1"
  local first=""
  local second=""
  local candidate=""

  read -r first second _ <<< "$command"

  case "$first" in
    bash|sh|python|python3)
      candidate="$second"
      ;;
    ./*|scripts/*)
      candidate="$first"
      ;;
    *)
      candidate=""
      ;;
  esac

  if [ -z "$candidate" ]; then
    return 1
  fi

  case "$candidate" in
    /*)
      printf '%s\n' "$candidate"
      ;;
    *)
      printf '%s\n' "$repo_root/$candidate"
      ;;
  esac
}

supports_assume_yes() {
  local command="$1"
  local local_script=""

  if [[ "$command" == *" --yes"* ]]; then
    return 0
  fi

  if ! local_script="$(extract_local_script_path "$command")"; then
    return 1
  fi

  [ -f "$local_script" ] || return 1
  grep -Fq -- '--yes' "$local_script"
}

run_captured() {
  local command="$1"
  local output_file="$2"

  set +e
  (
    cd "$repo_root"
    bash -lc "$command"
  ) >"$output_file" 2>&1
  local exit_code=$?
  set -e

  return "$exit_code"
}

skill_name="${1:-}"

case "$skill_name" in
  --help|-h)
    usage
    exit 0
    ;;
  "")
    usage >&2
    exit 2
    ;;
esac

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd "${script_dir}/../.." && pwd -P)"
skill_dir="${repo_root}/skills/${skill_name}"
upstream_md="${skill_dir}/UPSTREAM.md"
upstream_backup=""

command -v python3 >/dev/null 2>&1 || {
  say "skill: ${skill_name}"
  say "status: error"
  say "summary: python3 nao encontrado; nao foi possivel interpretar o UPSTREAM.md"
  exit 0
}

if [ ! -f "$upstream_md" ]; then
  say "skill: ${skill_name}"
  say "status: no-clear-update-flow"
  say "summary: skill sem UPSTREAM.md; nao e considerada atualizavel"
  exit 0
fi

tmpdir="$(mktemp -d "${TMPDIR:-/tmp}/update-upstream-skill-XXXXXX")"
trap 'rm -rf "$tmpdir"' EXIT

commands_file="$tmpdir/commands.txt"
check_output="$tmpdir/check.log"
update_output="$tmpdir/update.log"
upstream_backup="$tmpdir/UPSTREAM.md.bak"

cp "$upstream_md" "$upstream_backup"

python3 - "$upstream_md" > "$commands_file" <<'PY'
import re
import sys

path = sys.argv[1]

section = False
fence = False
commands = []

with open(path, "r", encoding="utf-8") as fh:
    for raw_line in fh:
        line = raw_line.rstrip("\n")

        if not section and re.match(r"^##\s+Como\s+atualizar\s*$", line):
            section = True
            continue

        if not section:
            continue

        if not fence and re.match(r"^##\s+", line):
            break

        if re.match(r"^```", line):
            fence = not fence
            continue

        cmd = None
        if fence:
            stripped = line.strip()
            if stripped:
                cmd = stripped
        elif line.startswith("    "):
            cmd = line[4:].strip()
        elif line.startswith("\t"):
            cmd = line.lstrip("\t").strip()

        if not cmd:
            continue

        if re.match(r"^(bash|sh|python|python3)\s+", cmd) or cmd.startswith("./") or cmd.startswith("scripts/"):
            commands.append(cmd)

for command in commands:
    print(command)
PY

mapfile -t documented_commands < "$commands_file"

update_candidates=()
check_candidates=()

for command in "${documented_commands[@]}"; do
  if [[ "$command" == *"--check-only"* ]]; then
    check_candidates+=("$command")
  else
    update_candidates+=("$command")
  fi
done

say "skill: ${skill_name}"

if [ "${#update_candidates[@]}" -eq 0 ]; then
  say "status: no-clear-update-flow"
  say "summary: UPSTREAM.md encontrado, mas sem comando de atualizacao claramente identificavel"
  if [ "${#check_candidates[@]}" -gt 0 ]; then
    say "documented_check_command: ${check_candidates[0]}"
  fi
  exit 0
fi

if [ "${#update_candidates[@]}" -gt 1 ]; then
  say "status: ambiguous-update-flow"
  say "summary: UPSTREAM.md possui multiplos comandos candidatos de atualizacao; revisao manual necessaria"
  for command in "${update_candidates[@]}"; do
    say "candidate_update_command: ${command}"
  done
  exit 0
fi

documented_update_command="${update_candidates[0]}"
documented_check_command=""
executed_command=""
check_summary="nao executado"

say "documented_update_command: ${documented_update_command}"

if [ "${#check_candidates[@]}" -gt 0 ]; then
  documented_check_command="${check_candidates[0]}"
  say "documented_check_command: ${documented_check_command}"

  if run_captured "$documented_check_command" "$check_output"; then
    if grep -Fq 'Ja esta atualizado' "$check_output"; then
      check_summary="ja estava atualizada"
      say "status: already-up-to-date"
      say "summary: nenhuma atualizacao necessaria; check-only informou que a skill ja estava atualizada"
      say "check_summary: ${check_summary}"
      say "check_output:"
      indent_file "$check_output"
      exit 0
    fi

    if grep -Fq 'Atualizacao disponivel' "$check_output"; then
      check_summary="ha atualizacao disponivel"
    else
      check_summary="check-only executado com sucesso"
    fi
  else
    check_summary="check-only falhou; update sera tentado mesmo assim"
  fi

  say "check_summary: ${check_summary}"
fi

if [[ "$documented_update_command" == *" --yes"* ]]; then
  executed_command="$documented_update_command"
elif supports_assume_yes "$documented_update_command"; then
  executed_command="${documented_update_command} --yes"
else
  say "status: non-interactive-mode-not-found"
  say "summary: fluxo encontrado, mas nao ha modo nao interativo claramente identificavel para executar com seguranca"
  exit 0
fi

say "executed_command: ${executed_command}"

if run_captured "$executed_command" "$update_output"; then
  say "status: success"
  say "summary: skill atualizada com sucesso"
  say "update_output:"
  indent_file "$update_output"
  exit 0
fi

restore_upstream_md

say "status: error"
say "summary: erro ao executar a atualizacao da skill; UPSTREAM.md restaurado para o estado anterior"
say "update_output:"
indent_file "$update_output"
exit 0
