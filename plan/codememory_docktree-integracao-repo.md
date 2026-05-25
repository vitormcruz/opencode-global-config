# Plano: Integrar codememory_docktree neste repo

**Data:** 25/05/2026
**Status:** Aguardando implementação
**Guia base:** plan/combo1-codebase-memory-doctree.md

---

## 1. Escopo

Integrar codebase-memory-mcp + doctree-mcp ao ciclo de bootstrap deste
repo, tornando-os disponíveis automaticamente em OpenCode e VS Code para
qualquer projeto.

---

## 2. Arquivos alterados

### 2.1 `opencode.json` — adicionar entradas MCP

Na seção `mcp`, após a entrada `crawl4ai`:

```json
"codebase-memory": {
  "type": "stdio",
  "command": "codebase-memory-mcp",
  "args": [],
  "enabled": true
},
"doctree": {
  "type": "stdio",
  "command": "bunx",
  "args": ["doctree-mcp"],
  "enabled": true
}
```

> DOCS_ROOT não definido — doctree usa default `./docs` relativo à raiz
> do projeto onde o OpenCode for iniciado.

---

### 2.2 `scripts/bootstrap_repo/opencode-install-deps` — 2 novos blocos

Inserir após o bloco `[graphify]`, antes do sumário sudo.

**Bloco `[bun]`** — necessário para doctree-mcp via bunx:
- `has_cmd bun` → OK
- Ausente: `confirm_action` → `curl -fsSL https://bun.sh/install | bash`
- Sem sudo

**Bloco `[codebase-memory-mcp]`** — binário estático:
- `has_cmd codebase-memory-mcp` → OK
- Ausente: `confirm_action` → instala via installer oficial
- **Não** roda `codebase-memory-mcp install` após (evita sobrescrever
  `opencode.json` gerenciado por este repo)

---

### 2.3 `scripts/bootstrap_repo/vscode-sync.ps1` — estender `Sync-Mcp`

No hashtable `$newServers`, adicionar após `crawl4ai`:

```powershell
"codebase-memory" = [ordered]@{
    "command" = "codebase-memory-mcp"
    "args"    = @()
}
"doctree" = [ordered]@{
    "command" = "bunx"
    "args"    = @("doctree-mcp")
    "env"     = [ordered]@{
        "DOCS_ROOT" = "${workspaceFolder}"
    }
}
```

---

### 2.4 `commands/codememory_docktree.md` — criar command

Invocado como `/codememory_docktree` no OpenCode.
Sincronizado automaticamente como `codememory_docktree.prompt.md` no
VS Code via `vscode-sync.ps1`.

Conteúdo: guia o agente a:
1. Chamar `index_repository` no projeto atual
2. Verificar doctree com `search_documents`
3. Reportar status e exibir cheatsheet dos tools

---

### 2.5 `tests/scripts/bootstrap_repo/opencode-install-deps-test.bats`
       — atualizar testes

Adicionar casos para os 2 novos blocos, seguindo o padrão existente:
- `[bun] reporta OK quando bun está disponível`
- `[bun] reporta MISSING quando bun está ausente`
- `[codebase-memory-mcp] reporta OK quando binário está disponível`
- `[codebase-memory-mcp] reporta MISSING quando binário está ausente`

---

## 3. Ordem de implementação

1. `opencode.json`
2. `scripts/bootstrap_repo/opencode-install-deps` +
   `tests/.../opencode-install-deps-test.bats` (juntos)
3. `scripts/bootstrap_repo/vscode-sync.ps1`
4. `commands/codememory_docktree.md`
5. `make test` — verificar suite completa

---

## 4. Sem novos arquivos de teste para `vscode-sync.ps1`

PS1 não é testável via BATS. Não existe `vscode-sync-test.bats` no repo
e não será criado neste escopo.
