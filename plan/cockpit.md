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

## Research Notes — similares (2026-09-12)

O espaço "agentic UI / generative UI" explodiu em 2025-2026, mas em duas
linhas principais: **chat-cêntrico** (UI gerada inline na conversa) e
**dashboard gerado por prompt** (uma tela nova a cada pedido). Nada
achado combina: cockpit pessoal **persistente** + **docking IDE-style**
+ agente que molda a tela inteira.

Referências por maturidade:

- **AG-UI / CopilotKit** (15.6k stars, MIT) — protocolo aberto
  agent↔app (SSE/WS, eventos, state sync) + framework React com
  generative UI (components as tools, A2UI, MCP Apps, open GenUI em
  sandbox). MADURO, mas chat-first: o UI nasce DENTRO do chat.
  https://ag-ui.com · https://docs.copilotkit.ai
- **A2UI (Google, a2ui.org)** — protocolo declarativo agent→UI (v0.9
  draft): agente emite componentes, renderer compõe. Tendência de
  padrão; suportado por CopilotKit e outros.
- **Morph (eumemic/morph)** — o mais próximo CONCEITUALMENTE: "agente
  fala remodelando um dashboard vivo, não digitando num chat".
  Stable-IDs + View Transitions (animação derivada do diff), human
  commits por manipulação direta, receipts. EXPERIMENTAL, sem
  docking/persistência de workspace. Ideias ricas para colher.
  https://github.com/eumemic/morph
- **ggui** (36 stars) — MCP-UI com `ggui_render` (gera UI via LLM),
  self-host, RC v0.1.
- **adk-ui** (Rust, 9 stars), **Pane** (1 star), **Zephyr**
  (webcomponents+MCP) — pequenos/nicho.
- Geradores por prompt (generative-dashboard-builder, gen-ui Angular,
  OpenGenerativeUI) — não são cockpit persistente.

**Veredito da pesquisa:** nada em estado bom que substitua a ideia.
Diferencial a preservar: workspace docking persistente como superfície
do agente (vs chat-first dos grandes). Ações recomendadas: (1) seguir
com repo novo; (2) avaliar adotar/adaptar AG-UI ou A2UI como formato
de comandos no lugar do DSL próprio (interoperabilidade); (3) estudar
Morph para as ideias de stable-ID/animação/human-commits.

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
