#!/usr/bin/env bats
# tests/scripts/doctree/install-doctree-test.bats
# Testa o script scripts/doctree/install

load "../../helpers/test_helper"

SCRIPT="$REPO_ROOT/scripts/doctree/install.sh"

setup()    { common_setup; }
teardown() { common_teardown; }

@test "doctree/install --help retorna exit 0" {
  run bash "$SCRIPT" --help
  assert_success
  assert_output --partial "doctree/install"
  assert_output --partial "Uso:"
}

@test "doctree/install com opcao invalida retorna exit 2" {
  run bash "$SCRIPT" --opcao-inexistente
  assert_failure
  [ "$status" -eq 2 ]
}

@test "doctree/install --check-only reporta OK quando bun e doctree-mcp estao disponiveis" {
  local fake_bin
  fake_bin="$(mktemp -d)"

  printf '#!/bin/sh\necho "1.0.0"\n' > "$fake_bin/bun"
  chmod +x "$fake_bin/bun"
  printf '#!/bin/sh\nexit 0\n' > "$fake_bin/bunx"
  chmod +x "$fake_bin/bunx"

  run env PATH="$fake_bin" /usr/bin/bash "$SCRIPT" --check-only
  assert_success
  assert_output --partial "doctree-mcp disponivel"

  rm -rf "$fake_bin"
}

@test "doctree/install --check-only reporta missing quando bun ausente" {
  local fake_bin
  fake_bin="$(mktemp -d)"

  run env PATH="$fake_bin" /usr/bin/bash "$SCRIPT" --check-only
  assert_success
  assert_output --partial "bun nao encontrado"
  assert_output --partial "doctree-mcp nao disponivel"

  rm -rf "$fake_bin"
}

@test "doctree/install aborta quando npm nao esta disponivel e bun ausente" {
  local fake_bin
  fake_bin="$(mktemp -d)"

  for cmd in bash grep head awk; do
    local p
    p="$(command -v "$cmd" 2>/dev/null)" || continue
    ln -sf "$p" "$fake_bin/$cmd"
  done

  run env PATH="$fake_bin" /usr/bin/bash "$SCRIPT" --yes
  assert_failure
  assert_output --partial "npm nao encontrado"

  rm -rf "$fake_bin"
}

@test "doctree/install baixa skills do doctree para OpenCode" {
  local fake_bin fake_home
  fake_bin="$(mktemp -d)"
  fake_home="$(mktemp -d)"

  for cmd in bash head mkdir basename cp rm dirname ln readlink; do
    local p
    p="$(command -v "$cmd" 2>/dev/null)" || continue
    ln -sf "$p" "$fake_bin/$cmd"
  done

  printf '#!/bin/sh\necho "1.0.0"\n' > "$fake_bin/bun"
  chmod +x "$fake_bin/bun"
  printf '#!/bin/sh\nexit 0\n' > "$fake_bin/bunx"
  chmod +x "$fake_bin/bunx"

  cat > "$fake_bin/curl" <<'SCRIPT'
#!/bin/bash
prev=""
outfile=""
for i in "$@"; do
  if [ "$prev" = "-o" ]; then
    outfile="$i"
  fi
  prev="$i"
done
if [ -n "$outfile" ]; then
  outdir="${outfile%/*}"
  mkdir -p "$outdir"
  echo "# doctree skill" > "$outfile"
fi
exit 0
SCRIPT
  chmod +x "$fake_bin/curl"

  run env PATH="$fake_bin" HOME="$fake_home" /usr/bin/bash "$SCRIPT" --yes
  assert_success

  [ -f "$fake_home/.config/opencode/skills/doc-read/SKILL.md" ]
  [ -f "$fake_home/.config/opencode/skills/doc-write/SKILL.md" ]
  [ -f "$fake_home/.config/opencode/skills/doc-lint/SKILL.md" ]

  # Verifica que o symlink opencode-doctree-run foi criado
  assert_symlink_to "$REPO_ROOT/scripts/doctree/doctree-run.sh" "$fake_home/.local/bin/opencode-doctree-run"

  rm -rf "$fake_bin" "$fake_home"
}
