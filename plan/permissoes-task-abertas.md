# Plano: Permissões de delegação (tool task) abertas

## Overview

Os agentes globais em `harness-conf/agents/` carregam no frontmatter um bloco
`permission.task` com `"*": deny` seguido de allowlist estática de agentes.
Essa política bloqueia agentes novos criados por projetos consumidores da
config global: qualquer agente fora da lista é negado pela regra estática,
e reiniciar o opencode não resolve porque a lista é texto fixo no markdown.
Este plano troca a política fechada por uma política aberta (`"*": allow`),
ajusta as guardas de teste que sancionavam a política antiga, ajusta o
adapter Copilot que materializa a allowlist no prompt e registra a decisão
em ADR permanente.

Contexto histórico (levantado em 2026-10-14): a política fechada entrou em
`b416dbe`/`9b185cb` (2026-09-26) como hardening contra (1) falha de spawn
de agente `mode: primary` em runtime ("Unknown subagent type") e (2)
permissão ampla considerada inauditável. A resolução foi creditada à
classificação do `rev` em 2026-09-27 (plano arquivado
`plan/insumo-devflow-spawn-dinamico.md`, commit `dc44d79`), não ao `sec`.
O cenário de projetos com agentes próprios não foi considerado na época.

Estado inicial dos blocos `permission.task` (10 arquivos):

- deny puro, sem allows: `dba`, `eng-software`, `front`, `qa`, `rev`, `sec`
- deny + allowlist: `analista` (revisor-historia), `curador-produto`
  (eng-software), `devflow` (7 agentes), `smart-planner` (8 agentes)
- `revisor-historia` não tem bloco `permission.task`

## Architecture Decisions

- **D1 (aprovada pelo humano em 2026-10-14): política de delegação aberta.**
  Agentes podem spawnar qualquer agente. O padrão `"*": deny` + allowlist
  estática em `permission.task` deixa de existir nos agentes do harness-conf.
  Rationale: projetos consumidores podem definir agentes próprios e usá-los
  com o smart-planner e demais orquestradores; a allowlist estática bloqueava
  isso. Registro permanente em ADR nova (`docs/adr/0012-*`), revogando
  explicitamente a política de hardening de 2026-09-26.
- (demais decisões pendentes de aprovação)

## Task List

(a preencher após decisões)

## Risks and Mitigations

(a preencher)

## Open Questions

- Escopo da abertura: todos os agentes (incluindo workers com deny puro
  hoje) ou apenas orquestradores (smart-planner, devflow, analista)?
  Pendente de decisão humana.

## Status

- Fase: coleta de contexto e decisões de arquitetura.
