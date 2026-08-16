# ADR-0001: Migração de MCPs locais para CLIs nativos

- **Status:** Aceita
- **Data:** 2026-08-07
- **Escopo:** OpenCode, Copilot CLI, bootstrap, skills e testes

## Contexto

Servidores MCP locais, o wrapper `avelino/mcp` e o container do crawl4ai
adicionavam processos persistentes, configuração duplicada e diferenças entre
WSL/Linux e Windows. O repositório também mantinha pares de scripts Bash e
PowerShell e uma suíte BATS que não podia rodar nativamente no Windows.

## Decisão

Adotar CLIs nativos e um pacote Python instalável como fonte única de
comportamento. O plano de migração aprovado registra as seguintes decisões:

| ID | Decisão aceita |
|---|---|
| AD-1 | Eliminar MCPs locais; usar `crwl` e `codebase-memory-mcp cli`. |
| AD-2 | Skills invocam `crwl` diretamente, sem wrapper intermediário. |
| AD-3 | Instalar CLIs nativamente em WSL/Linux e Windows. |
| AD-4 | Migrar scripts para Python e testes para pytest. |
| AD-5 | OpenCode permanece exclusivo de WSL/Linux. |
| AD-6 | Copilot CLI fica exclusivo do Windows; clientes não são misturados. |
| AD-7 (rev.) | `websearch` como busca padrão única; busca do ambiente como fallback. |
| AD-8 | Remover o Makefile ao final e usar marcadores/fixtures pytest. |
| AD-9 | Instalar dependências em user-space, sem sudo ou administrador. |
| AD-10 | Detectar dependências antes de instalar e permitir seleção interativa. |
| AD-11 | Distribuir entrypoints por pacote Python e `console_scripts`. |
| AD-12 | Executar a migração em fatias verticais, com checkpoints por fase. |
| AD-13 | Gerenciar AWS CLI v2 como dependência obrigatória user-local. |

## Implementação atual

- `crwl` é o cliente local do Crawl4AI; não existe servidor MCP nem container
  local para pesquisa web.
- `codebase-memory-mcp cli` é o cliente local de busca de código e
  documentação; não é configurado como transporte MCP.
- O comportamento executável vive em `src/opencode_config/`. Restam somente os
  entrypoints finos de bootstrap `configurar-repo.sh` e
  `configurar-repo.ps1`.
- Linux/WSL configura o OpenCode; Windows configura somente o Copilot CLI.
- As dependências são detectadas e instaladas em user-space. O AWS CLI v2 usa
  os instaladores oficiais em modo user-local nos dois sistemas.

## Consequências

- `crwl` requer `crawl4ai-setup` após a instalação para preparar o browser.
- A configuração deixa de gerar `servers.json` e não depende de Docker para
  pesquisa web.
- O pacote Python fornece os entrypoints compartilhados por Linux, WSL e
  Windows.
- O pytest substitui BATS e o Makefile; os marcadores separam testes unitários,
  ferramentas e integrações por cliente.
- A manutenção de dois adapters shell/PowerShell deixa de existir; os
  entrypoints de bootstrap somente delegam ao mesmo módulo Python.

## Alternativas rejeitadas

- Manter o wrapper `avelino/mcp` sobre os CLIs: duplicaria configuração e
  manteria uma dependência local sem valor após a migração.
- Manter o container crawl4ai: exigiria Docker e conservaria o acoplamento ao
  transporte MCP.
- Manter implementações Bash e PowerShell separadas: perpetuaria divergências
  de comportamento entre plataformas.
- Manter BATS e o Makefile: impediria a execução nativa da suíte Copilot no
  Windows e duplicaria o runner de testes.

## Asserções executáveis

As decisões são verificadas pelos testes e pelos inventários do repositório:

- `pytest -m "unit or tools"` valida o pacote, bootstrap, adapters e CLIs.
- `tests/test_mcp_wrapper_cleanup.py` verifica a ausência do wrapper e do
  Makefile.
- `tests/test_crawl4ai_cleanup.py` verifica a remoção do container local do
  Crawl4AI.
- `tests/scripts/bootstrap_repo/test_repo_structure.py` verifica os
  entrypoints e a ausência dos scripts legados.
- A validação final executa `aws --version` após o bootstrap em WSL/Linux e
  Windows, além das suítes específicas de cada cliente.
