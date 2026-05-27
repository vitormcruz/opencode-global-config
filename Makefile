# Makefile — opencode-config test targets

BATS_LIB_PATH ?= $(HOME)/.local/lib/bats
BATS_LOCAL    := $(HOME)/.local/bin/bats
BATS          ?= $(shell test -x "$(BATS_LOCAL)" && echo "$(BATS_LOCAL)" || echo bats)
TESTS_DIR     := tests

# Atalho: MODEL=default-open-model define OPENCODE_TEST_MODEL com o modelo aberto padrao
# Atualmente mapeia para opencode/big-pickle (modelo externo que COLETA DADOS)
# AVISO: Nao use em ambientes sensiveis. Use apenas para testes pessoais/demonstracao.
ifeq ($(MODEL),default-open-model)
  export OPENCODE_TEST_MODEL := opencode/big-pickle
endif

export BATS_LIB_PATH

.PHONY: test test-unit test-tools \
        test-opencode-integration test-opencode-integration-rebuild help

## Todos os testes (unit + tools + integracao Docker)
test: test-unit test-tools test-opencode-integration

## Testes unitarios puros - sem dependencias externas
test-unit:
	$(BATS) \
	        $(TESTS_DIR)/agents \
	        $(TESTS_DIR)/scripts/bootstrap_repo/opencode-link-test.bats \
	        $(TESTS_DIR)/scripts/bootstrap_repo/repo-state-test.bats \
	        $(TESTS_DIR)/scripts/bootstrap_repo/repo-structure-test.bats \
	        $(TESTS_DIR)/scripts/skills \
	        $(TESTS_DIR)/scripts/browser-test \
	        $(TESTS_DIR)/scripts/graphify/install-test.bats \
	        $(TESTS_DIR)/scripts/mapa-produto

## Testes que requerem ferramentas instaladas no WSL
test-tools:
	@printf '\n'
	@printf '=== test-tools: requer ferramentas configuradas no WSL ===\n'
	@printf '    Se algum falhar, rode primeiro:\n'
	@printf '    ./scripts/bootstrap_repo/opencode-install-deps\n'
	@printf '\n'
	$(BATS) \
	        $(TESTS_DIR)/scripts/opencode-doc-extract-test.bats \
	        $(TESTS_DIR)/scripts/opencode-md-export-test.bats \
	        $(TESTS_DIR)/scripts/opencode-svgtoimage-test.bats \
	        $(TESTS_DIR)/scripts/bootstrap_repo/opencode-install-deps-test.bats \
	        $(TESTS_DIR)/scripts/crawl4ai \
	        $(TESTS_DIR)/scripts/graphify/graphify-installed-test.bats

## OpenCode via container Docker (reusa container existente)
test-opencode-integration:
	@bash -c 'set -e; \
	  if [ -z "$$OPENCODE_TEST_MODEL" ]; then \
	    echo "ERRO: OPENCODE_TEST_MODEL não definido"; \
	    echo ""; \
	    echo "Opções:"; \
	    echo "  1. export OPENCODE_TEST_MODEL=seu-modelo"; \
	    echo "     Exemplo: export OPENCODE_TEST_MODEL=openai/gpt-4"; \
	    echo ""; \
	    echo "  2. make test-opencode-integration MODEL=default-open-model"; \
	    echo "     (usa modelo aberto padrão — ATENÇÃO: coleta dados externos)"; \
	    exit 1; \
	  fi; \
	  trap "bash tests/opencode-int-test/docker/container-test-opencode.sh --down" EXIT; \
	  bash tests/opencode-int-test/docker/container-test-opencode.sh --up; \
	  $(BATS) $(TESTS_DIR)/opencode-int-test'

## OpenCode via container Docker (forca rebuild da imagem e recria container)
test-opencode-integration-rebuild:
	@bash -c 'set -e; \
	  if [ -z "$$OPENCODE_TEST_MODEL" ]; then \
	    echo "ERRO: OPENCODE_TEST_MODEL não definido"; \
	    echo ""; \
	    echo "Opções:"; \
	    echo "  1. export OPENCODE_TEST_MODEL=seu-modelo"; \
	    echo "     Exemplo: export OPENCODE_TEST_MODEL=openai/gpt-4"; \
	    echo ""; \
	    echo "  2. make test-opencode-integration-rebuild MODEL=default-open-model"; \
	    echo "     (usa modelo aberto padrão — ATENÇÃO: coleta dados externos)"; \
	    exit 1; \
	  fi; \
	  trap "bash tests/opencode-int-test/docker/container-test-opencode.sh --down" EXIT; \
	  bash tests/opencode-int-test/docker/container-test-opencode.sh --rebuild; \
	  $(BATS) $(TESTS_DIR)/opencode-int-test'

help:
	@grep -E '^##' Makefile | sed 's/## //'
