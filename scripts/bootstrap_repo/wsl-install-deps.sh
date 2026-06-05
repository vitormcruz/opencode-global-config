#!/usr/bin/env bash
# wsl-install-deps.sh
# Instala/verifica dependencias do repo e das skills do opencode-config.
#
# - Dependencias user-space (pipx, docling): instala automaticamente se possivel.
# - Dependencias que precisam de sudo (make, pandoc, ocrmypdf etc.): sugere o comando.
#
# Uso: ./scripts/bootstrap_repo/wsl-install-deps.sh [--yes] [--quiet]

set -euo pipefail

BATS_LIB_INSTALL_DIR="${BATS_LIB_INSTALL_DIR:-$HOME/.local/lib/bats}"
BATS_BIN_DIR="${BATS_BIN_DIR:-$HOME/.local/bin}"

BATS_CORE_REF="${BATS_CORE_REF:-v1.13.0}"
BATS_CORE_URL="${BATS_CORE_URL:-https://github.com/bats-core/bats-core/archive/${BATS_CORE_REF}.tar.gz}"

BATS_SUPPORT_REF="${BATS_SUPPORT_REF:-0954abb9925cad550424cebca2b99255d4eabe96}"
BATS_ASSERT_REF="${BATS_ASSERT_REF:-697471b7a89d3ab38571f38c6c7c4b460d1f5e35}"
BATS_FILE_REF="${BATS_FILE_REF:-6bee58bec7c2f4aed1a7425ccd4bdc42b4a84599}"
BATS_SUPPORT_URL="${BATS_SUPPORT_URL:-https://github.com/bats-core/bats-support/archive/${BATS_SUPPORT_REF}.tar.gz}"
BATS_ASSERT_URL="${BATS_ASSERT_URL:-https://github.com/bats-core/bats-assert/archive/${BATS_ASSERT_REF}.tar.gz}"
BATS_FILE_URL="${BATS_FILE_URL:-https://github.com/bats-core/bats-file/archive/${BATS_FILE_REF}.tar.gz}"

assume_yes=0
quiet=0

while [ $# -gt 0 ]; do
  case "$1" in
    --yes)   assume_yes=1 ;;
    --quiet) quiet=1 ;;
    --help|-h)
      cat <<'EOF'
wsl-install-deps

Verifica e instala dependencias das skills do opencode-config.

Uso:
  ./scripts/bootstrap_repo/wsl-install-deps.sh [--yes] [--quiet]

Opcoes:
  --yes      Instala sem pedir confirmacao
  --quiet    Suprime saida de progresso
  --help     Mostra esta ajuda
EOF
      exit 0
      ;;
    *) echo "Opcao desconhecida: $1" >&2; exit 2 ;;
  esac
  shift
done

say()  { [ "$quiet" -eq 0 ] && printf '%s\n' "$*" || true; }
warn() { printf '%s\n' "$*" >&2; }

# --------------------------------------------------------------------------
# Detectar OS
# --------------------------------------------------------------------------
detect_os() {
  if [ -f /proc/version ] && grep -qi microsoft /proc/version 2>/dev/null; then
    echo "wsl"
  elif [ "$(uname)" = "Darwin" ]; then
    echo "macos"
  elif [ "$(uname)" = "Linux" ]; then
    echo "linux"
  else
    echo "unknown"
  fi
}

OS="$(detect_os)"

# --------------------------------------------------------------------------
# Helpers de status
# --------------------------------------------------------------------------
status_ok()      { say "  OK       $*"; }
status_installed(){ say "  INSTALLED $*"; }
status_missing() { say "  MISSING   $*"; }
status_hint()    { say "            $*"; }

# --------------------------------------------------------------------------
# Verificar se comando existe no PATH
# --------------------------------------------------------------------------
has_cmd() { command -v "$1" >/dev/null 2>&1; }

