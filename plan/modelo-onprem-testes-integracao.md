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

## Contexto Tecnico do Bonsai (pesquisa confirmada)

Fontes: `prismml.com/news/bonsai-27b`, `github.com/PrismML-Eng/Bonsai-demo`
(README, AGENTS.md, TOOLS.md). Licenca Apache 2.0.

- Servido por `llama-server` (llama.cpp) em `http://localhost:8080`, com API
  **OpenAI-compatible** (`/v1/chat/completions`).
- Com `--jinja`, aceita o array `tools` da OpenAI e devolve `tool_calls`
  estruturados — sem prompt hacks. Round-trip de tool completo verificado.
- Familias e tamanhos: `ternary` (default, GGUF Q2_0 ~6.7 GB + mmproj 0.9 GB)
  e `bonsai` 1-bit (GGUF Q1_0 ~3.5 GB + mmproj 0.9 GB), nos tamanhos 27B, 8B,
  4B e 1.7B.
- **Restricao critica:** somente os modelos **27B** tem tool calling. O guia
  oficial descreve 8B/4B/1.7B como "text-only, no tools wiring". Testes
  comportamentais de agente dependem de tool calling.
- Benchmark agentic/tool-calling: Ternary 27B = 74.0, 1-bit 27B = 66.0
  (baseline full-precision Qwen3.6 27B = 80.0).
- Enquanto os repositorios 27B estiverem privados no HuggingFace, o download
  exige `BONSAI_TOKEN` (token HF read-only).
- Setup: `./setup.sh` (baixa deps, modelos e binarios) e
  `./scripts/start_llama_server.sh`.

## Architecture Decisions

### D1 — Harness Copilot fica restrito a testes deterministicos

O Copilot CLI autentica no backend do GitHub e nao permite apontar para um
endpoint LLM arbitrario. Portanto:

- O harness Copilot mantem apenas smoke tests deterministicos, sem inferencia
  (o padrao ja existente em `tests/integration/test_copilot_cli.py`).
- Todos os testes **comportamentais** de agentes, skills e comandos passam a
  rodar no OpenCode apontando para o modelo on-premises.

Rationale: assumir a limitacao real da ferramenta em vez de interceptar
internals nao documentados do Copilot (opcao descartada por fragilidade).

### D2 — Privacidade com enforcement, nao apenas configuracao

Nao basta configurar o provider local. O plano deve incluir verificacao ativa:

- O ambiente de teste roda com rede isolada, enxergando apenas o servidor do
  modelo on-premises.
- Um teste falha se houver provider externo configurado na config efetiva.
- O download de artefatos pela internet durante o **build** da imagem
  (hoje `curl https://opencode.ai/install` no Dockerfile) e tratado como
  problema separado do isolamento em **runtime**.

## Task List

<!-- Preenchido apos resolver todos os ramos de decisao. -->

_(pendente)_

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Copilot CLI nao permite endpoint LLM arbitrario | Alto | D1: harness Copilot fica em smoke tests deterministicos |
| Modelos Bonsai < 27B nao tem tool calling | Alto | A definir na escolha de variante |
| Repos 27B privados no HF exigem `BONSAI_TOKEN` | Medio | A definir |
| Hardware insuficiente para servir 27B | Medio | A definir |

## Open Questions

- Qual variante/tamanho do Bonsai sera usada?
- Onde o `llama-server` roda: host/WSL, container dedicado ou servico interno?
- Como resolver o download de artefatos externos no build da imagem Docker?
