# Makefile — opencode-config test targets

BATS_LIB_PATH ?= $(HOME)/.local/lib/bats
BATS_LOCAL    := $(HOME)/.local/bin/bats
BATS          ?= $(shell test -x "$(BATS_LOCAL)" && echo "$(BATS_LOCAL)" || echo bats)
TESTS_DIR     := tests

export BATS_LIB_PATH

.PHONY: test test-scripts test-bootstrap-repo \
        test-opencode-integration help

## Todos os testes da Camada 1 (sem Docker)
test:
	$(BATS) $(TESTS_DIR)/scripts

## Só scripts (bootstrap_repo + wrappers + skills + crawl4ai)
test-scripts:
	$(BATS) $(TESTS_DIR)/scripts

## Só bootstrap do repo
test-bootstrap-repo:
	$(BATS) \
	        $(TESTS_DIR)/scripts/bootstrap_repo/opencode-link-test.bats \
	        $(TESTS_DIR)/scripts/bootstrap_repo/opencode-install-deps-test.bats \
	        $(TESTS_DIR)/scripts/bootstrap_repo/repo-state-test.bats

## OpenCode via container Docker (sobe e desce automaticamente)
test-opencode-integration:
	@bash -c 'set -e; trap "bash tests/opencode-int-test/container-test-opencode.sh --down" EXIT; bash tests/opencode-int-test/container-test-opencode.sh --up; $(BATS) $(TESTS_DIR)/opencode-int-test'

help:
	@grep -E '^##' Makefile | sed 's/## //'