download_to_file() {
  local source="$1"
  local dest="$2"

  case "$source" in
    file://*)
      cp "${source#file://}" "$dest"
      return 0
      ;;
  esac

  if [ -f "$source" ]; then
    cp "$source" "$dest"
    return 0
  fi

  if has_cmd curl; then
    curl -fsSL "$source" -o "$dest"
    return 0
  fi

  if has_cmd wget; then
    wget -qO "$dest" "$source"
    return 0
  fi

  return 1
}

bats_core_version_file() {
  printf '%s/.opencode-version\n' "$BATS_BIN_DIR/bats-core-install"
}

read_bats_core_ref() {
  local version_file
  version_file="$(bats_core_version_file)"
  if [ ! -f "$version_file" ]; then return 1; fi
  tr -d '\n' < "$version_file"
}

bats_core_ready() {
  local expected_ref="$1"
  local current_ref

  if [ ! -x "$BATS_BIN_DIR/bats" ]; then return 1; fi

  current_ref="$(read_bats_core_ref 2>/dev/null || true)"
  [ -n "$current_ref" ] && [ "$current_ref" = "$expected_ref" ]
}

install_bats_core() {
  local ref="$1"
  local url="$2"
  local tmp_dir archive extract_dir source_dir

  tmp_dir="$(mktemp -d)"
  archive="$tmp_dir/bats-core.tar.gz"
  extract_dir="$tmp_dir/extract"

  mkdir -p "$extract_dir" "$BATS_BIN_DIR"
  download_to_file "$url" "$archive"
  tar -xzf "$archive" -C "$extract_dir"

  source_dir=""
  for candidate in "$extract_dir"/*; do
    if [ -f "$candidate/bin/bats" ]; then
      source_dir="$candidate"
      break
    fi
  done

  if [ -z "$source_dir" ]; then
    warn "Falha ao localizar bin/bats em $url"
    rm -rf "$tmp_dir"
    return 1
  fi

  # Instala usando o install.sh embutido do bats-core (para ~/.local)
  PREFIX="$HOME/.local" bash "$source_dir/install.sh" "$HOME/.local" >/dev/null 2>&1

  # Salva versão instalada
  local install_dir="$BATS_BIN_DIR/bats-core-install"
  mkdir -p "$install_dir"
  printf '%s\n' "$ref" > "$install_dir/.opencode-version"

  rm -rf "$tmp_dir"
}

ensure_bats_core() {
  say "[bats-core] Runner dos testes automatizados"

  if bats_core_ready "$BATS_CORE_REF"; then
    status_ok "bats $("$BATS_BIN_DIR/bats" --version 2>/dev/null | awk '{print $NF}' || echo "$BATS_CORE_REF")"
    say ""
    return 0
  fi

  status_missing "bats-core $BATS_CORE_REF"
  status_hint "Destino: $BATS_BIN_DIR/bats"

  if ! has_cmd tar || ! has_cmd gzip; then
    status_hint "Instale tar e gzip para baixar e extrair bats-core"
    say ""
    return 0
  fi

  if ! has_cmd curl && ! has_cmd wget && [ ! -f "$BATS_CORE_URL" ] && [ "${BATS_CORE_URL#file://}" = "$BATS_CORE_URL" ]; then
    status_hint "Instale curl ou wget para baixar bats-core"
    say ""
    return 0
  fi

  if confirm_action "  Instalar bats-core $BATS_CORE_REF em $BATS_BIN_DIR agora?"; then
    if install_bats_core "$BATS_CORE_REF" "$BATS_CORE_URL"; then
      status_installed "bats-core $BATS_CORE_REF"
    else
      status_missing "bats-core"
      status_hint "Falha ao instalar bats-core"
    fi
  else
    status_hint "Para instalar depois, rode novamente o bootstrap"
  fi
  say ""
}

bats_lib_version_file() {
  printf '%s/.opencode-version\n' "$BATS_LIB_INSTALL_DIR/$1"
}

read_bats_lib_ref() {
  local version_file
  version_file="$(bats_lib_version_file "$1")"

  if [ ! -f "$version_file" ]; then
    return 1
  fi

  tr -d '\n' < "$version_file"
}

bats_library_ready() {
  local name="$1"
  local expected_ref="$2"
  local current_ref

  if [ ! -f "$BATS_LIB_INSTALL_DIR/$name/load.bash" ]; then
    return 1
  fi

  current_ref="$(read_bats_lib_ref "$name" 2>/dev/null || true)"
  [ -n "$current_ref" ] && [ "$current_ref" = "$expected_ref" ]
}

install_bats_library() {
  local name="$1"
  local ref="$2"
  local url="$3"
  local tmp_dir archive extract_dir source_dir version_file

  tmp_dir="$(mktemp -d)"
  archive="$tmp_dir/$name.tar.gz"
  extract_dir="$tmp_dir/extract"

  mkdir -p "$extract_dir" "$BATS_LIB_INSTALL_DIR"
  download_to_file "$url" "$archive"
  tar -xzf "$archive" -C "$extract_dir"

  source_dir=""
  for candidate in "$extract_dir"/*; do
    if [ -f "$candidate/load.bash" ]; then
      source_dir="$candidate"
      break
    fi
  done

  if [ -z "$source_dir" ]; then
    warn "Falha ao localizar load.bash em $url"
    rm -rf "$tmp_dir"
    return 1
  fi

  rm -rf "$BATS_LIB_INSTALL_DIR/$name"
  cp -R "$source_dir" "$BATS_LIB_INSTALL_DIR/$name"
  version_file="$(bats_lib_version_file "$name")"
  printf '%s\n' "$ref" > "$version_file"
  rm -rf "$tmp_dir"
}

ensure_bats_library() {
  local name="$1"
  local ref="$2"
  local url="$3"

  say "[$name] Biblioteca auxiliar do BATS"
  if bats_library_ready "$name" "$ref"; then
    status_ok "$name $ref"
    say ""
    return 0
  fi

  status_missing "$name"
  status_hint "Destino: $BATS_LIB_INSTALL_DIR/$name"

  if ! has_cmd tar || ! has_cmd gzip; then
    status_hint "Instale tar e gzip para baixar e extrair $name"
    say ""
    return 0
  fi

  if ! has_cmd curl && ! has_cmd wget && [ ! -f "$url" ] && [ "${url#file://}" = "$url" ]; then
    status_hint "Instale curl ou wget para baixar $name"
    say ""
    return 0
  fi

  if confirm_action "  Instalar $name em $BATS_LIB_INSTALL_DIR agora?"; then
    if install_bats_library "$name" "$ref" "$url"; then
      status_installed "$name"
    else
      status_missing "$name"
      status_hint "Falha ao instalar $name"
    fi
  else
    status_hint "Para instalar depois, rode novamente o bootstrap"
  fi
  say ""
}

# --------------------------------------------------------------------------
# Instalar pipx em user-space (sem sudo)
# --------------------------------------------------------------------------
install_pipx_userspace() {
  if has_cmd pip3; then
    say "  -> Tentando: pip3 install --user pipx"
    pip3 install --user pipx --quiet && return 0
  fi
  if has_cmd pip; then
    say "  -> Tentando: pip install --user pipx"
    pip install --user pipx --quiet && return 0
  fi
  return 1
}

# --------------------------------------------------------------------------
# Verificar se python3 atende versao minima (3.10+)
# Retorna 0 se ok, 1 se ausente ou versao menor que 3.10
# --------------------------------------------------------------------------
PYTHON3_VERSION=""
check_python3_version() {
  if ! has_cmd python3; then return 1; fi
  PYTHON3_VERSION="$(python3 --version 2>/dev/null | awk '{print $2}')"
  local minor
  minor="$(echo "$PYTHON3_VERSION" | cut -d. -f2)"
  [ -n "$minor" ] && [ "$minor" -ge 10 ] 2>/dev/null
}

# --------------------------------------------------------------------------
# Instalar docling via pipx
# --------------------------------------------------------------------------
install_docling_pipx() {
  say "  -> Instalando docling via pipx..."
  pipx install docling 2>&1 | while IFS= read -r line; do
    say "     $line"
  done
  pipx ensurepath 2>/dev/null || true
}

# --------------------------------------------------------------------------
# Confirmar acao (respeita --yes)
# --------------------------------------------------------------------------
confirm_action() {
  local msg="$1"
  if [ "$assume_yes" -eq 1 ]; then return 0; fi
  if ! [ -t 0 ] || ! [ -t 1 ]; then return 0; fi
  printf '%s [y/N] ' "$msg"
  read -r ans || true
  case "$ans" in y|Y|yes|YES) return 0 ;; esac
  return 1
}

# --------------------------------------------------------------------------
# Lista de pacotes sudo necessarios
# --------------------------------------------------------------------------
SUDO_PKGS=()

need_sudo_pkg() {
  SUDO_PKGS+=("$1")
}

# --------------------------------------------------------------------------
# Main: verificar cada dependencia
# --------------------------------------------------------------------------
say ""
say "=== opencode-install-deps ==="
say "OS detectado: $OS"
say ""
say "--- Verificando dependencias ---"
say ""

# --- make ---
say "[make] Necessario para executar o Makefile de testes"
if has_cmd make; then
  status_ok "make $(make --version 2>/dev/null | head -1 | awk '{print $3}')"
else
  status_missing "make"
  case "$OS" in
    wsl|linux)
      status_hint "Instalar: sudo apt-get install -y make"
      need_sudo_pkg "make"
      ;;
    macos)
      status_hint "Instalar: brew install make"
      ;;
    *)
      status_hint "Instale o GNU Make para usar o Makefile do repo"
      ;;
  esac
fi
say ""

ensure_bats_core

ensure_bats_library "bats-support" "$BATS_SUPPORT_REF" "$BATS_SUPPORT_URL"
ensure_bats_library "bats-assert" "$BATS_ASSERT_REF" "$BATS_ASSERT_URL"
ensure_bats_library "bats-file" "$BATS_FILE_REF" "$BATS_FILE_URL"

# --- pandoc ---
say "[pandoc] Skill: md-export"
if has_cmd pandoc; then
  status_ok "pandoc $(pandoc --version 2>/dev/null | head -1 | awk '{print $2}')"
else
  status_missing "pandoc"
  case "$OS" in
    wsl|linux)
      status_hint "Instalar: sudo apt-get install -y pandoc"
      need_sudo_pkg "pandoc"
      ;;
    macos)
      status_hint "Instalar: brew install pandoc"
      ;;
    *)
      status_hint "Instalar: https://pandoc.org/installing.html"
      ;;
  esac
fi
say ""

# --- pipx ---
say "[pipx] Necessario para instalar docling"
if has_cmd pipx; then
  status_ok "pipx $(pipx --version 2>/dev/null | head -1)"
else
  status_missing "pipx"
  case "$OS" in
    wsl|linux)
      # Tentar instalar via pip --user primeiro
      if install_pipx_userspace 2>/dev/null; then
        # Recarregar PATH
        export PATH="$HOME/.local/bin:$PATH"
        if has_cmd pipx; then
          status_installed "pipx (via pip --user)"
        else
          status_missing "pipx (pip install ok mas nao encontrado no PATH)"
          status_hint "Execute: export PATH=\"\$HOME/.local/bin:\$PATH\""
          status_hint "Ou: sudo apt-get install -y pipx"
          need_sudo_pkg "pipx"
        fi
      else
        status_hint "Instalar: sudo apt-get install -y pipx"
        status_hint "Alternativa: pip3 install --user pipx"
        need_sudo_pkg "pipx"
      fi
      ;;
    macos)
      status_hint "Instalar: brew install pipx"
      ;;
    *)
      status_hint "Instalar: pip3 install --user pipx"
      ;;
  esac
fi
say ""

# --- Python 3.10+ ---
say "[python3] Requerido >= 3.10 para docling"
if check_python3_version; then
  status_ok "python3 $PYTHON3_VERSION"
else
  status_missing "Python >= 3.10 (sistema tem ${PYTHON3_VERSION:-nenhum})"
  status_hint "Requer Ubuntu 22.04+ ou equivalente com Python 3.10+"
  status_hint "WSL: wsl --install -d Ubuntu-24.04"
fi
say ""

# --- docling ---
say "[docling] Skill: doc-extract"
if has_cmd docling; then
  status_ok "docling $(docling --version 2>/dev/null | head -1 | awk '{print $NF}' || echo '(versao desconhecida)')"
elif ! check_python3_version; then
  status_missing "docling (requer Python >= 3.10)"
elif ! has_cmd pipx; then
  status_missing "docling"
  status_hint "Primeiro instale pipx, depois: pipx install docling"
elif confirm_action "  Instalar docling via pipx agora?"; then
  install_docling_pipx
  export PATH="$HOME/.local/bin:$PATH"
  if has_cmd docling; then
    status_installed "docling"
  else
    status_missing "docling instalado mas nao encontrado no PATH"
    status_hint "Execute: export PATH=\"\$HOME/.local/bin:\$PATH\""
  fi
else
  status_missing "docling"
  status_hint "Para instalar depois: pipx install docling"
fi
say ""

# --- conversor SVG ---
say "[resvg ou rsvg-convert] Skill: svg-to-image"
if has_cmd resvg; then
  status_ok "resvg"
elif has_cmd rsvg-convert; then
  status_ok "rsvg-convert"
else
  status_missing "resvg"
  status_missing "rsvg-convert"
  case "$OS" in
    wsl|linux)
      status_hint "Instalar: sudo apt-get install -y librsvg2-bin"
      need_sudo_pkg "librsvg2-bin"
      ;;
    macos)
      status_hint "Instalar: brew install librsvg"
      ;;
    *)
      status_hint "Instale resvg ou rsvg-convert para usar a skill svg-to-image"
      ;;
  esac
fi
say ""

# --- Playwright (browser-testing) ---
say "[playwright] Skill: browser-testing (via WSL)"
if has_cmd playwright; then
  status_ok "playwright"
else
  status_missing "playwright"
  status_hint "Instalar: bash scripts/browser-test/install-playwright.sh --yes"
fi
say ""

# --- doctree MCP (requer bun via npm) ---
say "[doctree] MCP de navegacao de documentacao"
export PATH="$HOME/.bun/bin:$PATH"
doctree_installed=0

if has_cmd bun && ls "$HOME/.bun/install/cache/doctree-mcp" &>/dev/null 2>&1; then
  status_ok "doctree-mcp (bun $(bun --version 2>/dev/null | head -1))"
  doctree_installed=1
fi

if [ "$doctree_installed" -eq 0 ]; then
  if ! has_cmd npm; then
    status_missing "doctree (requer npm/bun)"
    status_hint "Instale Node.js (npm) e rode o bootstrap novamente"
    need_sudo_pkg "nodejs"  # npm vem com node
  else
    say "  -> Instalando bun via npm..."
    npm config set prefix "$HOME/.local" 2>/dev/null || true
    export PATH="$HOME/.local/bin:$PATH"

    if [ "$assume_yes" -eq 0 ] && [ -t 0 ] && [ -t 1 ]; then
      printf '  Instalar bun agora? [y/N] '
      read -r ans || true
      case "$ans" in y|Y|yes|YES) ;; *) status_hint "Instalar manualmente: npm install -g bun"; say ""; exit 0 ;; esac
    fi

    if npm install -g bun 2>&1 | while IFS= read -r line; do say "     $line"; done; then
      export PATH="$HOME/.bun/bin:$PATH"
      if has_cmd bun; then
        status_installed "bun $(bun --version 2>/dev/null | head -1)"
        say "  -> Verificando doctree-mcp no cache do bun..."
        if ls "$HOME/.bun/install/cache/doctree-mcp" &>/dev/null 2>&1; then
          status_installed "doctree-mcp"
          doctree_installed=1
        else
          status_missing "doctree"
          status_hint "Bun instalado, mas doctree-mcp nao encontrado no cache."
          status_hint "Acesse a internet publica e rode: bunx doctree-mcp --help"
        fi
      else
        status_missing "bun (instalado mas nao encontrado no PATH)"
        status_hint "Execute: export PATH=\"\$HOME/.bun/bin:\$PATH\""
      fi
    else
      status_missing "doctree"
      status_hint "Falha ao instalar bun. Instale manualmente: npm install -g bun"
    fi
  fi
fi
say ""

# --- codebase-memory-mcp ---
say "[codebase-memory-mcp] MCP de memoria do codebase"
export PATH="$HOME/.local/bin:$PATH"
if has_cmd codebase-memory-mcp; then
  if codebase-memory-mcp --version &>/dev/null; then
    status_ok "codebase-memory-mcp ($(codebase-memory-mcp --version 2>&1 | head -1 || echo ok))"
  else
    # Binario incompativel — npm reinstall NAO resolve (binario pre-compilado)
    error_output="$(codebase-memory-mcp --version 2>&1 || true)"
    status_missing "codebase-memory-mcp (binario pre-compilado incompativel)"
    say "     Erro: $error_output"
    say ""
    say "     Este binario foi compilado com glibc >= 2.38"
    say "     Seu glibc: $(ldd --version 2>&1 | head -1)"
    say ""
    say "     REQUER Ubuntu 24.04+ (WSL). npm reinstall NAO resolve."
  fi
else
  status_missing "codebase-memory-mcp"
  status_hint "Instalar: npm install -g codebase-memory-mcp (requer npm)"
fi
say ""

# --- mcp (avelino) ---
say "[mcp (avelino)] MCP CLI"
MCP_INSTALL_DIR="${HOME}/.local/bin"
MCP_URL="${MCP_URL:-https://github.com/avelino/mcp/releases/latest/download/mcp-linux-amd64}"
MCP_EXPECTED_SHA="${MCP_EXPECTED_SHA:-}"

if has_cmd mcp; then
  status_ok "mcp ($(mcp --version 2>/dev/null | head -1 || echo ok))"
else
  if ! has_cmd curl; then
    status_missing "mcp"
    status_hint "Instale curl para baixar o mcp automaticamente"
  else
    _mcp_tmp="$(mktemp)"
    if curl -fsSL "$MCP_URL" -o "$_mcp_tmp" 2>/dev/null; then
      _mcp_sha="$(sha256sum "$_mcp_tmp" | awk '{print $1}')"
      say "            SHA do arquivo: $_mcp_sha"
      if [ -n "$MCP_EXPECTED_SHA" ] && [ "$_mcp_sha" != "$MCP_EXPECTED_SHA" ]; then
        say "  ERROR: SHA mismatch ao instalar mcp"
        say "         SHA esperado no repo: $MCP_EXPECTED_SHA"
        say "         SHA real do arquivo:  $_mcp_sha"
        say "         Para atualizar: MCP_EXPECTED_SHA=<novo valor>"
        rm -f "$_mcp_tmp"
        exit 1
      fi
      mkdir -p "$MCP_INSTALL_DIR"
      mv "$_mcp_tmp" "$MCP_INSTALL_DIR/mcp"
      chmod +x "$MCP_INSTALL_DIR/mcp"
      status_installed "mcp"
    else
      rm -f "$_mcp_tmp"
      status_missing "mcp"
      status_hint "Falha ao baixar mcp. Tente manualmente: $MCP_URL"
    fi
  fi
fi
say ""

# --------------------------------------------------------------------------
# Sumario de comandos sudo necessarios
# --------------------------------------------------------------------------
if [ ${#SUDO_PKGS[@]} -gt 0 ]; then
  say "--- Pacotes que precisam de sudo ---"
  say ""
  case "$OS" in
    wsl|linux)
      say "Execute manualmente:"
      say ""
      say "  sudo apt-get update && sudo apt-get install -y ${SUDO_PKGS[*]}"
      say ""
      ;;
    macos)
      say "Execute manualmente:"
      say ""
      say "  brew install ${SUDO_PKGS[*]}"
      say ""
      ;;
  esac
else
  say "--- Tudo verificado, nenhum comando sudo necessario ---"
  say ""
fi

say "=== Concluido ==="
