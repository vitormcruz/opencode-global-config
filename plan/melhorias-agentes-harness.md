# Plano: Melhorias em Agentes, Curadoria e Estrutura de Harness

Status: EM PLANEJAMENTO

## Overview

Ajustes no repo opencode-global-config a partir de 6 anotações do humano:
contextualização do plano na conversa, especificação executável na curadoria,
skill de spec executável extraída do analista, AGENTS.md global para harnesses,
distinção repo vs artefatos copiados, e flexibilidade de modelos no devflow.

## Architecture Decisions

- **D1 (plano único)**: as 6 anotações serão tratadas em um único plano,
  com fases independentes e checkpoints por fase. Corte natural se preciso
  isolar: [1,2,3,6] agentes/workflow vs [4,5] estrutura/adapters.
- **D2 (fusão no README, anotação 2)**: o spec `docs/testes-produto.md`
  do projeto-alvo será fundido no `docs/README.md` como seção "Testes por
  Especialidade". O `AGENTS.md` do projeto-alvo mantém só a tabela índice
  + link (âncora para a seção). O template `default-artifacts/testes-produto.md`
  é absorvido pelo `doc-readme.md`.
- **D3 (dois níveis de teste, anotação 2)**: distinção obrigatória e
  explícita para o agente: (1) **testes da aplicação** — rodam via
  suítes/orquestrador `testes-produto` na fase Testes, sempre que se
  desenvolve funcionalidade; (2) **testes dos scripts de teste** — os
  scripts de suíte/orquestrador são código, têm testes próprios que cobrem
  o que o doc especifica (o doc é a especificação executável deles) e rodam
  SOMENTE quando os scripts mudam (ex: curadoria alterando
  ferramentas/critérios por orientação do humano); nunca no ciclo normal.
  A distinção deve ficar clara nos agentes, nos templates default-artifacts
  e no doc gerado no projeto-alvo.
- **D4 (AGENTS.md base, anotação 4)**: criar `harness-conf/AGENTS.base.md`
  com as regras universais do humano (idioma/concisão, proibição de timeouts,
  espera determinística, Conventional Commits, codebase-memory, CLIs nativos,
  separação por ambiente, confirmação para ação, etc.). Entrega: OpenCode
  via symlink `~/.config/opencode/AGENTS.md`; Copilot via cópia para
  `~/.copilot/AGENTS.md`. Extinção do
  `.github/copilot-specific.instructions.md`, com conteúdo absorvido pela
  base. `AGENTS.md` raiz fica só com regras específicas do repo + aponta
  para a base.
- **D5 (reestruturação harness-conf/, anotações 4 e 5)**: mover para
  `harness-conf/` (via `git mv`): `agents/`, `skills/`, `commands/`,
  `opencode.json` + novo `AGENTS.base.md`. Ficam na raiz (infra do repo):
  `AGENTS.md` (repo), `scripts/`, `src/`, `tests/`, `docs/`, `adapters/`,
  `plan/`, `README.md`. Sentido do termo **harness** a partir daqui:
  plataforma de agentes (OpenCode, Copilot CLI) — NÃO o antigo "harness"
  de testes (hoje `testes-produto`). **Requisito de commit:** o commit da
  reestruturação DEVE ter body detalhado explicando a mudança de conceito
  (harness antigo = agregador de testes renomeado para testes-produto;
  harness novo = plataforma de agentes) para desambiguar o log para
  agentes que consultarem o histórico.

## Task List

(fases e tasks serão definidas após as decisões)

## Risks and Mitigations

(a definir)

## Open Questions

- Q1: Um plano único ou N planejamentos?
- Q2: Sentido exato de "doc do harness vira especificação executável" (anotação 2)
- Q3: Conteúdo e entrega do AGENTS.md global (anotação 4)
- Q4: Solução para padronização de specs executáveis (anotação 3)
- Q5: Confirmação de leitura das anotações 1, 5 e 6
