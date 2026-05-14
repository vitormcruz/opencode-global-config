#!/usr/bin/env bats
# tests/scripts/opencode-svgtoimage-test.bats — testa o wrapper opencode-svgtoimage

load "../helpers/test_helper"

SCRIPT="$REPO_ROOT/scripts/opencode-svgtoimage"
FIXTURE_SVG="$REPO_ROOT/tests/test-resources/sample.svg"

setup()    { common_setup; }
teardown() { common_teardown; }

# ---------------------------------------------------------------------------
# Sem conversor no PATH → exit 1
# ---------------------------------------------------------------------------

@test "svgtoimage sem conversor disponível falha com exit != 0" {
  local fake_bin
  fake_bin="$(mktemp -d)"

  run bash -c "
    SVG2PNG_BIN=nenhum_conversor_xyz
    export SVG2PNG_BIN
    PATH='$fake_bin:/usr/bin:/bin'
    cat '$FIXTURE_SVG' | bash '$SCRIPT' 2>&1
  "
  assert_failure

  rm -rf "$fake_bin"
}

@test "svgtoimage sem conversor exibe mensagem de erro" {
  run bash -c "
    SVG2PNG_BIN=conversor_inexistente_xyz
    export SVG2PNG_BIN
    cat '$FIXTURE_SVG' | bash '$SCRIPT' 2>&1 || true
  "
  assert_output --partial "Conversor nao suportado"
}

# ---------------------------------------------------------------------------
# Helper: garante que ao menos um conversor está disponível no PATH.
# O script escolhe qual usar — o teste não precisa saber qual é.
# ---------------------------------------------------------------------------

_require_converter() {
  if ! command -v resvg >/dev/null 2>&1 && ! command -v rsvg-convert >/dev/null 2>&1; then
    fail "nenhum conversor SVG disponível (resvg ou rsvg-convert) — instale um deles para executar este teste"
  fi
}

# ---------------------------------------------------------------------------
# Comportamento do script com conversor disponível
# ---------------------------------------------------------------------------

@test "svgtoimage gera PNG e retorna imagePath" {
  _require_converter

  run bash -c "cat '$FIXTURE_SVG' | bash '$SCRIPT'"
  assert_success
  assert_output --partial '"imagePath"'

  local img_path
  img_path="$(echo "$output" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['imagePath'])")"
  assert_file_exist "$img_path"
}

@test "svgtoimage retorna campo markdown" {
  _require_converter

  run bash -c "cat '$FIXTURE_SVG' | bash '$SCRIPT'"
  assert_success
  assert_output --partial '"markdown"'
}

@test "svgtoimage saída é JSON válido" {
  _require_converter

  run bash -c "cat '$FIXTURE_SVG' | bash '$SCRIPT'"
  assert_success
  run python3 -c "import sys,json; json.loads('$output')" <<< "$output" || \
  run bash -c "echo '$output' | python3 -c 'import sys,json; json.load(sys.stdin)'"
  assert_success
}
