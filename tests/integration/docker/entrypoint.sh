#!/usr/bin/env bash
set -euo pipefail

# Substitui o modelo no opencode.json com OPENCODE_TEST_MODEL
if [[ -n "${OPENCODE_TEST_MODEL:-}" ]]; then
  echo "[entrypoint] Aplicando modelo: ${OPENCODE_TEST_MODEL}"
  tmp="$(mktemp)"
  jq --arg model "$OPENCODE_TEST_MODEL" '
    .agent.plan.model = $model |
    .agent.build.model = $model
  ' /opt/opencode-config/opencode.json > "$tmp" && mv "$tmp" /opt/opencode-config/opencode.json
else
  echo "[entrypoint] WARN: OPENCODE_TEST_MODEL não definido, usando config padrão." >&2
fi

# Mescla seção provider do OPENCODE_CONFIG (montado como volume) no opencode.json
if [[ -n "${OPENCODE_CONFIG:-}" && -f "${OPENCODE_CONFIG}" ]]; then
  host_provider="$(jq '.provider // empty' "$OPENCODE_CONFIG" 2>/dev/null || true)"
  if [[ -n "$host_provider" ]]; then
    echo "[entrypoint] Mesclando provider de OPENCODE_CONFIG..."
    tmp="$(mktemp)"
    jq --argjson prov "$host_provider" '
      .provider = (.provider // {} | . * $prov)
    ' /opt/opencode-config/opencode.json > "$tmp" && mv "$tmp" /opt/opencode-config/opencode.json
  fi
fi

exec /root/.opencode/bin/opencode --pure serve --hostname 0.0.0.0 --port 4096
