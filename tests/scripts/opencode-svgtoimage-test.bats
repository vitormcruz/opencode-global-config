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
# SVG via stdin com resvg → JSON com imagePath, PNG existe
# ---------------------------------------------------------------------------

@test "svgtoimage com resvg gera PNG e retorna imagePath" {
  local fake_bin
  fake_bin="$(mktemp -d)"

  # Mock de resvg: copia o arquivo de entrada para o de saída (simula conversão)
  cat > "$fake_bin/resvg" <<'MOCK'
#!/usr/bin/env bash
# resvg <entrada.svg> <saida.png>
cp "$1" "$2"
MOCK
  chmod +x "$fake_bin/resvg"

  run env PATH="$fake_bin:$PATH" SVG2PNG_BIN=resvg bash -c "cat '$FIXTURE_SVG' | bash '$SCRIPT'"
  assert_success
  assert_output --partial '"imagePath"'

  local img_path
  img_path="$(echo "$output" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['imagePath'])")"
  assert_file_exist "$img_path"

  rm -rf "$fake_bin"
}

@test "svgtoimage com rsvg-convert gera PNG e retorna imagePath (requer rsvg-convert)" {
  if ! command -v rsvg-convert >/dev/null 2>&1; then
    skip "rsvg-convert não disponível neste ambiente"
  fi

  run bash -c "cat '$FIXTURE_SVG' | SVG2PNG_BIN=rsvg-convert bash '$SCRIPT'"
  assert_success
  assert_output --partial '"imagePath"'

  local img_path
  img_path="$(echo "$output" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['imagePath'])")"
  assert_file_exist "$img_path"
}

# ---------------------------------------------------------------------------
# Saída contém campo markdown
# ---------------------------------------------------------------------------

@test "svgtoimage retorna campo markdown com conversor disponível" {
  if ! command -v resvg >/dev/null 2>&1 && ! command -v rsvg-convert >/dev/null 2>&1; then
    skip "nenhum conversor SVG disponível neste ambiente"
  fi

  run bash -c "cat '$FIXTURE_SVG' | bash '$SCRIPT'"
  assert_success
  assert_output --partial '"markdown"'
}

# ---------------------------------------------------------------------------
# Modo automático detecta conversor
# ---------------------------------------------------------------------------

@test "svgtoimage em modo auto detecta conversor disponível" {
  if ! command -v resvg >/dev/null 2>&1 && ! command -v rsvg-convert >/dev/null 2>&1; then
    skip "nenhum conversor SVG disponível neste ambiente"
  fi

  run bash -c "cat '$FIXTURE_SVG' | bash '$SCRIPT'"
  assert_success
  assert_output --partial '"imagePath"'
}
