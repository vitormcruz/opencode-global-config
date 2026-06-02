#!/usr/bin/env bash
# tests/helpers/test_helper.bash — setup/teardown compartilhado

BATS_LIB_PATH="${BATS_LIB_PATH:-$HOME/.local/lib/bats}"
export BATS_LIB_PATH

# Carrega libs BATS instaladas via BATS_LIB_PATH
bats_load_library bats-support
bats_load_library bats-assert
bats_load_library bats-file

# Raiz do repositório
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Diretório temporário para sandbox de HOME
common_setup() {
  TEST_HOME="$(mktemp -d)"
  TEST_CONFIG_DIR="$TEST_HOME/.config/opencode"
  TEST_BASHRC="$TEST_HOME/.bashrc"
  touch "$TEST_BASHRC"
  export HOME="$TEST_HOME"
  export XDG_CONFIG_HOME="$TEST_HOME/.config"
}

common_teardown() {
  if [[ -n "$TEST_HOME" && "$TEST_HOME" == /tmp/* ]]; then
    rm -rf "$TEST_HOME"
  fi
}

# Cria tarball fake de uma lib BATS auxiliar (bats-support, bats-assert, bats-file)
make_fake_bats_library_archive() {
  local name="$1"
  local workdir archive

  workdir="$(mktemp -d)"
  archive="$workdir/${name}.tar.gz"
  mkdir -p "$workdir/${name}/src"
  printf '#!/usr/bin/env bash\n' > "$workdir/${name}/load.bash"
  tar -czf "$archive" -C "$workdir" "$name"
  rm -rf "$workdir/$name"
  printf '%s\n' "$archive"
}

# Cria tarball fake do bats-core com install.sh funcional
make_fake_bats_core_archive() {
  local workdir archive bin_dir

  workdir="$(mktemp -d)"
  archive="$workdir/bats-core.tar.gz"
  bin_dir="$workdir/bats-core-fake/bin"
  mkdir -p "$bin_dir"
  printf '#!/usr/bin/env bash\nPREFIX="${1:-/usr/local}"\nmkdir -p "$PREFIX/bin"\ncp "$(dirname "$0")/../bin/bats" "$PREFIX/bin/bats"\n' \
    > "$workdir/bats-core-fake/install.sh"
  chmod +x "$workdir/bats-core-fake/install.sh"
  printf '#!/usr/bin/env bash\necho "Bats 1.99.0-fake"\n' > "$bin_dir/bats"
  chmod +x "$bin_dir/bats"
  tar -czf "$archive" -C "$workdir" "bats-core-fake"
  rm -rf "$workdir/bats-core-fake"
  printf '%s\n' "$archive"
}

# Injeta variáveis de ambiente para evitar downloads reais durante testes
# de opencode-install-deps. Chame após common_setup().
# Armazena arquivos fake em FAKE_ARCHIVES_DIR para limpeza no teardown.
common_setup_deps() {
  FAKE_ARCHIVES_DIR="$(mktemp -d)"

  export BATS_LIB_INSTALL_DIR="$TEST_HOME/.local/lib/bats"
  export BATS_BIN_DIR="$TEST_HOME/.local/bin"
  export BATS_SUPPORT_URL="$(make_fake_bats_library_archive bats-support)"
  export BATS_ASSERT_URL="$(make_fake_bats_library_archive bats-assert)"
  export BATS_FILE_URL="$(make_fake_bats_library_archive bats-file)"
  export BATS_CORE_URL="$(make_fake_bats_core_archive)"

  # Fake docling: evita instalacao real nos testes de script completo.
  # Testes que verificam MISSING usam fake_bin proprio com PATH controlado.
  mkdir -p "$TEST_HOME/.local/bin"
  printf '#!/bin/sh\necho "docling 1.0.0"\n'   > "$TEST_HOME/.local/bin/docling"
  chmod +x "$TEST_HOME/.local/bin/docling"

  # Fake bun/bunx: evita chamadas de rede ao instalar ou verificar doctree-mcp.
  # O script verifica ~/.bun/install/cache/doctree-mcp — criamos o diretorio fake.
  printf '#!/bin/sh\ncase "$1" in --version) echo "1.0.0" ;; *) exit 0 ;; esac\n' \
    > "$TEST_HOME/.local/bin/bun"
  chmod +x "$TEST_HOME/.local/bin/bun"
  ln -sf "$TEST_HOME/.local/bin/bun" "$TEST_HOME/.local/bin/bunx"
  mkdir -p "$TEST_HOME/.bun/install/cache/doctree-mcp"

  # Fake npm: evita instalacao real de bun via npm install -g bun.
  printf '#!/bin/sh\necho "npm mock ok" ; exit 0\n' > "$TEST_HOME/.local/bin/npm"
  chmod +x "$TEST_HOME/.local/bin/npm"

  # Fake codebase-memory-mcp
  printf '#!/bin/sh\necho "0.7.0"\n' > "$TEST_HOME/.local/bin/codebase-memory-mcp"
  chmod +x "$TEST_HOME/.local/bin/codebase-memory-mcp"

  export PATH="$TEST_HOME/.local/bin:$PATH"
}

common_teardown_deps() {
  rm -f "$BATS_SUPPORT_URL" "$BATS_ASSERT_URL" "$BATS_FILE_URL" "$BATS_CORE_URL"
  if [[ -n "${FAKE_ARCHIVES_DIR:-}" && "$FAKE_ARCHIVES_DIR" == /tmp/* ]]; then
    rm -rf "$FAKE_ARCHIVES_DIR"
  fi
}
