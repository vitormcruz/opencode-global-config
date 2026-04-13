#!/usr/bin/env bash
# tests/opencode-int-test/docker/container-test-opencode.sh — gerencia o container Docker dos testes do OpenCode
#
# Uso:
#   bash tests/opencode-int-test/docker/container-test-opencode.sh --up
#   bash tests/opencode-int-test/docker/container-test-opencode.sh --down
#   bash tests/opencode-int-test/docker/container-test-opencode.sh --help

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

CONTAINER_NAME="opencode-config-test"
IMAGE_NAME="opencode-config-test:latest"
PORT=4196

# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

log()  { echo "[container-test-opencode] $*"; }
warn() { echo "[container-test-opencode] WARN: $*" >&2; }
die()  { echo "[container-test-opencode] ERROR: $*" >&2; exit 1; }

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

remove_container_if_exists() {
  if container_exists; then
    docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  fi
}

# ---------------------------------------------------------------------------
# Seleção de modelo
# ---------------------------------------------------------------------------

list_models() {
  docker run --rm "$IMAGE_NAME" /root/.opencode/bin/opencode --pure models
}

choose_model_interactively() {
  local models="$1"
  local choice=1
  local count=0
  local line

  printf '%s\n' "Modelos disponíveis:" >&2
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    count=$((count + 1))
    printf '  %d) %s\n' "$count" "$line" >&2
  done <<EOF
$models
EOF
  printf '\n' >&2

  while :; do
    read -rp "Escolha o número do modelo: " choice >&2
    case "$choice" in
      ''|*[!0-9]*)
        printf '%s\n' "Escolha inválida. Digite um número da lista." >&2
        ;;
      *)
        if [ "$choice" -ge 1 ] && [ "$choice" -le "$count" ]; then
          break
        fi
        printf '%s\n' "Escolha inválida. Digite um número da lista." >&2
        ;;
    esac
  done

  count=0
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    count=$((count + 1))
    if [ "$count" -eq "$choice" ]; then
      printf '%s\n' "$line"
      return 0
    fi
  done <<EOF
$models
EOF

  return 1
}

select_model_if_needed() {
  if [[ -n "${OPENCODE_TEST_MODEL:-}" ]]; then
    log "Modelo já configurado: ${OPENCODE_TEST_MODEL}"
    return 0
  fi

  log "Detectando modelos disponíveis..."
  local models preferred_count preferred_model
  models="$(list_models)"
  if [[ -z "$models" ]]; then
    die "Não foi possível listar os modelos disponíveis."
  fi

  preferred_count="$(printf '%s\n' "$models" | grep -ic 'big[- ]pickle' || true)"
  if [[ "$preferred_count" -eq 1 ]]; then
    preferred_model="$(printf '%s\n' "$models" | grep -i 'big[- ]pickle' | head -1)"
    export OPENCODE_TEST_MODEL="$preferred_model"
    log "Modelo selecionado automaticamente: ${OPENCODE_TEST_MODEL}"
    return 0
  fi

  if [[ "$preferred_count" -gt 1 ]]; then
    warn "Mais de um modelo compatível com 'Big Pickle' foi encontrado."
  else
    warn "Modelo preferido 'Big Pickle' não encontrado."
  fi

  OPENCODE_TEST_MODEL="$(choose_model_interactively "$models")"
  export OPENCODE_TEST_MODEL
  log "Modelo selecionado: ${OPENCODE_TEST_MODEL}"
}

# ---------------------------------------------------------------------------
# Build da imagem
# ---------------------------------------------------------------------------

prepare_mock_artifacts() {
  log "Preparando artefatos do mock MCP..."
  npm --prefix "$REPO_ROOT/tests/opencode-int-test/mcp-mock" install
}

build_image() {
  prepare_mock_artifacts
  log "Construindo imagem Docker '${IMAGE_NAME}'..."
  docker build -t "$IMAGE_NAME" -f "$SCRIPT_DIR/Dockerfile" "$REPO_ROOT"
  log "Imagem construída com sucesso."
}

# ---------------------------------------------------------------------------
# Start do container
# ---------------------------------------------------------------------------

start_container() {
  if container_running; then
    log "Container '${CONTAINER_NAME}' já está em execução."
  else
    if container_exists; then
      log "Container '${CONTAINER_NAME}' já existe, recriando..."
      remove_container_if_exists
    fi
    log "Criando e iniciando container '${CONTAINER_NAME}'..."
    docker run -d \
      --name "$CONTAINER_NAME" \
      -p "${PORT}:4096" \
      -e "OPENCODE_TEST_MODEL=${OPENCODE_TEST_MODEL:-opencode/big-pickle}" \
      "$IMAGE_NAME"
  fi

  # Aguarda OpenCode estar disponível
  log "Aguardando OpenCode ficar disponível na porta ${PORT}..."
  local retries=30
  local i=0
  while [[ $i -lt $retries ]]; do
    if curl -sf "http://127.0.0.1:${PORT}/" &>/dev/null; then
      log "OpenCode disponível em http://127.0.0.1:${PORT}/"
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
# Stop
# ---------------------------------------------------------------------------

stop_container() {
  if container_running; then
    log "Parando container '${CONTAINER_NAME}'..."
    docker stop "$CONTAINER_NAME"
  else
    log "Container '${CONTAINER_NAME}' não está em execução."
  fi
}

case "${1:-}" in
  --help|-h)
    cat <<'EOF'
Uso: bash tests/opencode-int-test/docker/container-test-opencode.sh [opção]

--up       Faz o setup interativo na primeira execução e sobe o container
--down     Para o container de testes
--help     Exibe esta ajuda

O modelo é configurado via variável de ambiente OPENCODE_TEST_MODEL.
Se não estiver definida, o script tenta detectar automaticamente (preferindo
'big-pickle') ou solicita escolha interativa.
EOF
    exit 0
    ;;
  --up)
    check_docker
    build_image
    select_model_if_needed
    start_container
    ;;
  --down)
    check_docker
    stop_container
    ;;
  *)
    die "Opção desconhecida: ${1:-}. Use --help para ver as opções."
    ;;
esac
