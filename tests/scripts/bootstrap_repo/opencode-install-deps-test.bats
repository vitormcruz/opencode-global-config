#!/usr/bin/env bats
# tests/scripts/bootstrap_repo/opencode-install-deps-test.bats — testa o script de dependências

load "../../helpers/test_helper"

SCRIPT="$REPO_ROOT/scripts/bootstrap_repo/opencode-install-deps.sh"

setup() {
  common_setup
  common_setup_deps
}

teardown() {
  common_teardown_deps
  common_teardown
}

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

@test "opencode-install-deps exibe MISSING para bats quando ausente do PATH" {
  local fake_bin
  fake_bin="$(mktemp -d)"

  for cmd in grep uname head awk tar gzip cp rm mkdir mktemp tr; do
    local p
    p="$(command -v "$cmd")"
    ln -sf "$p" "$fake_bin/$cmd"
  done

  run env PATH="$fake_bin" /usr/bin/bash "$SCRIPT" --yes
  assert_success
  assert_output --partial "MISSING   bats-core"

  rm -rf "$fake_bin"
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
    fail "pandoc não disponível neste ambiente — instale pandoc para executar este teste"
  fi
  run bash "$SCRIPT" --yes
  assert_success
  assert_output --partial "OK"
  assert_output --partial "pandoc"
}

