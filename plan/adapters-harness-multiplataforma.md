# Plano: Adapters de Harness Multiplataforma

## Overview

Remover o acoplamento SO→harness: hoje Linux/WSL configura somente o OpenCode
e Windows somente o Copilot CLI (ADR-0001 AD-5/AD-6, bloqueio em
`adapters/opencode.py` e seleção por SO em `bootstrap/main.py`). O novo
comportamento: o bootstrap detecta o SO corrente e adapta **todos os harnesses
instalados** naquele SO, com estratégia de materialização por ambiente. A
arquitetura vira um registry extensível de harnesses, facilitando adicionar
novos clientes no futuro.

## Architecture Decisions

- **D1 — Windows usa cópia sincronizada.** A config global materializada no
  Windows é sempre cópia sincronizada a cada execução (modelo do adapter
  Copilot atual), sem symlink/junction. Evita dependência de Developer Mode e
  privilégios; contrapartida: divergência possível até o próximo sync.
- **D2 — Default: todos os harnesses instalados.** O bootstrap detecta quais
  harnesses estão instalados no SO corrente e configura todos; ausentes são
  ignorados com aviso. Flag `--harness` restringe a subconjunto.
- **D3 — Escopo: arquitetura completa.** Registry central + contrato comum de
  harness + migração dos dois adapters existentes + ADR novo revogando AD-5/AD-6
  do ADR-0001 + testes multi-SO. Não apenas remoção de bloqueios.
- **D4 — Env vars no Windows via HKCU\Environment.** No Windows nativo, o
  adapter OpenCode persiste `OPENCODE_ENABLE_EXA` (e demais env vars de
  usuário) em `HKEY_CURRENT_USER\Environment` via `winreg`, com broadcast de
  `WM_SETTINGCHANGE` (ctypes) para o Explorer recarregar o ambiente sem
  logoff. A persistência existente do PATH (installers/core.py) também passa a
  broadcastar.
- **D5 — Copilot instalável pelo bootstrap em Linux/WSL.** A dependência
  `copilot` do registry passa a ter `supported_environments` com Linux/WSL
  além de Windows, com install method via npm (`npm install --global --prefix
  ~/.local @github/copilot`). Provisionamento de máquina nova fica sem passos
  manuais.
- **D6 — Testes de integração permanecem por SO atual.** `-m opencode`
  continua WSL/Linux (Docker + llama-server); `-m copilot` continua Windows.
  O que vira multi-SO nesta mudança são os testes unitários/tools dos
  adapters e do registry. Execução cruzada das integrações fica registrada
  como open question futura.
- **D7 — Arquitetura: factory injeta strategy por SO; adapter cego ao SO.**
  Contrato `HarnessAdapter` por harness (OpenCode, Copilot) consumido pelo
  bootstrap via registry. Cada harness que varia por SO tem interface de
  strategy própria (ex.: `OpenCodeEnvStrategy`) com implementações
  `OpenCodePosix` (symlink + `.bashrc`) e `OpenCodeWindows` (cópia
  sincronizada + HKCU\Environment). Factory com mapa `strategy[env]`
  instancia o adapter já com a strategy correta (injeção no construtor);
  o adapter não contém decisão de SO. Copilot hoje não varia por SO e não
  ganha strategy. Reuso entre harnesses via utilitários de `lib/`
  (cópia sincronizada, backup), não hierarquia genérica. Entry points
  `opencode-adapter` e `opencode-copilot-adapter` permanecem como wrappers
  finos sobre os adapters.

## Task List

(a definir)

## Risks and Mitigations

(a definir)

## Open Questions

(a definir)
