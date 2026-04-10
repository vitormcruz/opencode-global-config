#!/usr/bin/env bats
# tests/wrappers/doc-extract.bats — testa o wrapper opencode-doc-extract

load "../helpers/test_helper"

SCRIPT="$REPO_ROOT/scripts/opencode-doc-extract"
FIXTURE_PDF="$REPO_ROOT/tests/fixtures/sample.pdf"

setup()    { common_setup; }
teardown() { common_teardown; }

# ---------------------------------------------------------------------------
# Sem campo 'source' → ok:false
# ---------------------------------------------------------------------------

@test "doc-extract sem campo source retorna ok:false" {
  run bash -c "echo '{}' | bash '$SCRIPT'"
  assert_success
  assert_output --partial '"ok":false'
}

@test "doc-extract sem campo source inclui mensagem de erro" {
  run bash -c "echo '{}' | bash '$SCRIPT'"
  assert_success
  assert_output --partial "obrigatorio"
}

# ---------------------------------------------------------------------------
# Formato inválido → ok:false
# ---------------------------------------------------------------------------

@test "doc-extract com formato inválido retorna ok:false" {
  run bash -c "
    echo '{\"source\":\"$FIXTURE_PDF\",\"to\":\"xyz\"}' | bash '$SCRIPT'
  "
  assert_success
  assert_output --partial '"ok":false'
  assert_output --partial "invalido"
}

# ---------------------------------------------------------------------------
# Arquivo fonte não encontrado → ok:false
# ---------------------------------------------------------------------------

@test "doc-extract com arquivo inexistente retorna ok:false" {
  run bash -c "
    echo '{\"source\":\"/tmp/nao-existe-xyz.pdf\"}' | bash '$SCRIPT'
  "
  assert_success
  assert_output --partial '"ok":false'
}

# ---------------------------------------------------------------------------
# Sem docling no PATH → ok:false com hint
# ---------------------------------------------------------------------------

@test "doc-extract sem docling no PATH retorna ok:false com hint" {
  local fake_bin
  fake_bin="$(mktemp -d)"
  # Não coloca docling no fake_bin

  run bash -c "
    PATH='$fake_bin:/usr/bin:/bin'
    echo '{\"source\":\"$FIXTURE_PDF\"}' | bash '$SCRIPT'
  "
  assert_success
  assert_output --partial '"ok":false'
  assert_output --partial '"hint":'

  rm -rf "$fake_bin"
}

@test "doc-extract sem docling no PATH inclui hint de instalação" {
  local fake_bin
  fake_bin="$(mktemp -d)"

  run bash -c "
    PATH='$fake_bin:/usr/bin:/bin'
    echo '{\"source\":\"$FIXTURE_PDF\"}' | bash '$SCRIPT'
  "
  assert_success
  assert_output --partial "pipx"

  rm -rf "$fake_bin"
}

# ---------------------------------------------------------------------------
# Entrada válida com docling disponível → ok:true
# ---------------------------------------------------------------------------

@test "doc-extract com PDF válido retorna ok:true (requer docling)" {
  if ! command -v docling >/dev/null 2>&1; then
    skip "docling não disponível neste ambiente"
  fi

  local out_dir
  out_dir="$(mktemp -d)"

  run bash -c "
    echo '{\"source\":\"$FIXTURE_PDF\",\"outputDir\":\"$out_dir\"}' | bash '$SCRIPT'
  "
  assert_success
  assert_output --partial '"ok":true'

  rm -rf "$out_dir"
}

@test "doc-extract com PDF válido gera artifact (requer docling)" {
  if ! command -v docling >/dev/null 2>&1; then
    skip "docling não disponível neste ambiente"
  fi

  local out_dir
  out_dir="$(mktemp -d)"

  run bash -c "
    echo '{\"source\":\"$FIXTURE_PDF\",\"outputDir\":\"$out_dir\"}' | bash '$SCRIPT'
  "
  assert_success

  # artifacts não deve estar vazio
  refute_output --partial '"artifacts":[]'

  rm -rf "$out_dir"
}

# ---------------------------------------------------------------------------
# Saída é sempre JSON válido
# ---------------------------------------------------------------------------

@test "doc-extract saída é JSON válido em caso de erro" {
  run bash -c "echo '{}' | bash '$SCRIPT'"
  assert_success
  # JSON válido começa com {
  [[ "$output" =~ ^\{.*\}$ ]]
}
