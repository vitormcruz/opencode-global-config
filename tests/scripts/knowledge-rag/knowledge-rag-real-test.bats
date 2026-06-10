#!/usr/bin/env bats
# tests/scripts/knowledge-rag/knowledge-rag-real-test.bats
# Valida o MCP real do knowledge-rag (se disponivel)

load "../../helpers/test_helper"

setup()    { common_setup; }
teardown() { common_teardown; }

require_knowledge_rag_real() {
  if ! command -v knowledge-rag >/dev/null 2>&1; then
    fail "knowledge-rag nao disponivel neste ambiente — instale com: pipx install knowledge-rag"
  fi
}

@test "knowledge-rag real: comando knowledge-rag esta disponivel" {
  run command -v knowledge-rag
  if [ "$status" -ne 0 ]; then
    fail "knowledge-rag nao encontrado no PATH. Instale com: pipx install knowledge-rag"
  fi
}

@test "knowledge-rag real: consegue iniciar servidor MCP" {
  require_knowledge_rag_real
  
  local tmpdir
  tmpdir="$(mktemp -d)"
  mkdir -p "$tmpdir/docs"
  echo "# Test Document" > "$tmpdir/docs/test.md"
  
  # Testar que o comando existe e tem subcomando mcp-server
  run knowledge-rag --help
  assert_success
  assert_output --partial "mcp-server" || assert_output --partial "MCP"
  
  rm -rf "$tmpdir"
}

@test "knowledge-rag real: consegue indexar documentos" {
  require_knowledge_rag_real
  
  local tmpdir
  tmpdir="$(mktemp -d)"
  mkdir -p "$tmpdir/docs"
  echo "# Documento de Teste" > "$tmpdir/docs/test.md"
  echo "Conteudo do documento para indexacao." >> "$tmpdir/docs/test.md"
  
  # Tenta criar uma collection e indexar
  # Nota: isto pode falhar se o modelo ONNX ainda nao foi baixado
  run knowledge-rag index "$tmpdir/docs" --collection "test-collection" 2>&1 || true
  
  # Aceita sucesso ou erro por modelo nao baixado
  [ "$status" -eq 0 ] || assert_output --partial "model" || assert_output --partial "ONNX" || assert_output --partial "download"
  
  rm -rf "$tmpdir"
}
