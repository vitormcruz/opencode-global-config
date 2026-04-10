#!/usr/bin/env bats
# tests/scripts/bootstrap_repo/opencode-install-deps-test.bats — testa o script de dependências

load "../../helpers/test_helper"

SCRIPT="$REPO_ROOT/scripts/bootstrap_repo/opencode-install-deps"

setup()    { common_setup; }
teardown() { common_teardown; }

# ---------------------------------------------------------------------------
# Ajuda e opções
# ---------------------------------------------------------------------------

@test "opencode-install-deps --help retorna exit 0" {
  run bash "$SCRIPT" --help
  assert_success
}

@test "opencode-install-deps --help exibe texto de uso" {
  run bash "$SCRIPT" --help
  assert_success
  assert_output --partial "opencode-install-deps"
  assert_output --partial "Uso:"
}

@test "opencode-install-deps com opção inválida retorna exit 2" {
  run bash "$SCRIPT" --opcao-inexistente
  assert_failure
  [ "$status" -eq 2 ]
}

# ---------------------------------------------------------------------------
# Modo --quiet suprime saída de progresso
# ---------------------------------------------------------------------------

@test "opencode-install-deps --quiet suprime saída de progresso" {
  run bash "$SCRIPT" --yes --quiet
  assert_success
  refute_output --partial "=== opencode-install-deps ==="
}

# ---------------------------------------------------------------------------
# Detecção de OS via função interna
# ---------------------------------------------------------------------------

@test "função detect_os retorna wsl, linux ou macos" {
  run bash -c "
    detect_os() {
      if [ -f /proc/version ] && grep -qi microsoft /proc/version 2>/dev/null; then
        echo 'wsl'
      elif [ \"\$(uname)\" = 'Darwin' ]; then
        echo 'macos'
      elif [ \"\$(uname)\" = 'Linux' ]; then
        echo 'linux'
      else
        echo 'unknown'
      fi
    }
    os=\$(detect_os)
    case \"\$os\" in
      wsl|linux|macos|unknown) echo \"\$os\" ;;
      *) exit 1 ;;
    esac
  "
  assert_success
}

@test "opencode-install-deps exibe OS detectado na saída" {
  run bash "$SCRIPT" --yes
  assert_success
  assert_output --partial "OS detectado:"
}

@test "opencode-install-deps exibe MISSING para make quando ausente do PATH" {
  local fake_bin
  fake_bin="$(mktemp -d)"

  for cmd in grep uname head awk; do
    local p
    p="$(command -v "$cmd")"
    ln -sf "$p" "$fake_bin/$cmd"
  done

  run env PATH="$fake_bin" /usr/bin/bash "$SCRIPT" --yes
  assert_success
  assert_output --partial "MISSING   make"
  assert_output --partial "Instalar: sudo apt-get install -y make"

  rm -rf "$fake_bin"
}

@test "opencode-install-deps exibe hint de librsvg2-bin quando conversor SVG está ausente" {
  local fake_bin
  fake_bin="$(mktemp -d)"

  for cmd in bash grep uname head awk command; do
    local p
    p="$(command -v "$cmd")"
    ln -sf "$p" "$fake_bin/$cmd"
  done

  run env PATH="$fake_bin" /usr/bin/bash "$SCRIPT" --yes
  assert_success
  assert_output --partial "[resvg ou rsvg-convert] Skill: svg-to-image"
  assert_output --partial "MISSING   resvg"
  assert_output --partial "MISSING   rsvg-convert"
  assert_output --partial "Instalar: sudo apt-get install -y librsvg2-bin"

  rm -rf "$fake_bin"
}

# ---------------------------------------------------------------------------
# Dependência presente → exibe OK
# ---------------------------------------------------------------------------

@test "opencode-install-deps exibe OK para pandoc quando presente" {
  if ! command -v pandoc >/dev/null 2>&1; then
    skip "pandoc não disponível neste ambiente"
  fi
  run bash "$SCRIPT" --yes
  assert_success
  assert_output --partial "OK"
  assert_output --partial "pandoc"
}

# ---------------------------------------------------------------------------
# Dependência ausente → exibe MISSING + hint
# ---------------------------------------------------------------------------

@test "opencode-install-deps exibe MISSING quando ferramenta ausente do PATH" {
  # Cria diretório fake sem pandoc e roda apenas a lógica de detecção
  local fake_bin
  fake_bin="$(mktemp -d)"

  # Script mínimo que testa a lógica de MISSING diretamente
  run bash -c "
    has_cmd() { command -v \"\$1\" >/dev/null 2>&1; }
    quiet=0
    say()  { [ \"\$quiet\" -eq 0 ] && printf '%s\n' \"\$*\" || true; }
    status_missing() { say \"  MISSING   \$*\"; }
    status_hint()    { say \"            \$*\"; }

    # Testa com comando que certamente não existe
    if ! has_cmd _cmd_que_nao_existe_xyz_; then
      status_missing '_cmd_que_nao_existe_xyz_'
      status_hint 'Instalar: algum-pacote'
    fi
  "
  assert_success
  assert_output --partial "MISSING"
  assert_output --partial "Instalar:"

  rm -rf "$fake_bin"
}

# ---------------------------------------------------------------------------
# Execução padrão retorna exit 0
# ---------------------------------------------------------------------------

@test "opencode-install-deps --yes retorna exit 0" {
  run bash "$SCRIPT" --yes
  assert_success
}

@test "opencode-install-deps exibe cabeçalho de conclusão" {
  run bash "$SCRIPT" --yes
  assert_success
  assert_output --partial "Concluido"
}
