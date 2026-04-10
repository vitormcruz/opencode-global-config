#!/usr/bin/env bash
# tests/setup-container.sh — gerencia o container Docker para testes comportamentais
#
# Uso:
#   bash tests/setup-container.sh          # interativo: cria ou reutiliza container
#   bash tests/setup-container.sh --start  # inicia container existente (não interativo)
#   bash tests/setup-container.sh --stop   # para o container
#   bash tests/setup-container.sh --clean  # para e remove o container
#   bash tests/setup-container.sh --help   # exibe ajuda

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEST_ENV="$SCRIPT_DIR/.test-env"

CONTAINER_NAME="opencode-config-test"
IMAGE_NAME="opencode-config-test:latest"
PORT=4096

# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

log()  { echo "[setup-container] $*"; }
warn() { echo "[setup-container] WARN: $*" >&2; }
die()  { echo "[setup-container] ERROR: $*" >&2; exit 1; }

check_docker() {
  if ! command -v docker &>/dev/null; then
    die "Docker não encontrado. Instale Docker para executar testes comportamentais."
  fi
  if ! docker info &>/dev/null 2>&1; then
    die "Docker daemon não está em execução."
  fi
}

container_exists() {
  docker ps -a --filter "name=^${CONTAINER_NAME}$" --format '{{.Names}}' \
    | grep -q "^${CONTAINER_NAME}$"
}

container_running() {
  docker ps --filter "name=^${CONTAINER_NAME}$" --format '{{.Names}}' \
    | grep -q "^${CONTAINER_NAME}$"
}

# ---------------------------------------------------------------------------
# Setup interativo — pergunta sobre provider/modelo
# ---------------------------------------------------------------------------

interactive_setup() {
  log "Container '${CONTAINER_NAME}' não existe. Configuração inicial."
  echo ""

  # Escolha do modo
  echo "Como deseja configurar o provider do OpenCode no container?"
  echo "  1) Provider configurado (Anthropic, OpenAI, Google, etc.)"
  echo "  2) OpenCode Zen (modelos gratuitos — usa OPENCODE_API_KEY)"
  echo ""
  read -rp "Escolha [1/2]: " mode_choice

  case "$mode_choice" in
    1)
      read -rp "Provider (ex: anthropic, openai, google): " provider
      read -rp "Modelo (ex: anthropic/claude-sonnet-4-20250514): " model
      read -rp "Nome da variável de ambiente do HOST com a API key (ex: ANTHROPIC_API_KEY): " api_key_var
      mode="provider"
      ;;
    2)
      provider="opencode"
      read -rp "Modelo Zen (ex: anthropic/claude-3-5-haiku): " model
      api_key_var="OPENCODE_API_KEY"
      mode="zen"
      ;;
    *)
      die "Opção inválida: $mode_choice"
      ;;
  esac

  # Salva configuração (NUNCA salva a key real)
  cat > "$TEST_ENV" <<EOF
OPENCODE_TEST_MODE=${mode}
OPENCODE_TEST_PROVIDER=${provider}
OPENCODE_TEST_MODEL=${model}
OPENCODE_TEST_API_KEY_VAR=${api_key_var}
EOF
  log "Configuração salva em $TEST_ENV"
}

# ---------------------------------------------------------------------------
# Build da imagem
# ---------------------------------------------------------------------------

build_image() {
  log "Construindo imagem Docker '${IMAGE_NAME}'..."
  docker build -t "$IMAGE_NAME" -f "$SCRIPT_DIR/Dockerfile" "$REPO_ROOT"
  log "Imagem construída com sucesso."
}

# ---------------------------------------------------------------------------
# Start do container
# ---------------------------------------------------------------------------

start_container() {
  if ! [[ -f "$TEST_ENV" ]]; then
    die "Arquivo $TEST_ENV não encontrado. Execute sem flags para configuração interativa."
  fi

  # Lê variáveis salvas
  # shellcheck source=/dev/null
  source "$TEST_ENV"

  # Resolve o valor real da API key do host
  api_key_value="${!OPENCODE_TEST_API_KEY_VAR:-}"
  if [[ -z "$api_key_value" ]]; then
    warn "Variável de ambiente '${OPENCODE_TEST_API_KEY_VAR}' não definida no host."
    warn "Testes comportamentais que precisam de LLM vão falhar."
  fi

  if container_exists; then
    log "Container '${CONTAINER_NAME}' já existe. Iniciando..."
    docker start "$CONTAINER_NAME"
  else
    log "Criando e iniciando container '${CONTAINER_NAME}'..."
    docker run -d \
      --name "$CONTAINER_NAME" \
      -p "${PORT}:${PORT}" \
      -e "OPENCODE_TEST_PROVIDER=${OPENCODE_TEST_PROVIDER}" \
      -e "OPENCODE_TEST_MODEL=${OPENCODE_TEST_MODEL}" \
      -e "${OPENCODE_TEST_API_KEY_VAR}=${api_key_value}" \
      "$IMAGE_NAME"
  fi

  # Aguarda OpenCode estar disponível
  log "Aguardando OpenCode ficar disponível na porta ${PORT}..."
  local retries=30
  local i=0
  while [[ $i -lt $retries ]]; do
    if curl -sf "http://localhost:${PORT}/" &>/dev/null; then
      log "OpenCode disponível em http://localhost:${PORT}/"
      return 0
    fi
    sleep 2
    ((i++))
  done

  warn "OpenCode não respondeu após $((retries * 2))s. Verifique os logs:"
  warn "  docker logs ${CONTAINER_NAME}"
  return 1
}

# ---------------------------------------------------------------------------
# Stop / Clean
# ---------------------------------------------------------------------------

stop_container() {
  if container_running; then
    log "Parando container '${CONTAINER_NAME}'..."
    docker stop "$CONTAINER_NAME"
  else
    log "Container '${CONTAINER_NAME}' não está em execução."
  fi
}

clean_container() {
  stop_container || true
  if container_exists; then
    log "Removendo container '${CONTAINER_NAME}'..."
    docker rm "$CONTAINER_NAME"
  fi
  log "Container removido. Próxima execução fará setup interativo novamente."
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

case "${1:-}" in
  --help|-h)
    cat <<'EOF'
Uso: bash tests/setup-container.sh [opção]

Sem opção  — setup interativo: cria imagem + container (ou reutiliza)
--start    — inicia container existente usando .test-env
--stop     — para o container
--clean    — para e remove o container
--help     — exibe esta ajuda

O arquivo tests/.test-env é gitignored e nunca deve ser commitado.
A API key real nunca é salva — apenas o nome da variável de ambiente do host.
EOF
    exit 0
    ;;
  --start)
    check_docker
    if ! container_exists; then
      build_image
    fi
    start_container
    ;;
  --stop)
    check_docker
    stop_container
    ;;
  --clean)
    check_docker
    clean_container
    ;;
  "")
    check_docker
    if ! container_exists; then
      interactive_setup
      build_image
    fi
    start_container
    ;;
  *)
    die "Opção desconhecida: $1. Use --help para ver as opções."
    ;;
esac
