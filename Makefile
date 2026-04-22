# Makefile — opencode-config test targets

BATS_LIB_PATH ?= $(HOME)/.local/lib/bats
BATS_LOCAL    := $(HOME)/.local/bin/bats
BATS          ?= $(shell test -x "$(BATS_LOCAL)" && echo "$(BATS_LOCAL)" || echo bats)
TESTS_DIR     := tests

export BATS_LIB_PATH

.PHONY: test test-all test-scripts test-bootstrap-repo \
        test-opencode-integration test-opencode-integration-rebuild help

## Todos os testes da Camada 1 (sem Docker)
test:
	$(BATS) $(TESTS_DIR)/scripts \
	        $(TESTS_DIR)/opencode-int-test/docker/container-test-opencode-test.bats

## Só scripts (bootstrap_repo + wrappers + skills + crawl4ai)
test-scripts:
	$(BATS) $(TESTS_DIR)/scripts

## Só bootstrap do repo
test-bootstrap-repo:
	$(BATS) \
	        $(TESTS_DIR)/scripts/bootstrap_repo/opencode-link-test.bats \
	        $(TESTS_DIR)/scripts/bootstrap_repo/opencode-install-deps-test.bats \
	        $(TESTS_DIR)/scripts/bootstrap_repo/repo-state-test.bats

## OpenCode via container Docker (reusa container existente)
test-opencode-integration:
	@bash -c 'set -e; \
	  trap "bash tests/opencode-int-test/docker/container-test-opencode.sh --down" EXIT; \
	  bash tests/opencode-int-test/docker/container-test-opencode.sh --up; \
	  export OPENCODE_TEST_MODEL=$$(cat /tmp/opencode-test-model 2>/dev/null || echo "opencode/big-pickle"); \
	  $(BATS) $(TESTS_DIR)/opencode-int-test'

## OpenCode via container Docker (força rebuild da imagem e recria container)
test-opencode-integration-rebuild:
	@bash -c 'set -e; \
	  trap "bash tests/opencode-int-test/docker/container-test-opencode.sh --down" EXIT; \
	  bash tests/opencode-int-test/docker/container-test-opencode.sh --rebuild; \
	  export OPENCODE_TEST_MODEL=$$(cat /tmp/opencode-test-model 2>/dev/null || echo "opencode/big-pickle"); \
	  $(BATS) $(TESTS_DIR)/opencode-int-test'

## Todos os testes (unidade + integração com Docker)
test-all: test test-opencode-integration

help:
	@grep -E '^##' Makefile | sed 's/## //'
