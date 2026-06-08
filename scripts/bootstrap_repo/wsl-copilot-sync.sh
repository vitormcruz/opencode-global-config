#!/usr/bin/env bash
# wsl-copilot-sync.sh
# Sincroniza configuracoes do opencode-config para GitHub Copilot (WSL).
#
# Uso: ./scripts/bootstrap_repo/wsl-copilot-sync.sh [--yes] [--quiet]

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd "${script_dir}/../.." && pwd -P)"

skills_dir="${HOME}/.copilot/skills"
instructions_dir="${HOME}/.copilot/instructions"
prompts_dir="${HOME}/.vscode-server/data/User/prompts"
windows_user_profile=""
windows_prompts_dir=""
windows_code_user_dir=""
mcp_json="${HOME}/.vscode-server/data/User/mcp.json"
mcp_servers_json="${HOME}/.config/mcp/servers.json"
backup_dir="${HOME}/.config/copilot-backup/$(date +%Y%m%d-%H%M%S)"

assume_yes=0
quiet=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --yes) assume_yes=1 ;;
    --quiet) quiet=1 ;;
    --help|-h)
      cat <<'EOF'
wsl-copilot-sync

Sincroniza configuracoes do opencode-config para GitHub Copilot (WSL).

Uso:
  ./scripts/bootstrap_repo/wsl-copilot-sync.sh [--yes] [--quiet]

Opcoes:
  --yes      Nao pede confirmacao
  --quiet    Suprime saidas detalhadas
  --help     Mostra esta ajuda

