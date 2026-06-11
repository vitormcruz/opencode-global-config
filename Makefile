# Makefile — opencode-config test targets

BATS_LIB_PATH ?= $(HOME)/.local/lib/bats
BATS_LOCAL    := $(HOME)/.local/bin/bats
BATS          ?= $(shell test -x "$(BATS_LOCAL)" && echo "$(BATS_LOCAL)" || echo bats)
TESTS_DIR     := tests

# Atalho: DEFAULT_OPEN_MODEL=1 define OPENCODE_TEST_MODEL com o modelo aberto padrao
# Atualmente mapeia para opencode/big-pickle (modelo externo que COLETA DADOS)
# AVISO: Nao use em ambientes sensiveis. Use apenas para testes pessoais/demonstracao.
ifeq ($(DEFAULT_OPEN_MODEL),1)
  export OPENCODE_TEST_MODEL := opencode/big-pickle
endif

export BATS_LIB_PATH

.PHONY: test-unit test-tools \
        test-opencode test-copilot \
        test-opencode-integration test-opencode-integration-rebuild \
        test-opencode-integration-default-model test-opencode-integration-rebuild-default-model \
        test-copilot-integration \
        help

## OpenCode completo (unit + tools + integracao)
test-opencode: test-unit test-tools test-opencode-integration
	@printf '\n=== test-opencode: concluido ===\n'

## Copilot completo (unit + tools + integracao)
test-copilot: test-unit test-tools test-copilot-integration
	@printf '\n=== test-copilot: concluido ===\n'

## Testes unitarios puros - sem dependencias externas
test-unit:
	$(BATS) \
	        $(TESTS_DIR)/agents \
	        $(TESTS_DIR)/scripts/bootstrap_repo/opencode-link-test.bats \
	        $(TESTS_DIR)/scripts/bootstrap_repo/repo-state-test.bats \
	        $(TESTS_DIR)/scripts/bootstrap_repo/repo-structure-test.bats \
	        $(TESTS_DIR)/scripts/bootstrap_repo/configurar-repo-test.bats \
	        $(TESTS_DIR)/scripts/skills \
	        $(TESTS_DIR)/scripts/browser-test \
	        $(TESTS_DIR)/scripts/mapa-produto

## Testes que requerem ferramentas instaladas no WSL
test-tools:
	@printf '\n'
	@printf '=== test-tools: requer ferramentas configuradas no WSL ===\n'
	@printf '    Se algum falhar, rode primeiro:\n'
	@printf '    ./scripts/bootstrap_repo/configurar-repo.sh\n'
	@printf '\n'
	$(BATS) \
	        $(TESTS_DIR)/scripts/opencode-doc-extract-test.bats \
	        $(TESTS_DIR)/scripts/opencode-md-export-test.bats \
	        $(TESTS_DIR)/scripts/opencode-svgtoimage-test.bats \
	        $(TESTS_DIR)/scripts/bootstrap_repo/wsl-install-deps-test.bats \
	        $(TESTS_DIR)/scripts/crawl4ai \
	        $(TESTS_DIR)/scripts/codebase-memory

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
	    echo "  2. make test-opencode-integration-default-model"; \
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
	    echo "  2. make test-opencode-integration-rebuild-default-model"; \
	    echo "     (usa modelo aberto padrão — ATENÇÃO: coleta dados externos)"; \
	    exit 1; \
	  fi; \
	  trap "bash tests/opencode-int-test/docker/container-test-opencode.sh --down" EXIT; \
	  bash tests/opencode-int-test/docker/container-test-opencode.sh --rebuild; \
	  $(BATS) $(TESTS_DIR)/opencode-int-test'

## OpenCode com modelo aberto padrão (reusa container)
test-opencode-integration-default-model:
	$(MAKE) test-opencode-integration OPENCODE_TEST_MODEL=opencode/big-pickle

## OpenCode com modelo aberto padrão (forca rebuild)
test-opencode-integration-rebuild-default-model:
	$(MAKE) test-opencode-integration-rebuild OPENCODE_TEST_MODEL=opencode/big-pickle

## Integracao Copilot CLI (requer copilot e mcp no PATH)
test-copilot-integration:
	@bash -c 'set -e; \
	  if ! command -v copilot >/dev/null 2>&1; then \
	    echo "ERRO: Copilot CLI nao encontrado no PATH"; \
	    echo ""; \
	    echo "Instale com:"; \
	    echo "  npm install -g @github/copilot"; \
	    echo "  copilot --login"; \
	    exit 1; \
	  fi; \
	  if ! command -v mcp >/dev/null 2>&1; then \
	    echo "ERRO: avelino/mcp nao encontrado no PATH"; \
	    echo ""; \
	    echo "Instale via bootstrap:"; \
	    echo "  ./scripts/bootstrap_repo/configurar-repo.sh --yes"; \
	    exit 1; \
	  fi; \
	  $(BATS) $(TESTS_DIR)/copilot-int-test'

help:
	@grep -E '^##' Makefile | sed 's/## //'
