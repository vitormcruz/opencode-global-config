#!/usr/bin/env bash
# copilot-cli-adapter.sh
# Sincroniza a fonte canonica com o Copilot CLI.
#
# Uso: ./adapters/copilot-cli/copilot-cli-adapter.sh [--yes] [--quiet]

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd "${script_dir}/../.." && pwd -P)"
dest_root="${DestRoot:-${DEST_ROOT:-$HOME}}"

copilot_dir="${dest_root}/.copilot"
skills_dir="${copilot_dir}/skills"
instructions_dir="${copilot_dir}/instructions"
agents_dir="${copilot_dir}/agents"
backup_dir="${dest_root}/.config/copilot-backup/$(date +%Y%m%d-%H%M%S)"

assume_yes=0
quiet=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --yes) assume_yes=1 ;;
    --dest-root)
      [[ $# -ge 2 ]] || { echo "--dest-root requer um caminho" >&2; exit 2; }
      dest_root="$2"
      copilot_dir="${dest_root}/.copilot"
      skills_dir="${copilot_dir}/skills"
      instructions_dir="${copilot_dir}/instructions"
      agents_dir="${copilot_dir}/agents"
      backup_dir="${dest_root}/.config/copilot-backup/$(date +%Y%m%d-%H%M%S)"
      shift
      ;;
    --quiet) quiet=1 ;;
    --help|-h)
      cat <<'EOF'
copilot-cli-adapter

Sincroniza a fonte canonica deste repositorio com o Copilot CLI.

Uso:
  ./adapters/copilot-cli/copilot-cli-adapter.sh [--yes] [--quiet]

Opcoes:
  --yes      Nao pede confirmacao
  --quiet    Suprime saidas detalhadas
  --dest-root PATH
             Substitui a raiz de destino (usado em testes)
  --help     Mostra esta ajuda

  O que e sincronizado:
   skills/*/         -> ~/.copilot/skills/
  agents/*.md       -> ~/.copilot/agents/*.agent.md
  commands/*.md     -> ~/.copilot/skills/*/SKILL.md
  default-artifacts -> ~/.copilot/agents/default-artifacts/
  copilot-instrs    -> ~/.copilot/instructions/copilot-specific.instructions.md
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

convert_agent_frontmatter() {
  python3 - <<'PY' "$1"
import json, pathlib, re, sys
path = pathlib.Path(sys.argv[1])
content = path.read_text(encoding='utf-8')
lines = content.splitlines()
if not lines or lines[0].strip() != '---':
    print(content, end='')
    raise SystemExit(0)

end = next((i for i in range(1, len(lines)) if lines[i].strip() == '---'), None)
if end is None:
    print(content, end='')
    raise SystemExit(0)

front = lines[1:end]
body = '\n'.join(lines[end + 1:])
description = []
in_description = False
permission = {}
current_permission = None
mode = None
for line in front:
    if re.match(r'^description:', line):
        description = [line]
        in_description = True
        continue
    if in_description and (line.startswith(' ') or not line.strip()):
        description.append(line)
        continue
    in_description = False
    match = re.match(r'^mode:\s*(\S+)', line)
    if match:
        mode = match.group(1)
        continue
    match = re.match(r'^  (edit|bash|webfetch|websearch|task):\s*(.*)$', line)
    if match:
        current_permission = match.group(1)
        value = match.group(2).strip().lower()
        permission[current_permission] = value
        continue
    if current_permission == 'task' and re.match(r'^\s{4}', line):
        permission['task'] = line.strip().lower()

tools = ['read']
if permission.get('edit') == 'allow':
    tools.append('edit')
if permission.get('bash') == 'allow':
    tools.append('execute')
tools.append('search')
if permission.get('webfetch') == 'allow' or permission.get('websearch') == 'allow':
    tools.append('web')
if permission.get('task') and 'allow' in permission['task']:
    tools.append('agent')

if not description:
    description = ['description: Agent OpenCode convertido para Copilot CLI']
print('---')
print('\n'.join(description).rstrip())
print('tools: ' + json.dumps(tools))
if mode == 'subagent':
    print('user-invocable: false')
print('---')
if body:
    print(body)
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

ensure_skill_frontmatter() {
  local skill_name="$1"
  local skill_dest="$2"
  local skill_md="$skill_dest/SKILL.md"
  python3 - <<'PY' "$skill_name" "$skill_md"
import pathlib, re, sys
skill_name = sys.argv[1]
path = pathlib.Path(sys.argv[2])
if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', skill_name) or len(skill_name) > 64:
    raise SystemExit(f'invalid skill name: {skill_name}')
content = path.read_text(encoding='utf-8')
lines = content.splitlines()
if lines and lines[0].strip() == '---':
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == '---'), None)
    if end is None:
        raise SystemExit(f'invalid frontmatter: {path}')
    front = '\n'.join(lines[1:end])
    name_match = re.search(r'^name:\s*(\S+)\s*$', front, re.MULTILINE)
    if name_match and name_match.group(1) != skill_name:
        raise SystemExit(f'skill name does not match directory: {path}')
    if not name_match:
        lines.insert(1, f'name: {skill_name}')
        path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
