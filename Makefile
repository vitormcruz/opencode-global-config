# Makefile — opencode-config test targets

BATS        := tests/bats-libs/bats-core/bin/bats
TESTS_DIR   := tests

.PHONY: test test-unit test-integration test-smoke test-bootstrap \
        test-behavioral help

## Todos os testes da Camada 1 (sem Docker)
test:
	$(BATS) $(TESTS_DIR)/structure \
	        $(TESTS_DIR)/bootstrap \
	        $(TESTS_DIR)/skills \
	        $(TESTS_DIR)/crawl4ai \
	        $(TESTS_DIR)/smoke.bats

## Só estrutura estática (sem deps externas)
test-unit:
	$(BATS) $(TESTS_DIR)/structure

## Só wrappers (precisa de pandoc/docling/resvg)
test-integration:
	$(BATS) $(TESTS_DIR)/wrappers

## Só smoke test
test-smoke:
	$(BATS) $(TESTS_DIR)/smoke.bats

## Só bootstrap
test-bootstrap:
	$(BATS) $(TESTS_DIR)/bootstrap

## Camada 2 (precisa de Docker)
test-behavioral:
	$(BATS) $(TESTS_DIR)/behavioral

## Valida que a infra BATS funciona (1 teste trivial)
test-infra:
	$(BATS) $(TESTS_DIR)/smoke-infra.bats

help:
	@grep -E '^##' Makefile | sed 's/## //'
