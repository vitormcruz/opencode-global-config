# Implementation Plan: Modelo On-Premises para Testes de Integracao

## Overview

Substituir o modelo externo usado hoje nos testes de integracao dos harness
OpenCode e Copilot CLI por um modelo servido on-premises (ex.: "bonsai"),
garantindo que nenhum prompt, codigo ou artefato do repositorio saia para
provedores externos durante a execucao da suite.

Estado atual observado no repo:

- `tests/integration/config/opencode.test.json` fixa `opencode/big-pickle`
  para os agentes `plan` e `build` (provider externo).
- `tests/integration/docker/entrypoint.py` sobrescreve esse modelo com
  `OPENCODE_TEST_MODEL` e mescla `provider` vindo de `OPENCODE_CONFIG`.
- `tests/integration/docker/Dockerfile` baixa o OpenCode de
  `https://opencode.ai/install` durante o build.
- `tests/integration/test_copilot_cli.py` faz apenas smoke test
  (`--help`, `--version`); nao ha teste comportamental do Copilot CLI.
- Markers do pytest: `unit`, `tools`, `opencode`, `copilot`.

## Architecture Decisions

<!-- Preenchido incrementalmente conforme as decisoes forem aprovadas. -->

_(nenhuma decisao registrada ainda)_

## Task List

<!-- Preenchido apos resolver todos os ramos de decisao. -->

_(pendente)_

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Copilot CLI nao permite endpoint LLM arbitrario | Alto | A definir |

## Open Questions

- Qual a natureza tecnica do "bonsai" (endpoint, protocolo, auth)?
- O harness Copilot pode ter teste comportamental sem backend GitHub?
- O isolamento deve ser verificado (assercao de ausencia de trafego externo)?