O que e sincronizado:
  skills/*/         -> ~/.copilot/skills/
  agents/*.md       -> ~/.vscode-server/data/User/prompts/*.agent.md
  commands/*.md     -> ~/.vscode-server/data/User/prompts/*.prompt.md
  copilot-instrs    -> ~/.copilot/instructions/copilot-specific.instructions.md
  MCPs Copilot (exa,crawl4ai) -> ~/.vscode-server/data/User/mcp.json
  MCPs CLI (crawl4ai,codebase-memory,doctree) -> ~/.config/mcp/servers.json
EOF
      exit 0
      ;;
    *) echo "Opcao desconhecida: $1" >&2; exit 2 ;;
  esac
  shift
done

say() { [[ "$quiet" -eq 0 ]] && printf '%s\n' "$*" || true; }

ensure_dir() {
  mkdir -p "$1"
}

backup_if_exists() {
  local path="$1"
  [[ ! -e "$path" && ! -L "$path" ]] && return 0

  ensure_dir "$backup_dir"

  local base out i
  base="$backup_dir/$(basename "$path")"
  out="$base"
  i=1
  while [[ -e "$out" || -L "$out" ]]; do
    out="${base}.${i}"
    i=$((i + 1))
  done

  cp -a "$path" "$out"
}

write_utf8() {
  local path="$1"
  local content="$2"
  printf '%s' "$content" > "$path"
}

detect_windows_targets() {
  local candidate current_home_name
  current_home_name="$(basename "$HOME")"

  for candidate in "/mnt/c/Users/$current_home_name" "/mnt/c/Users/${USER:-}"; do
    [[ -n "$candidate" ]] || continue
    [[ -d "$candidate/AppData/Roaming/Code/User" ]] || continue
    windows_user_profile="$candidate"
    windows_code_user_dir="$candidate/AppData/Roaming/Code/User"
    windows_prompts_dir="$windows_code_user_dir/prompts"
    return 0
  done

  return 1
}

strip_agent_frontmatter() {
  python3 - <<'PY' "$1"
import pathlib, sys
path = pathlib.Path(sys.argv[1])
content = path.read_text(encoding='utf-8')
lines = content.splitlines()
if not lines or lines[0].strip() != '---':
    print(content, end='')
    raise SystemExit(0)

i = 1
desc = []
in_desc = False
while i < len(lines):
    line = lines[i]
    if line.strip() == '---':
        i += 1
        break
    if line.startswith('description:'):
        desc = [line]
        in_desc = True
    elif in_desc and line.startswith('  '):
        desc.append(line)
    else:
        in_desc = False
    i += 1
body = '\n'.join(lines[i:])
if desc:
    print('---')
    print('\n'.join(desc))
    print('---')
    if body:
      print(body)
else:
    print(content, end='')
PY
}

rewrite_skill_script_refs() {
  local skill_name="$1"
  local skill_dest="$2"
  local skill_md="$skill_dest/SKILL.md"
  [[ -f "$skill_md" ]] || return 0

  python3 - <<'PY' "$repo_root" "$skill_name" "$skill_dest"
import pathlib, re, shutil, sys
repo_root = pathlib.Path(sys.argv[1])
skill_name = sys.argv[2]
skill_dest = pathlib.Path(sys.argv[3])
skill_md = skill_dest / 'SKILL.md'
content = skill_md.read_text(encoding='utf-8')
original = content
scripts_dest = skill_dest / 'scripts'
wsl_base = scripts_dest.as_posix()

for match in re.findall(r'~/.config/opencode/scripts/(\S+)', content):
    src = repo_root / 'scripts' / match
    if src.exists():
        scripts_dest.mkdir(parents=True, exist_ok=True)
        dst = scripts_dest / match
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        content = content.replace(f'~/.config/opencode/scripts/{match}', f'wsl bash {wsl_base}/{match}')

for match in re.findall(r'\./scripts/(\S+)', content):
    src = repo_root / 'skills' / skill_name / 'scripts' / match
    if src.exists():
        scripts_dest.mkdir(parents=True, exist_ok=True)
        dst = scripts_dest / match
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        cmd = f'wsl python {wsl_base}/{match}' if dst.suffix == '.py' else f'wsl bash {wsl_base}/{match}'
        content = content.replace(f'./scripts/{match}', cmd)

if skill_name == 'web-research-exa-crawl4ai':
    content = content.replace('`websearch/Exa`', '`web_search_exa`')
    content = content.replace('websearch/Exa', 'web_search_exa')
    content = content.replace('`websearch`', '`web_search_exa`')
    content = re.sub(r'\bwebsearch\b', 'web_search_exa', content)

if content != original:
    skill_md.write_text(content, encoding='utf-8')
PY
}

sync_skills() {
  say ""
  say "--- Skills ---"
  ensure_dir "$skills_dir"
  local count=0
  local skill_src skill_name skill_md dest
  for skill_src in "$repo_root"/skills/*; do
    [[ -d "$skill_src" ]] || continue
    skill_name="$(basename "$skill_src")"
    skill_md="$skill_src/SKILL.md"
    [[ -f "$skill_md" ]] || continue
    dest="$skills_dir/$skill_name"
    backup_if_exists "$dest"
    rm -rf "$dest"
    cp -a "$skill_src" "$dest"
    rewrite_skill_script_refs "$skill_name" "$dest"
    say "OK    $skill_name"
    count=$((count + 1))
  done
  say "      $count skill(s) sincronizada(s)"
}

sync_agents() {
  say ""
  say "--- Agents ---"
  ensure_dir "$prompts_dir"
  [[ -n "$windows_prompts_dir" ]] && ensure_dir "$windows_prompts_dir"
  local count=0
  local agent_src base_name dest converted
   for agent_src in "$repo_root"/agents/*.md; do
     [[ -f "$agent_src" ]] || continue
     base_name="$(basename "$agent_src" .md)"
     dest="$prompts_dir/$base_name.agent.md"
     backup_if_exists "$dest"
     converted="$(strip_agent_frontmatter "$agent_src")"
     write_utf8 "$dest" "$converted"
    if [[ -n "$windows_prompts_dir" ]]; then
      local win_dest="$windows_prompts_dir/$base_name.agent.md"
      backup_if_exists "$win_dest"
      write_utf8 "$win_dest" "$converted"
    fi
     say "OK    $base_name.agent.md"
     count=$((count + 1))
   done
   say "      $count agent(s) sincronizado(s)"
 }
 
 sync_commands() {
   say ""
   say "--- Commands ---"
   ensure_dir "$prompts_dir"
   [[ -n "$windows_prompts_dir" ]] && ensure_dir "$windows_prompts_dir"
   local count=0
   local cmd_src base_name dest
   for cmd_src in "$repo_root"/commands/*.md; do
     [[ -f "$cmd_src" ]] || continue
     base_name="$(basename "$cmd_src" .md)"
     dest="$prompts_dir/$base_name.prompt.md"
     backup_if_exists "$dest"
     cp "$cmd_src" "$dest"
     if [[ -n "$windows_prompts_dir" ]]; then
       local win_dest="$windows_prompts_dir/$base_name.prompt.md"
       backup_if_exists "$win_dest"
       cp "$cmd_src" "$win_dest"
     fi
     say "OK    $base_name.prompt.md"
     count=$((count + 1))
   done
   say "      $count command(s) sincronizado(s)"
 }
 
 sync_windows_prompt_instructions() {
   [[ -n "$windows_prompts_dir" ]] || return 0
   local source="$repo_root/.github/copilot-specific.instructions.md"
   [[ -f "$source" ]] || return 0
   ensure_dir "$windows_prompts_dir"
   local dest="$windows_prompts_dir/opencode-config.instructions.md"
   backup_if_exists "$dest"
   cp "$source" "$dest"
   say "OK    opencode-config.instructions.md (windows prompts)"
 }
 
 sync_instructions() {
   say ""
   say "--- Instructions ---"
   local source="$repo_root/.github/copilot-specific.instructions.md"
   [[ -f "$source" ]] || {
     say "AVISO .github/copilot-specific.instructions.md nao encontrado"
     return 0
   }
   ensure_dir "$instructions_dir"
   local dest="$instructions_dir/copilot-specific.instructions.md"
   backup_if_exists "$dest"
   cp "$source" "$dest"
   say "OK    copilot-specific.instructions.md (user global)"
   sync_windows_prompt_instructions
 }

 sync_mcp() {
   say "" >&2
   say "--- MCP ---" >&2
   ensure_dir "$(dirname "$mcp_json")"
   backup_if_exists "$mcp_json"
   python3 - <<'PY' "$mcp_json"
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
new_servers = {
    'exa': {
        'command': 'npx',
        'args': ['-y', 'exa-mcp-server'],
    },
    'crawl4ai': {
        'type': 'sse',
        'url': 'http://localhost:11235/mcp/sse',
    },
}
if path.exists():
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        data = {'servers': {}}
else:
    data = {'servers': {}}
servers = data.setdefault('servers', {})
added = []
updated = []
for key, value in new_servers.items():
    if key not in servers:
        servers[key] = value
        added.append(key)
    elif servers[key] != value:
        servers[key] = value
        updated.append(key)
path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps({'added': added, 'updated': updated}))
PY
}

sync_mcp_cli() {
  say "--- MCP CLI ---" >&2
  ensure_dir "$(dirname "$mcp_servers_json")"
  backup_if_exists "$mcp_servers_json"
  python3 - <<'PY' "$mcp_servers_json"
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
new_servers = {
    'crawl4ai': {
        'type': 'sse',
        'url': 'http://localhost:11235/mcp/sse',
    },
    'codebase-memory': {
        'command': 'codebase-memory-mcp',
        'args': [],
    },
    'doctree': {
        'command': 'opencode-doctree-run',
        'args': [],
    },
}
if path.exists():
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        data = {'servers': {}}
else:
    data = {'servers': {}}
servers = data.setdefault('servers', {})
added = []
updated = []
for key, value in new_servers.items():
    if key not in servers:
        servers[key] = value
        added.append(key)
    elif servers[key] != value:
        servers[key] = value
        updated.append(key)
path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps({'added': added, 'updated': updated}))
PY
}

show_plan() {
  detect_windows_targets || true
  local n_skills n_agents n_commands
  n_skills="$(find "$repo_root/skills" -mindepth 1 -maxdepth 1 -type d | while read -r d; do [[ -f "$d/SKILL.md" ]] && printf 'x\n'; done | wc -l)"
  n_agents="$(find "$repo_root/agents" -maxdepth 1 -type f -name '*.md' | wc -l)"
  n_commands="$(find "$repo_root/commands" -maxdepth 1 -type f -name '*.md' | wc -l)"

  say "Repo:         $repo_root"
  say "Skills:       $skills_dir"
  say "Instructions: $instructions_dir"
  say "Prompts:      $prompts_dir"
  say "MCP:          $mcp_json"
  say "MCP CLI:      $mcp_servers_json"
  say ""
  say "Plano:"
  say "  - Copiar $n_skills skill(s) para ~/.copilot/skills/"
  say "  - Converter $n_agents agent(s) para .agent.md"
  say "  - Copiar $n_commands command(s) para .prompt.md"
  say "  - Copiar .github/copilot-specific.instructions.md para ~/.copilot/instructions/"
  say "  - Configurar MCPs Copilot (exa, crawl4ai) em mcp.json"
  say "  - Configurar MCPs CLI (crawl4ai, codebase-memory, doctree) em servers.json"
  if [[ -n "$windows_prompts_dir" ]]; then
    say "  - Espelhar prompts/agents/instructions em $windows_prompts_dir"
  else
    say "  - Windows prompts nao detectado; espelho Windows sera pulado"
  fi
}

confirm() {
  [[ "$assume_yes" -eq 1 ]] && return 0
  if ! [[ -t 0 && -t 1 ]]; then
    echo "Sem TTY para confirmacao; use --yes" >&2
    exit 2
  fi
  printf 'Aplicar estas alteracoes? [y/N] '
  read -r ans || true
  case "$ans" in y|Y|yes|YES) return 0 ;; esac
  say "Cancelado."
  exit 1
}

main() {
  show_plan
  confirm
  sync_skills
  sync_agents
  sync_commands
  sync_instructions
  local mcp_result mcp_cli_result added updated cli_added cli_updated
  mcp_result="$(sync_mcp)"
  mcp_cli_result="$(sync_mcp_cli)"
  added="$(python3 - <<'PY' "$mcp_result"
import json, sys
payload = json.loads(sys.argv[1] or '{}')
print(', '.join(payload.get('added', [])))
PY
)"
  updated="$(python3 - <<'PY' "$mcp_result"
import json, sys
payload = json.loads(sys.argv[1] or '{}')
print(', '.join(payload.get('updated', [])))
PY
)"
  cli_added="$(python3 - <<'PY' "$mcp_cli_result"
import json, sys
payload = json.loads(sys.argv[1] or '{}')
print(', '.join(payload.get('added', [])))
PY
)"
  cli_updated="$(python3 - <<'PY' "$mcp_cli_result"
import json, sys
payload = json.loads(sys.argv[1] or '{}')
print(', '.join(payload.get('updated', [])))
PY
)"
  if [[ -n "$added" || -n "$updated" ]]; then
    say "OK    mcp.json (add: ${added:-nenhum}; update: ${updated:-nenhum})"
  else
    say "OK    mcp.json (sem alteracoes necessarias)"
  fi
  if [[ -n "$cli_added" || -n "$cli_updated" ]]; then
    say "OK    servers.json (add: ${cli_added:-nenhum}; update: ${cli_updated:-nenhum})"
  else
    say "OK    servers.json (sem alteracoes necessarias)"
  fi
  say ""
  say "Pronto."
}

main
