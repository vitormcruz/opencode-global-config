# Makefile — opencode-config test targets

BATS        := tests/bats-libs/bats-core/bin/bats
TESTS_DIR   := tests

.PHONY: test test-unit test-integration test-smoke test-bootstrap-repo \
        test-opencode-integration test-infra test-mcp help

## Todos os testes da Camada 1 (sem Docker)
test:
	$(BATS) $(TESTS_DIR)/structure \
	        $(TESTS_DIR)/scripts/bootstrap_repo \
	        $(TESTS_DIR)/skills \
	        $(TESTS_DIR)/mcp/install-crawl4ai-mcp.bats \
	        $(TESTS_DIR)/smoke.bats

## Só estrutura estática (sem deps externas)
test-unit:
	$(BATS) $(TESTS_DIR)/structure

## Só wrappers (precisa de pandoc/docling/resvg)
test-integration:
	$(BATS) $(TESTS_DIR)/scripts

## Só smoke test
test-smoke:
	$(BATS) $(TESTS_DIR)/smoke.bats

## Só bootstrap do repo
test-bootstrap-repo:
	$(BATS) $(TESTS_DIR)/scripts/bootstrap_repo

## OpenCode via container Docker (sobe e desce automaticamente)
test-opencode-integration:
	@bash -c 'set -e; trap "bash tests/opencode-int-test/container-test-opencode.sh --down" EXIT; bash tests/opencode-int-test/container-test-opencode.sh --up; $(BATS) $(TESTS_DIR)/opencode-int-test'

## Valida que a infra BATS funciona (1 teste trivial)
test-infra:
	$(BATS) $(TESTS_DIR)/infra/smoke-infra.bats

## Testes dos artefatos MCP (fora do contexto do OpenCode)
test-mcp:
	$(BATS) $(TESTS_DIR)/mcp

help:
	@grep -E '^##' Makefile | sed 's/## //'
