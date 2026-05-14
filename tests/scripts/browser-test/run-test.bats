#!/usr/bin/env bats
# tests/scripts/browser-test/run-test.bats

load "../../helpers/test_helper"

SCRIPT="$REPO_ROOT/scripts/browser-test/run"

setup()    { common_setup; }
teardown() { common_teardown; }

# ---------------------------------------------------------------------------
# --help retorna exit 0
# ---------------------------------------------------------------------------

@test "run --help retorna exit 0" {
  run bash "$SCRIPT" --help
  assert_success
  assert_output --partial "scripts/browser-test/run"
}

# ---------------------------------------------------------------------------
# Sem argumento → erro JSON
# ---------------------------------------------------------------------------

@test "run sem argumento retorna erro JSON" {
  run bash "$SCRIPT"
  assert_failure
  assert_output --partial '"ok":false'
  assert_output --partial "Uso:"
}

# ---------------------------------------------------------------------------
# Arquivo nao existe → erro JSON
# ---------------------------------------------------------------------------

@test "run com arquivo inexistente retorna erro JSON" {
  run bash "$SCRIPT" /tmp/nao-existe-xyz-123.js
  assert_failure
  assert_output --partial '"ok":false'
  assert_output --partial "nao encontrado"
}

# ---------------------------------------------------------------------------
# Arquivo sem extensao .js → erro JSON
# ---------------------------------------------------------------------------

@test "run com arquivo sem extensao .js retorna erro JSON" {
  local tmp_file
  tmp_file="$(mktemp /tmp/browser-test-XXXX.txt)"

  run bash "$SCRIPT" "$tmp_file"
  assert_failure
  assert_output --partial '"ok":false'
  assert_output --partial ".js"

  rm -f "$tmp_file"
}

# ---------------------------------------------------------------------------
# Node ausente → erro JSON
# ---------------------------------------------------------------------------

@test "run sem node no PATH retorna erro JSON" {
  local tmp_script
  tmp_script="$(mktemp /tmp/browser-test-XXXX.js)"
  echo "console.log('hello')" > "$tmp_script"

  # Cria PATH fake sem node
  local fake_bin
  fake_bin="$(mktemp -d)"
  ln -s "$(command -v bash)" "$fake_bin/bash"
  ln -s "$(command -v cat)" "$fake_bin/cat"
  ln -s "$(command -v grep)" "$fake_bin/grep"
  ln -s "$(command -v sed)" "$fake_bin/sed"
  ln -s "$(command -v date)" "$fake_bin/date"
  ln -s "$(command -v rm)" "$fake_bin/rm"
  ln -s "$(command -v printf)" "$fake_bin/printf" 2>/dev/null || true
  ln -s "$(command -v head)" "$fake_bin/head"
  ln -s "$(command -v tr)" "$fake_bin/tr"
  ln -s "$(command -v uname)" "$fake_bin/uname"

  run env PATH="$fake_bin" bash "$SCRIPT" "$tmp_script"
  assert_failure
  assert_output --partial '"ok":false'
  assert_output --partial "node"

  rm -f "$tmp_script" 2>/dev/null || true
  rm -rf "$fake_bin"
}

# ---------------------------------------------------------------------------
# Cleanup: script deletado apos execucao
# ---------------------------------------------------------------------------

@test "run deleta script .js apos execucao bem-sucedida" {
  # bats test_tags=requires:playwright
  if ! command -v node >/dev/null 2>&1; then
    fail "node nao instalado — instale node para executar este teste"
  fi
  if ! command -v playwright >/dev/null 2>&1; then
    fail "playwright nao instalado — instale playwright para executar este teste"
  fi

  local tmp_script
  tmp_script="$(mktemp /tmp/browser-test-XXXX.js)"
  cat > "$tmp_script" <<'SCRIPT'
console.log(JSON.stringify({ok:true,screenshots:[],console:["test"],errors:[],duration_ms:0}));
SCRIPT

  run bash "$SCRIPT" "$tmp_script"
  assert_success
  # Script deve ter sido deletado
  assert [ ! -f "$tmp_script" ]
}

@test "run deleta script .js mesmo em caso de erro do node" {
  # bats test_tags=requires:playwright
  if ! command -v node >/dev/null 2>&1; then
    fail "node nao instalado — instale node para executar este teste"
  fi
  if ! command -v playwright >/dev/null 2>&1; then
    fail "playwright nao instalado — instale playwright para executar este teste"
  fi

  local tmp_script
  tmp_script="$(mktemp /tmp/browser-test-XXXX.js)"
  echo "throw new Error('deliberate failure');" > "$tmp_script"

  run bash "$SCRIPT" "$tmp_script"
  # Pode falhar ou ter ok:false, mas script deve sumir
  assert [ ! -f "$tmp_script" ]
}
