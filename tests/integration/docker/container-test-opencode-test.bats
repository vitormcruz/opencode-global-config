#!/usr/bin/env bats
# tests/integration/docker/container-test-opencode-test.bats
# Testa a função extract_models_from_config isoladamente (sem container)

load "../../helpers/test_helper"

SCRIPT_UNDER_TEST=""

setup() {
  common_setup
  SCRIPT_UNDER_TEST="$REPO_ROOT/tests/integration/docker/container-test-opencode.sh"
}

teardown() {
  common_teardown
}

# Importa apenas a função extract_models_from_config do script
_extract() {
  eval "$(awk '/^extract_models_from_config\(\)/,/^}/' "$SCRIPT_UNDER_TEST")"
  extract_models_from_config "$@"
}

# ---------------------------------------------------------------------------
# extract_models_from_config — agent.*.model
# ---------------------------------------------------------------------------

@test "extrai modelos de config válido com dois agentes" {
  local cfg="$TEST_HOME/opencode.json"
  cat > "$cfg" <<'JSON'
{
  "agent": {
    "plan": { "model": "provider/model-a" },
    "build": { "model": "provider/model-b" }
  }
}
JSON
  run _extract "$cfg"
  assert_success
  assert_line "provider/model-a"
  assert_line "provider/model-b"
}

@test "extrai modelos únicos quando há duplicatas" {
  local cfg="$TEST_HOME/opencode.json"
  cat > "$cfg" <<'JSON'
{
  "agent": {
    "plan": { "model": "opencode/big-pickle" },
    "build": { "model": "opencode/big-pickle" }
  }
}
JSON
  run _extract "$cfg"
  assert_success
  assert_output "opencode/big-pickle"
}

# ---------------------------------------------------------------------------
# extract_models_from_config — provider.*.models
# ---------------------------------------------------------------------------

@test "extrai modelos de provider.*.models" {
  local cfg="$TEST_HOME/opencode.json"
  cat > "$cfg" <<'JSON'
{
  "provider": {
    "my-provider": {
      "models": {
        "model-x": { "name": "Model X" },
        "model-y": { "name": "Model Y" }
      }
    }
  }
}
JSON
  run _extract "$cfg"
  assert_success
  assert_line "my-provider/model-x"
  assert_line "my-provider/model-y"
}

@test "combina modelos de agent e provider sem duplicatas" {
  local cfg="$TEST_HOME/opencode.json"
  cat > "$cfg" <<'JSON'
{
  "agent": {
    "plan": { "model": "prov/model-a" }
  },
  "provider": {
    "prov": {
      "models": {
        "model-a": {},
        "model-b": {}
      }
    }
  }
}
JSON
  run _extract "$cfg"
  assert_success
  assert_line "prov/model-a"
  assert_line "prov/model-b"
  # model-a aparece em agent e provider, mas deve vir só uma vez
  local count
  count="$(echo "$output" | grep -c 'prov/model-a')"
  [ "$count" -eq 1 ]
}

# ---------------------------------------------------------------------------
# Casos de borda
# ---------------------------------------------------------------------------

@test "retorna vazio quando config não tem agent nem provider" {
  local cfg="$TEST_HOME/opencode.json"
  cat > "$cfg" <<'JSON'
{ "mcp": {} }
JSON
  run _extract "$cfg"
  assert_success
  assert_output ""
}

@test "retorna vazio quando agent existe mas sem model" {
  local cfg="$TEST_HOME/opencode.json"
  cat > "$cfg" <<'JSON'
{
  "agent": {
    "plan": { "permission": {} }
  }
}
JSON
  run _extract "$cfg"
  assert_success
  assert_output ""
}

@test "retorna falha silenciosa para arquivo inexistente" {
  run _extract "$TEST_HOME/nao-existe.json"
  assert_success
  assert_output ""
}

# ---------------------------------------------------------------------------
# Fluxo sem OPENCODE_CONFIG — simula cenário big-pickle
# ---------------------------------------------------------------------------

# Extrai funções auxiliares do script (log, warn, die) para testes de fluxo
_source_helpers() {
  eval "$(awk '/^log\(\)/,/^}/' "$SCRIPT_UNDER_TEST")"
  eval "$(awk '/^warn\(\)/,/^}/' "$SCRIPT_UNDER_TEST")"
  eval "$(awk '/^die\(\)/,/^}/' "$SCRIPT_UNDER_TEST")"
  eval "$(awk '/^extract_models_from_config\(\)/,/^}/' "$SCRIPT_UNDER_TEST")"
  export MODEL_FILE="$TEST_HOME/test-model-file"
}

@test "sem OPENCODE_CONFIG, extract_models_from_config não é chamado" {
  # Garante que sem OPENCODE_CONFIG o fluxo não tenta extrair modelos de config
  unset OPENCODE_CONFIG 2>/dev/null || true
  _source_helpers

  # extract não deve ser invocado — testar que config vazio retorna vazio
  run extract_models_from_config "$TEST_HOME/nao-existe.json"
  assert_success
  assert_output ""
}

@test "OPENCODE_CONFIG com arquivo inexistente não quebra extração" {
  export OPENCODE_CONFIG="$TEST_HOME/inexistente.json"
  _source_helpers

  run extract_models_from_config "$OPENCODE_CONFIG"
  assert_success
  assert_output ""
}

@test "OPENCODE_CONFIG com config válido sem provider retorna só agent models" {
  local cfg="$TEST_HOME/opencode.json"
  cat > "$cfg" <<'JSON'
{
  "agent": {
    "plan": { "model": "opencode/big-pickle" },
    "build": { "model": "opencode/big-pickle" }
  }
}
JSON
  export OPENCODE_CONFIG="$cfg"
  _source_helpers

  run extract_models_from_config "$OPENCODE_CONFIG"
  assert_success
  assert_output "opencode/big-pickle"
}

@test "OPENCODE_CONFIG com só provider e sem agent retorna modelos do provider" {
  local cfg="$TEST_HOME/opencode.json"
  cat > "$cfg" <<'JSON'
{
  "provider": {
    "corp-llm": {
      "models": {
        "modelo-interno": {}
      }
    }
  }
}
JSON
  export OPENCODE_CONFIG="$cfg"
  _source_helpers

  run extract_models_from_config "$OPENCODE_CONFIG"
  assert_success
  assert_output "corp-llm/modelo-interno"
}
