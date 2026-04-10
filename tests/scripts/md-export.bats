#!/usr/bin/env bats
# tests/scripts/md-export.bats — testa o wrapper opencode-md-export

load "../helpers/test_helper"

SCRIPT="$REPO_ROOT/scripts/opencode-md-export"
FIXTURE_MD="$REPO_ROOT/tests/fixtures/sample.md"

setup()    { common_setup; }
teardown() { common_teardown; }

# ---------------------------------------------------------------------------
# Sem campo 'source' → ok:false
# ---------------------------------------------------------------------------

@test "md-export sem campo source retorna ok:false" {
  run bash -c "echo '{\"to\":\"docx\"}' | bash '$SCRIPT'"
  assert_success
  assert_output --partial '"ok":false'
  assert_output --partial "obrigatorio"
}

# ---------------------------------------------------------------------------
# Sem campo 'to' → ok:false
# ---------------------------------------------------------------------------

@test "md-export sem campo to retorna ok:false" {
  run bash -c "echo '{\"source\":\"$FIXTURE_MD\"}' | bash '$SCRIPT'"
  assert_success
  assert_output --partial '"ok":false'
  assert_output --partial "obrigatorio"
}

# ---------------------------------------------------------------------------
# Formato inválido → ok:false
# ---------------------------------------------------------------------------

@test "md-export com formato inválido retorna ok:false" {
  run bash -c "
    echo '{\"source\":\"$FIXTURE_MD\",\"to\":\"pdf\"}' | bash '$SCRIPT'
  "
  assert_success
  assert_output --partial '"ok":false'
  assert_output --partial "invalido"
}

# ---------------------------------------------------------------------------
# Arquivo fonte não encontrado → ok:false
# ---------------------------------------------------------------------------

@test "md-export com arquivo inexistente retorna ok:false" {
  run bash -c "
    echo '{\"source\":\"/tmp/nao-existe-xyz.md\",\"to\":\"docx\"}' | bash '$SCRIPT'
  "
  assert_success
  assert_output --partial '"ok":false'
}

# ---------------------------------------------------------------------------
# Sem pandoc no PATH → ok:false com hint
# ---------------------------------------------------------------------------

@test "md-export sem pandoc no PATH retorna ok:false" {
  local fake_bin
  fake_bin="$(mktemp -d)"

  # Cria stub de python3 e outros, mas não de pandoc
  for cmd in bash sh python3 sed grep mkdir mktemp date basename dirname; do
    local p
    p="$(command -v "$cmd" 2>/dev/null)" || continue
    ln -sf "$p" "$fake_bin/$cmd"
  done

  run bash -c "
    PATH='$fake_bin'
    echo '{\"source\":\"$FIXTURE_MD\",\"to\":\"docx\"}' | bash '$SCRIPT'
  "
  assert_success
  assert_output --partial '"ok":false'

  rm -rf "$fake_bin"
}

@test "md-export sem pandoc no PATH inclui hint de instalação" {
  local fake_bin
  fake_bin="$(mktemp -d)"

  for cmd in bash sh python3 sed grep mkdir mktemp date basename dirname; do
    local p
    p="$(command -v "$cmd" 2>/dev/null)" || continue
    ln -sf "$p" "$fake_bin/$cmd"
  done

  run bash -c "
    PATH='$fake_bin'
    echo '{\"source\":\"$FIXTURE_MD\",\"to\":\"docx\"}' | bash '$SCRIPT'
  "
  assert_success
  assert_output --partial "pandoc"

  rm -rf "$fake_bin"
}

# ---------------------------------------------------------------------------
# Não sobrescreve sem --overwrite → ok:false
# ---------------------------------------------------------------------------

@test "md-export não sobrescreve arquivo existente sem --overwrite" {
  if ! command -v pandoc >/dev/null 2>&1; then
    skip "pandoc não disponível neste ambiente"
  fi

  local out_dir
  out_dir="$(mktemp -d)"
  local out_file="$out_dir/sample.docx"

  # Cria arquivo que vai colidir
  touch "$out_file"

  run bash -c "
    echo '{\"source\":\"$FIXTURE_MD\",\"to\":\"docx\",\"outputPath\":\"$out_file\"}' \
      | bash '$SCRIPT'
  "
  assert_success
  assert_output --partial '"ok":false'
  assert_output --partial "ja existe"

  rm -rf "$out_dir"
}

# ---------------------------------------------------------------------------
# MD válido → docx gerado (requer pandoc)
# ---------------------------------------------------------------------------

@test "md-export com MD válido gera DOCX (requer pandoc)" {
  if ! command -v pandoc >/dev/null 2>&1; then
    skip "pandoc não disponível neste ambiente"
  fi

  local out_dir
  out_dir="$(mktemp -d)"

  run bash -c "
    echo '{\"source\":\"$FIXTURE_MD\",\"to\":\"docx\",\"outputDir\":\"$out_dir\"}' \
      | bash '$SCRIPT'
  "
  assert_success
  assert_output --partial '"ok":true'

  rm -rf "$out_dir"
}

@test "md-export artifact gerado existe no disco (requer pandoc)" {
  if ! command -v pandoc >/dev/null 2>&1; then
    skip "pandoc não disponível neste ambiente"
  fi

  local out_dir
  out_dir="$(mktemp -d)"

  result="$(echo "{\"source\":\"$FIXTURE_MD\",\"to\":\"docx\",\"outputDir\":\"$out_dir\"}" \
    | bash "$SCRIPT")"

  artifact="$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['artifacts'][0])" 2>/dev/null)"

  assert_file_exist "$artifact"

  rm -rf "$out_dir"
}

# ---------------------------------------------------------------------------
# Saída é sempre JSON válido
# ---------------------------------------------------------------------------

@test "md-export saída é JSON válido em caso de erro" {
  run bash -c "echo '{}' | bash '$SCRIPT'"
  assert_success
  [[ "$output" =~ ^\{.*\}$ ]]
}
