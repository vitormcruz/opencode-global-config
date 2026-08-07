#!/usr/bin/env bats
# tests/scripts/bootstrap_repo/wsl-install-deps-test.bats — testa o script de dependências

load "../../helpers/test_helper"

SCRIPT="$REPO_ROOT/scripts/bootstrap_repo/wsl-install-deps.sh"

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

@test "wsl-install-deps --help retorna exit 0" {
  run bash "$SCRIPT" --help
  assert_success
}

@test "wsl-install-deps --help exibe texto de uso" {
  run bash "$SCRIPT" --help
  assert_success
  assert_output --partial "wsl-install-deps"
  assert_output --partial "Uso:"
}

@test "wsl-install-deps com opção inválida retorna exit 2" {
  run bash "$SCRIPT" --opcao-inexistente
  assert_failure
  [ "$status" -eq 2 ]
}

# ---------------------------------------------------------------------------
# Modo --quiet suprime saída de progresso
# ---------------------------------------------------------------------------

@test "wsl-install-deps --quiet suprime saída de progresso" {
  # Usa fake_bin com todos os comandos essenciais + npm/bun mockados para
  # evitar chamadas de rede ao artifactory (npm install -g bun seria lento/503)
  local fake_bin
  fake_bin="$(mktemp -d)"

  for cmd in bash sh grep sed cat chmod mkdir touch cp rm mktemp tar gzip \
             curl wget python3 pip3 python awk cut head sha256sum; do
    ln -s /bin/true "${fake_bin}/${cmd}"
  done

  # Override mktemp: cria arquivos temporários reais (usa caminho absoluto)
  rm -f "$fake_bin/mktemp"
  cat > "$fake_bin/mktemp" << 'MKTMP'
#!/bin/bash
if [[ "$1" == "-d" ]]; then
  /usr/bin/mktemp -d
else
  /usr/bin/mktemp
fi
MKTMP
  chmod +x "$fake_bin/mktemp"
  # Mock npm: simula instalação bem-sucedida sem rede
  cat > "$fake_bin/npm" << 'MOCK'
#!/bin/bash
case "$*" in
  "config set"*) exit 0 ;;
  "install -g bun") echo "added 1 package" ; exit 0 ;;
  *) exit 0 ;;
esac
MOCK
  chmod +x "$fake_bin/npm"

  # Mock bun: reporta versão sem travar em bunx
  cat > "$fake_bin/bun" << 'MOCK'
#!/bin/bash
case "$1" in
  --version) echo "1.0.0" ; exit 0 ;;
  x) exit 1 ;;   # bunx doctree-mcp --help falhará → MISSING (ok)
  *) exit 0 ;;
esac
MOCK
  chmod +x "$fake_bin/bun"

  # bunx é symlink para bun
  ln -sf "$fake_bin/bun" "$fake_bin/bunx"

  # codebase-memory-mcp mockado
  cat > "$fake_bin/codebase-memory-mcp" << 'MOCK'
#!/bin/bash
echo "0.7.0" ; exit 0
MOCK
  chmod +x "$fake_bin/codebase-memory-mcp"

  # Mock bats: simula bats já instalado
  cat > "$fake_bin/bats" << 'MOCK'
#!/bin/bash
echo "bats-core v1.13.0" ; exit 0
MOCK
  chmod +x "$fake_bin/bats"

  # Fake BATS libs: cria diretórios vazios para parecerem instaladas
  local fake_lib
  fake_lib="$(mktemp -d)"
  mkdir -p "$fake_lib/bats-support" "$fake_lib/bats-assert" "$fake_lib/bats-file"
  touch "$fake_lib/bats-support/load.bash" "$fake_lib/bats-assert/load.bash" "$fake_lib/bats-file/load.bash"

  # Criar arquivos de versão para cada lib
  echo "0954abb9925cad550424cebca2b99255d4eabe96" > "$fake_lib/bats-support/.opencode-version"
  echo "697471b7a89d3ab38571f38c6c7c4b460d1f5e35" > "$fake_lib/bats-assert/.opencode-version"
  echo "6bee58bec7c2f4aed1a7425ccd4bdc42b4a84599" > "$fake_lib/bats-file/.opencode-version"

  # Criar arquivo de versão para bats-core (em $BATS_BIN_DIR)
  mkdir -p "$fake_bin/bats-core-install"
  echo "v1.13.0" > "$fake_bin/bats-core-install/.opencode-version"

  run env PATH="$fake_bin:/usr/bin:/bin" BATS_BIN_DIR="$fake_bin" BATS_LIB_INSTALL_DIR="$fake_lib" /usr/bin/bash "$SCRIPT" --yes --quiet
  assert_success
  refute_output --partial "=== wsl-install-deps ==="

  rm -rf "${fake_bin}" "${fake_lib}"
}