else:
    paragraph = []
    started = False
    for line in lines:
        if not line.strip():
            if started:
                break
            continue
        if not started and line.lstrip().startswith('#'):
            continue
        started = True
        paragraph.append(line.strip())
    description = ' '.join(paragraph)[:1024] or f'Skill {skill_name}.'
    body = content.rstrip('\n')
    path.write_text(
        f'---\nname: {skill_name}\ndescription: {description}\n---\n\n{body}\n',
        encoding='utf-8',
    )
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
    ensure_skill_frontmatter "$skill_name" "$dest"
    say "OK    $skill_name"
    count=$((count + 1))
  done
  say "      $count skill(s) sincronizada(s)"
}

sync_agents() {
  say ""
  say "--- Agents ---"
  ensure_dir "$agents_dir"
  local count=0
  local agent_src base_name dest converted
  for agent_src in "$repo_root"/agents/*.md; do
    [[ -f "$agent_src" ]] || continue
    base_name="$(basename "$agent_src" .md)"
    dest="$agents_dir/$base_name.agent.md"
    backup_if_exists "$dest"
    converted="$(convert_agent_frontmatter "$agent_src")"
    write_utf8 "$dest" "$converted"
    say "OK    $base_name.agent.md"
    count=$((count + 1))
  done
  say "      $count agent(s) sincronizado(s)"
}

sync_commands_as_skills() {
  say ""
  say "--- Commands ---"
  ensure_dir "$skills_dir"
  local count=0
  local cmd_src base_name dest description
  for cmd_src in "$repo_root"/commands/*.md; do
    [[ -f "$cmd_src" ]] || continue
    base_name="$(basename "$cmd_src" .md)"
    case "$base_name" in
      index-codebase)
        description="Indexa repo no codebase-memory. Ative quando humano pedir index codebase ou indexar repositorio." ;;
      bench-indexing)
        description="Benchmark de indexacao codebase-memory. Ative quando humano pedir bench indexing." ;;
      sync-upstream-skills)
        description="Sincroniza skills com upstream. Ative quando humano pedir sync upstream skills." ;;
      *)
        description="Executa o comando $base_name." ;;
    esac
    dest="$skills_dir/$base_name"
    backup_if_exists "$dest"
    rm -rf "$dest"
    mkdir -p "$dest"
    python3 - "$cmd_src" "$dest/SKILL.md" "$base_name" "$description" <<'PY'
import pathlib, sys
source = pathlib.Path(sys.argv[1])
target = pathlib.Path(sys.argv[2])
name = sys.argv[3]
description = sys.argv[4]
lines = source.read_text(encoding='utf-8').splitlines()
if lines and lines[0].strip() == '---':
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == '---'), None)
    body = lines[end + 1:] if end is not None else lines
else:
    body = lines
target.write_text(
    f'---\nname: {name}\ndescription: {description}\n---\n\n' +
    '\n'.join(body).rstrip() + '\n',
    encoding='utf-8',
)
PY
    say "OK    $base_name/SKILL.md"
    count=$((count + 1))
  done
  say "      $count command(s) convertido(s) em skills"
}

sync_default_artifacts() {
  say ""
  say "--- Default Artifacts ---"
  local src="$repo_root/agents/default-artifacts"
  [[ -d "$src" ]] || {
    say "AVISO agents/default-artifacts nao encontrado"
    return 0
  }
   ensure_dir "$agents_dir"
   local dest="$agents_dir/default-artifacts"
  backup_if_exists "$dest"
  rm -rf "$dest"
  cp -a "$src" "$dest"
  local n
  n="$(find "$dest" -type f | wc -l)"
  say "OK    default-artifacts ($n arquivo(s))"
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
}

show_plan() {
  local n_skills n_agents n_commands
  n_skills="$(find "$repo_root/skills" -mindepth 1 -maxdepth 1 -type d | while read -r d; do [[ -f "$d/SKILL.md" ]] && printf 'x\n'; done | wc -l)"
  n_agents="$(find "$repo_root/agents" -maxdepth 1 -type f -name '*.md' | wc -l)"
  n_commands="$(find "$repo_root/commands" -maxdepth 1 -type f -name '*.md' | wc -l)"

  say "Repo:         $repo_root"
  say "Skills:       $skills_dir"
  say "Instructions: $instructions_dir"
  say "Agents:       $agents_dir"
  say ""
  say "Plano:"
  say "  - Copiar $n_skills skill(s) para ~/.copilot/skills/"
  say "  - Converter $n_agents agent(s) para .agent.md"
  say "  - Converter $n_commands command(s) em skills"
  say "  - Copiar agents/default-artifacts/ para ~/.copilot/agents/default-artifacts/"
  say "  - Copiar .github/copilot-specific.instructions.md para ~/.copilot/instructions/"
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
  sync_commands_as_skills
  sync_default_artifacts
  sync_instructions
  say ""
  say "Pronto."
}

main
