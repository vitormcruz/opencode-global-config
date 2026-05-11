# Makefile — opencode-config test targets

BATS_LIB_PATH ?= $(HOME)/.local/lib/bats
BATS_LOCAL    := $(HOME)/.local/bin/bats
BATS          ?= $(shell test -x "$(BATS_LOCAL)" && echo "$(BATS_LOCAL)" || echo bats)
TESTS_DIR     := tests

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
	        $(TESTS_DIR)/scripts/browser-test

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
	        $(TESTS_DIR)/scripts/crawl4ai

## OpenCode via container Docker (reusa container existente)
test-opencode-integration:
	@bash -c 'set -e; \
	  trap "bash tests/opencode-int-test/docker/container-test-opencode.sh --down" EXIT; \
	  bash tests/opencode-int-test/docker/container-test-opencode.sh --up; \
	  export OPENCODE_TEST_MODEL=$$(cat /tmp/opencode-test-model 2>/dev/null || echo "opencode/big-pickle"); \
	  $(BATS) $(TESTS_DIR)/opencode-int-test'

## OpenCode via container Docker (forca rebuild da imagem e recria container)
test-opencode-integration-rebuild:
	@bash -c 'set -e; \
	  trap "bash tests/opencode-int-test/docker/container-test-opencode.sh --down" EXIT; \
	  bash tests/opencode-int-test/docker/container-test-opencode.sh --rebuild; \
	  export OPENCODE_TEST_MODEL=$$(cat /tmp/opencode-test-model 2>/dev/null || echo "opencode/big-pickle"); \
	  $(BATS) $(TESTS_DIR)/opencode-int-test'

help:
	@grep -E '^##' Makefile | sed 's/## //'
