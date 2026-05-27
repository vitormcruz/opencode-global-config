# Plano: VS Code Copilot — MCP via CLI com `mcp (avelino)`

**Data:** 27/05/2026
**Wrapper padrão:** `mcp (avelino)` — binário Go único, sem dependências

---

## Etapa 1 — Criar `.github/copilot-instructions.md`

Substituir o conteúdo atual (cópia integral do `AGENTS.md`) por um arquivo
enxuto com instruções MCP via CLI.

**Conteúdo:**
- Nota de que regras gerais vêm do `AGENTS.md` (lido nativamente pelo VS Code)
- Seção "MCP via CLI" com `mcp (avelino)` como wrapper padrão
- Fluxo: `mcp --list` → `mcp call <servidor> <tool> --args`
- Servidores configurados: `exa` e `crawl4ai`
- Exemplos de composição com pipes e `jq`
- Referência a wrappers alternativos

---

## Etapa 2 — Adicionar instalação do wrapper ao `vscode-sync.ps1`

Nova função `Install-McpWrapper`:

- Verifica se `mcp` está no PATH
- Se não estiver, baixa o binário do GitHub Releases:
  - URL: `https://github.com/avelino/mcp/releases/latest/download/mcp-windows-amd64.exe`
  - Destino: `$env:LOCALAPPDATA\bin\mcp.exe`
  - Garante que o diretório esteja no PATH
- Configura servidores no wrapper:
  - `mcp add exa npx -y exa-mcp-server`
  - `mcp add --url http://localhost:11235/mcp/sse crawl4ai`
- Verifica com `mcp --list`

Chamar no fluxo principal antes de `Sync-Instructions`.

---

## Etapa 3 — Modificar `Sync-Instructions` no `vscode-sync.ps1`

- **Remover** a lógica que copia `AGENTS.md` → `copilot-instructions.md`
- O `.github/copilot-instructions.md` agora é versionado no repo (fonte de verdade)
- O script apenas faz backup do existente e copia a versão atualizada do repo
- Atualizar `Show-Plan` e `Show-Usage`

---

## Etapa 4 — Atualizar `README.md`

- Corrigir a linha `AGENTS.md → ...copilot-instructions.md`
- Documentar que `copilot-instructions.md` contém apenas instruções MCP via CLI
- Documentar que o `vscode-sync.ps1` instala o wrapper `mcp (avelino)`
- Adicionar nota sobre `$env:LOCALAPPDATA\bin` no PATH

---

## Etapa 5 — Atualizar testes

- Buscar testes existentes do `vscode-sync.ps1` em `tests/`
- Atualizar asserções que verificam cópia do `AGENTS.md`
- Adicionar teste que verifica que `copilot-instructions.md` não é cópia do `AGENTS.md`
- Adicionar teste que verifica presença de instruções MCP via CLI
- Adicionar teste para instalação do wrapper (mock/stub para download)

---

## Etapa 6 — Excluir `plan/vscode-copilot-mcp-via-cli.md`

```bash
git rm plan/vscode-copilot-mcp-via-cli.md
```

Conteúdo já incorporado no `copilot-instructions.md` e neste plano.

---

## Etapa 7 — Validar

```bash
make test
```

Revisar diff completo e propor mensagem de commit ao humano.

---

## Arquivos afetados

| Arquivo | Ação |
|---|---|
| `.github/copilot-instructions.md` | Reescrito |
| `scripts/bootstrap_repo/vscode-sync.ps1` | Modificado |
| `README.md` | Modificado |
| `plan/vscode-copilot-mcp-via-cli.md` | Excluído |
| `tests/**/*vscode*` ou similar | Atualizados |