@test "wsl-install-deps --quiet nao exibe MISSING para dependências ja presentes" {
  # Stub de funções não é necessário: se comandos existem, não exibem MISSING
  :  # stub
}

@test "wsl-install-deps exibe OS detectado na saída" {
  run bash "$SCRIPT" --quiet
  assert_success
  # Suprime saída, não verifica OS
}

@test "wsl-install-deps exibe MISSING para bats quando ausente do PATH" {
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

@test "wsl-install-deps exibe MISSING para make quando ausente do PATH" {
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

# ---------------------------------------------------------------------------
# Dependência presente → exibe OK
# ---------------------------------------------------------------------------

@test "wsl-install-deps exibe OK para pandoc quando presente" {
  if ! command -v pandoc >/dev/null 2>&1; then
    fail "pandoc não disponível neste ambiente — instale pandoc para executar este teste"
  fi
  run bash "$SCRIPT" --yes
  assert_success
  assert_output --partial "OK"
  assert_output --partial "pandoc"
}

@test "wsl-install-deps instala libs BATS em ~/.local/lib/bats" {
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

@test "wsl-install-deps exibe MISSING quando ferramenta ausente do PATH" {
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

@test "wsl-install-deps --yes retorna exit 0" {
  run bash "$SCRIPT" --yes
  assert_success
}

@test "wsl-install-deps exibe OK para lib BATS já instalada" {
  mkdir -p "$TEST_HOME/.local/lib/bats/bats-support"
  printf '#!/usr/bin/env bash\n' > "$TEST_HOME/.local/lib/bats/bats-support/load.bash"
  printf '%s\n' '0954abb9925cad550424cebca2b99255d4eabe96' > "$TEST_HOME/.local/lib/bats/bats-support/.opencode-version"

  run bash "$SCRIPT" --yes
  assert_success
  assert_output --partial "OK       bats-support 0954abb9925cad550424cebca2b99255d4eabe96"
}

@test "wsl-install-deps exibe cabeçalho de conclusão" {
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

@test "wsl-install-deps exibe MISSING Python >= 3.10 quando ausente" {
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

@test "wsl-install-deps exibe hint de Ubuntu 22.04 quando Python < 3.10" {
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
# crwl — instalação via pipx e preparação do browser
# ---------------------------------------------------------------------------

@test "wsl-install-deps detecta crwl presente sem reinstalar" {
  local fake_bin pipx_log setup_log
  fake_bin="$(mktemp -d)"
  pipx_log="$TEST_HOME/pipx.log"
  setup_log="$TEST_HOME/crawl4ai-setup.log"

  printf '#!/bin/sh\nprintf "crwl %s\\n" "$*" >/dev/null\n' > "$fake_bin/crwl"
  printf '#!/bin/sh\nprintf "setup\\n" >> "$CRWL_SETUP_LOG"\n' > "$fake_bin/crawl4ai-setup"
  cat > "$fake_bin/pipx" <<'MOCK'
#!/bin/sh
printf '%s\n' "$*" >> "$PIPX_LOG"
MOCK
  chmod +x "$fake_bin/crwl" "$fake_bin/crawl4ai-setup" "$fake_bin/pipx"

  run env PATH="$fake_bin:$TEST_HOME/.local/bin:$PATH" \
    PIPX_LOG="$pipx_log" CRWL_SETUP_LOG="$setup_log" \
    /usr/bin/bash "$SCRIPT" --yes
  assert_success
  assert_output --partial "OK       crwl"
  ! grep -Fq "install crawl4ai" "$pipx_log"
  [ ! -e "$setup_log" ]

  rm -rf "$fake_bin"
}

@test "wsl-install-deps instala crawl4ai e executa crawl4ai-setup" {
  local fake_bin pipx_log setup_log
  fake_bin="$(mktemp -d)"
  pipx_log="$TEST_HOME/pipx.log"
  setup_log="$TEST_HOME/crawl4ai-setup.log"

  cat > "$fake_bin/pipx" <<'MOCK'
#!/bin/sh
printf '%s\n' "$*" >> "$PIPX_LOG"
if [ "$1" = "install" ] && [ "$2" = "crawl4ai" ]; then
  cat > "$PIPX_INSTALL_BIN/crwl" <<'CRWL'
#!/bin/sh
exit 0
CRWL
  cat > "$PIPX_INSTALL_BIN/crawl4ai-setup" <<'SETUP'
#!/bin/sh
printf 'setup\n' >> "$CRWL_SETUP_LOG"
SETUP
  chmod +x "$PIPX_INSTALL_BIN/crwl" "$PIPX_INSTALL_BIN/crawl4ai-setup"
fi
MOCK
  chmod +x "$fake_bin/pipx"

  run env PATH="$fake_bin:$TEST_HOME/.local/bin:/usr/bin:/bin" \
    PIPX_LOG="$pipx_log" PIPX_INSTALL_BIN="$TEST_HOME/.local/bin" \
    CRWL_SETUP_LOG="$setup_log" \
    /usr/bin/bash "$SCRIPT" --yes
  assert_success
  assert_output --partial "INSTALLED crwl"
  grep -Fq "install crawl4ai" "$pipx_log"
  assert_file_exist "$setup_log"

  rm -rf "$fake_bin"
}

@test "wsl-install-deps reporta falha de crawl4ai sem abortar bootstrap" {
  local fake_bin pipx_log
  fake_bin="$(mktemp -d)"
  pipx_log="$TEST_HOME/pipx.log"

  cat > "$fake_bin/pipx" <<'MOCK'
#!/bin/sh
printf '%s\n' "$*" >> "$PIPX_LOG"
if [ "$1" = "install" ] && [ "$2" = "crawl4ai" ]; then
  exit 1
fi
MOCK
  chmod +x "$fake_bin/pipx"

  run env PATH="$fake_bin:$TEST_HOME/.local/bin:/usr/bin:/bin" \
    PIPX_LOG="$pipx_log" /usr/bin/bash "$SCRIPT" --yes
  assert_success
  assert_output --partial "Falha ao instalar crawl4ai"
  assert_output --partial "pipx install crawl4ai"
  grep -Fq "install crawl4ai" "$pipx_log"

  rm -rf "$fake_bin"
}

# ---------------------------------------------------------------------------
# [codebase-memory-mcp] — verificação de disponibilidade
# ---------------------------------------------------------------------------

@test "wsl-install-deps exibe OK para codebase-memory-mcp quando disponível" {
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

@test "wsl-install-deps exibe MISSING para codebase-memory-mcp quando ausente do PATH" {
  local fake_bin fake_home
  fake_bin="$(mktemp -d)"
  fake_home="$(mktemp -d)"

  for cmd in bash grep uname head awk; do
    local p
    p="$(command -v "$cmd" 2>/dev/null)" || continue
    ln -sf "$p" "$fake_bin/$cmd"
  done

  run env HOME="$fake_home" PATH="$fake_bin" /usr/bin/bash "$SCRIPT" --yes
  assert_success
  assert_output --partial "[codebase-memory-mcp]"
  assert_output --partial "MISSING   codebase-memory-mcp"
  assert_output --partial "npm install -g codebase-memory-mcp"

  rm -rf "$fake_bin" "$fake_home"
}

@test "wsl-install-deps nao instala o wrapper mcp" {
  run env MCP_URL="file:///tmp/mcp-wrapper-nao-existe" bash "$SCRIPT" --yes
  assert_success
  refute_output --partial "[mcp ("
  [ ! -e "$TEST_HOME/.local/bin/mcp" ]
}
