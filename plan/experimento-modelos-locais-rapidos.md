# Implementation Plan: Experimento de modelos locais rápidos

## Overview

Avaliar Needle 2 e Qwen3-0.6B como possíveis substitutos do Bonsai nos testes
comportamentais do OpenCode, preservando execução local, gratuita e sem
telemetria.

## Architecture Decisions

- **D1 — Candidatos:** comparar Needle 2 e Qwen3-0.6B contra o Bonsai. Ambos
  precisam operar localmente, gratuitamente e sem telemetria; a aprovação
  depende de compatibilidade com o endpoint OpenAI e com tool calling.
- **D2 — Gate de substituição:** substituir o Bonsai somente se um candidato
  aprovar 100% da suíte `-m opencode`, não usar rede nem telemetria durante os
  testes e reduzir a duração total de forma mensurável.
- **D3 — Ganho mínimo:** exigir redução de ao menos 30% na duração total,
  comparada a uma execução-base recente do Bonsai no mesmo ambiente.

## Task List

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|

## Open Questions
