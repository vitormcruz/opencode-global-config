# Plano: Cockpit — UI pessoal com painéis dinâmicos e agente

> STATUS: triagem inicial (em andamento)

## Overview

Cockpit pessoal de produção (não mais experimento): evolução do que foi
validado no experimento `painel-dinamico-lab` (React + Dockview +
FastAPI + agente LLM via WebSocket). A definir na triagem: escopo do
que o cockpit monitora/gerencia, onde roda, base de código (evoluir o
lab vs repo novo) e o papel do agente.

Base validada (veredito do experimento, 2026-09-12):
- docking IDE-style com Dockview (11+ tipos de painel, persistência);
- FAB + floating card refinado (R1-R3), workflows animados;
- backend FastAPI com SSE de dados e `/api/servicos` real;
- agente LLM (deepseek-v4-flash via `opencode run`) dirigindo a UI por
  WS (`open_panel`/`open_card` com conteúdo gerado, whitelist).

## Architecture Decisions

(Decisões aprovadas serão registradas aqui como D1, D2, ...)

## Task List

(A ser preenchida após a triagem e decisões)

## Risks and Mitigations

(A preencher)

## Open Questions

- Escopo: o que o cockpit monitora/gerencia de verdade?
- Onde roda: só local ou acessível externamente?
- Base de código: evoluir `painel-dinamico-lab` ou repo novo?
- Papel do agente: continua deepseek-v4-flash via opencode run? Evolui
  (memória, mais comandos, iniciativa)?