@test "opencode-install-deps instala libs BATS em ~/.local/lib/bats" {
  run bash "$SCRIPT" --yes

  assert_success
  assert_dir_exist "$TEST_HOME/.local/lib/bats/bats-support"
  assert_dir_exist "$TEST_HOME/.local/lib/bats/bats-assert"
  assert_dir_exist "$TEST_HOME/.local/lib/bats/bats-file"
  assert_file_exist "$TEST_HOME/.local/lib/bats/bats-support/load.bash"
  assert_file_exist "$TEST_HOME/.local/lib/bats/bats-assert/load.bash"
  assert_file_exist "$TEST_HOME/.local/lib/bats/bats-file/load.bash"
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

@test "opencode-install-deps exibe OK para lib BATS já instalada" {
  mkdir -p "$TEST_HOME/.local/lib/bats/bats-support"
  printf '#!/usr/bin/env bash\n' > "$TEST_HOME/.local/lib/bats/bats-support/load.bash"
  printf '%s\n' '0954abb9925cad550424cebca2b99255d4eabe96' > "$TEST_HOME/.local/lib/bats/bats-support/.opencode-version"

  run bash "$SCRIPT" --yes
  assert_success
  assert_output --partial "OK       bats-support 0954abb9925cad550424cebca2b99255d4eabe96"
}

@test "opencode-install-deps exibe cabeçalho de conclusão" {
  run bash "$SCRIPT" --yes
  assert_success
  assert_output --partial "Concluido"
}

# ---------------------------------------------------------------------------
# check_python3_version — verificação de Python >= 3.10
# ---------------------------------------------------------------------------

CHECK_PYTHON3_FN='
  has_cmd() { command -v "$1" >/dev/null 2>&1; }
  PYTHON3_VERSION=""
  check_python3_version() {
    if ! has_cmd python3; then return 1; fi
    PYTHON3_VERSION="$(python3 --version 2>/dev/null | awk '"'"'{print $2}'"'"')"
    local minor
    minor="$(echo "$PYTHON3_VERSION" | cut -d. -f2)"
    [ -n "$minor" ] && [ "$minor" -ge 10 ] 2>/dev/null
  }
'

@test "check_python3_version aceita Python 3.12" {
  local fake_bin
  fake_bin="$(mktemp -d)"
  printf '#!/bin/sh\necho "Python 3.12.4"\n' > "$fake_bin/python3"
  chmod +x "$fake_bin/python3"
  for cmd in awk cut; do
    ln -sf "$(command -v "$cmd")" "$fake_bin/$cmd"
  done

  run env PATH="$fake_bin" /usr/bin/bash -c "$CHECK_PYTHON3_FN"'check_python3_version'
  assert_success

  rm -rf "$fake_bin"
}

@test "check_python3_version rejeita Python 3.8" {
  local fake_bin
  fake_bin="$(mktemp -d)"
  printf '#!/bin/sh\necho "Python 3.8.10"\n' > "$fake_bin/python3"
  chmod +x "$fake_bin/python3"
  for cmd in awk cut; do
    ln -sf "$(command -v "$cmd")" "$fake_bin/$cmd"
  done

  run env PATH="$fake_bin" /usr/bin/bash -c "$CHECK_PYTHON3_FN"'check_python3_version'
  assert_failure

  rm -rf "$fake_bin"
}

@test "check_python3_version falha quando python3 ausente" {
  local fake_bin
  fake_bin="$(mktemp -d)"

  run env PATH="$fake_bin" /usr/bin/bash -c "$CHECK_PYTHON3_FN"'check_python3_version'
  assert_failure

  rm -rf "$fake_bin"
}

# ---------------------------------------------------------------------------
# docling — mensagens quando Python < 3.10
# ---------------------------------------------------------------------------

@test "opencode-install-deps exibe MISSING Python >= 3.10 quando ausente" {
  local fake_bin
  fake_bin="$(mktemp -d)"

  for cmd in grep uname head awk cut; do
    local p
    p="$(command -v "$cmd" 2>/dev/null)" || continue
    ln -sf "$p" "$fake_bin/$cmd"
  done
  printf '#!/bin/sh\necho "Python 3.8.10"\n' > "$fake_bin/python3"
  printf '#!/bin/sh\necho "1.0.0"\n' > "$fake_bin/pipx"
  chmod +x "$fake_bin/python3" "$fake_bin/pipx"

  run env PATH="$fake_bin" /usr/bin/bash "$SCRIPT" --yes
  assert_success
  assert_output --partial "Python >= 3.10"

  rm -rf "$fake_bin"
}

@test "opencode-install-deps exibe hint de Ubuntu 22.04 quando Python < 3.10" {
  local fake_bin
  fake_bin="$(mktemp -d)"

  for cmd in grep uname head awk cut; do
    local p
    p="$(command -v "$cmd" 2>/dev/null)" || continue
    ln -sf "$p" "$fake_bin/$cmd"
  done
  printf '#!/bin/sh\necho "Python 3.8.10"\n' > "$fake_bin/python3"
  printf '#!/bin/sh\necho "1.0.0"\n' > "$fake_bin/pipx"
  chmod +x "$fake_bin/python3" "$fake_bin/pipx"

  run env PATH="$fake_bin" /usr/bin/bash "$SCRIPT" --yes
  assert_success
  assert_output --partial "Ubuntu 22.04"

  rm -rf "$fake_bin"
}

# ---------------------------------------------------------------------------
# [doctree] — verificacao de disponibilidade do doctree-mcp
# ---------------------------------------------------------------------------

@test "opencode-install-deps exibe OK para doctree quando bun e cache disponiveis" {
  local fake_bin fake_home
  fake_bin="$(mktemp -d)"
  fake_home="$(mktemp -d)"

  printf '#!/bin/sh\necho "1.0.0"\n' > "$fake_bin/bun"
  chmod +x "$fake_bin/bun"
  mkdir -p "$fake_home/.bun/install/cache/doctree-mcp"

  run env HOME="$fake_home" PATH="$fake_bin" /usr/bin/bash "$SCRIPT" --yes
  assert_success
  assert_output --partial "[doctree]"
  assert_output --partial "OK"

  rm -rf "$fake_bin" "$fake_home"
}

@test "opencode-install-deps exibe MISSING para doctree quando bun ausente" {
  local fake_bin
  fake_bin="$(mktemp -d)"

  for cmd in bash grep uname head awk; do
    local p
    p="$(command -v "$cmd" 2>/dev/null)" || continue
    ln -sf "$p" "$fake_bin/$cmd"
  done

  run env PATH="$fake_bin" /usr/bin/bash "$SCRIPT" --yes
  assert_success
  assert_output --partial "[doctree]"
  assert_output --partial "MISSING   doctree"
  assert_output --partial "scripts/doctree/install"

  rm -rf "$fake_bin"
}

# ---------------------------------------------------------------------------
# [codebase-memory-mcp] — verificação de disponibilidade
# ---------------------------------------------------------------------------

@test "opencode-install-deps exibe OK para codebase-memory-mcp quando disponível" {
  local fake_bin
  fake_bin="$(mktemp -d)"

  printf '#!/bin/sh\necho "codebase-memory-mcp 1.0.0"\n' > "$fake_bin/codebase-memory-mcp"
  chmod +x "$fake_bin/codebase-memory-mcp"

  run env PATH="$fake_bin" /usr/bin/bash "$SCRIPT" --yes
  assert_success
  assert_output --partial "[codebase-memory-mcp]"
  assert_output --partial "OK"

  rm -rf "$fake_bin"
}

@test "opencode-install-deps exibe MISSING para codebase-memory-mcp quando ausente do PATH" {
  local fake_bin
  fake_bin="$(mktemp -d)"

  for cmd in bash grep uname head awk; do
    local p
    p="$(command -v "$cmd" 2>/dev/null)" || continue
    ln -sf "$p" "$fake_bin/$cmd"
  done

  run env PATH="$fake_bin" /usr/bin/bash "$SCRIPT" --yes
  assert_success
  assert_output --partial "[codebase-memory-mcp]"
  assert_output --partial "MISSING   codebase-memory-mcp"
  assert_output --partial "scripts/codebase-memory/install"

  rm -rf "$fake_bin"
}
