# ADR-0001: Migracao de MCPs locais para CLIs nativos

- **Status:** Aceita
- **Data:** 2026-08-07
- **Escopo:** OpenCode, Copilot CLI, bootstrap, skills e testes

## Contexto

Servidores MCP locais, o wrapper `avelino/mcp` e o container do crawl4ai
adicionavam processos persistentes, configuracao duplicada e diferencas entre
WSL/Linux e Windows. O repositorio tambem mantinha pares de scripts Bash e
PowerShell e uma suite BATS que nao podia rodar nativamente no Windows.

## Decisao

Adotar CLIs nativos e um pacote Python instalavel como fonte unica de
comportamento. O plano de migracao aprovado registra as seguintes decisoes:

| ID | Decisao aceita |
|---|---|
| AD-1 | Eliminar MCPs locais; usar `crwl` e `codebase-memory-mcp cli`. |
| AD-2 | Skills invocam `crwl` diretamente, sem wrapper intermediario. |
| AD-3 | Instalar CLIs nativamente em WSL/Linux e Windows. |
| AD-4 | Migrar scripts para Python e testes para pytest. |
| AD-5 | OpenCode permanece exclusivo de WSL/Linux. |
| AD-6 | Copilot CLI fica exclusivo do Windows; clientes nao sao misturados. |
| AD-7 | Preferir `web_search_exa`, depois `websearch`, depois busca padrao. |
| AD-8 | Remover o Makefile ao final e usar marcadores/fixtures pytest. |
| AD-9 | Instalar dependencias em user-space, sem sudo ou administrador. |
| AD-10 | Detectar dependencias antes de instalar e permitir selecao interativa. |
| AD-11 | Distribuir entrypoints por pacote Python e `console_scripts`. |
| AD-12 | Executar a migracao em fatias verticais, com checkpoints por fase. |
| AD-13 | Gerenciar AWS CLI v2 como dependencia obrigatoria user-local. |

## Consequencias

- `crwl` substitui o servidor crawl4ai e requer `crawl4ai-setup` apos a
  instalacao para baixar o browser.
- `codebase-memory-mcp` continua sendo instalado como binario, mas seu uso e
  feito pelo subcomando `cli`, nao por transporte MCP.
- A configuracao deixa de gerar `servers.json` e nao depende de Docker para
  pesquisa web.
- O bootstrap pode continuar reportando uma dependencia ausente sem abortar
  as demais instalacoes.
- A transicao preserva BATS e scripts legados ate as fases que os aposentam,
  evitando uma janela sem cobertura durante a migracao.

## Alternativas rejeitadas

- Manter o wrapper `avelino/mcp` sobre os CLIs: duplicaria configuracao e
  manteria uma dependencia local sem valor apos a migracao.
- Manter o container crawl4ai: exigiria Docker e conservaria o acoplamento ao
  transporte MCP.
- Manter implementacoes Bash e PowerShell separadas: perpetuaria divergencias
  de comportamento entre plataformas.
