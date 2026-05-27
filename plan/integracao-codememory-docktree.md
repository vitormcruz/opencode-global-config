# Plano: Integrar codebase-memory + doctree + Remover graphify

**Data:** 27/05/2026
**Status:** Aguardando implementação
**Origem:** plan/codememory_docktree-integracao-repo.md (este arquivo substitui)

---

## PARTE A — Remover graphify

### A1. `AGENTS.md` — remover seção "graphify — Gate Obrigatório"

- Remover toda a seção que obriga leitura do `graphify-out/GRAPH_REPORT.md`
  antes de qualquer ação no codebase
- Isso libera o agente de depender do grafo para decisões

### A2. `.opencode/opencode.json` — remover plugin graphify

- Remover entrada `.opencode/plugins/graphify.js` do array `plugin`
- Se o array ficar vazio, remover a chave `plugin` inteira

### A3. Remover arquivos/diretórios do graphify

| Caminho | Ação |
|---|---|
| `.opencode/plugins/graphify.js` | Deletar |
| `scripts/graphify/install` | Deletar |
| `skills/graphify/` | Deletar (pasta inteira) |
| `tests/scripts/graphify/` | Deletar (pasta inteira) |
| `plan/graphify-context-test.md` | Deletar |

### A4. `opencode-install-deps` — remover bloco `[graphify]`

- Remover linhas 559-585 (bloco completo `[graphify]`)
- Atualizar comentário da linha 491:
  - De: `"Requerido >= 3.10 para docling e graphify"`
  - Para: `"Requerido >= 3.10 para docling"`

### A5. `opencode-install-deps-test.bats` — atualizar comentário

- Linha 275: `# docling/graphify` → `# docling`

---

## PARTE B — Adicionar codebase-memory + doctree

### B1. `opencode.json` — adicionar MCPs

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

### B2. `opencode-install-deps` — blocos `[bun]` e `[codebase-memory-mcp]`

Inserir após onde estava o bloco `[graphify]`, antes do sumário sudo.

**Bloco `[bun]`** — necessário para doctree-mcp via bunx:
- `has_cmd bun` → OK
- Ausente: `confirm_action` → `curl -fsSL https://bun.sh/install | bash`
- Sem sudo

**Bloco `[codebase-memory-mcp]`** — binário estático:
- `has_cmd codebase-memory-mcp` → OK
- Ausente: `confirm_action` → instala via installer oficial
- **Não** roda `codebase-memory-mcp install` após (evita sobrescrever
  `opencode.json` gerenciado por este repo)

### B3. `opencode-install-deps-test.bats` — 4 novos testes

- `[bun]` reporta OK quando bun está disponível
- `[bun]` reporta MISSING quando bun está ausente
- `[codebase-memory-mcp]` reporta OK quando binário está disponível
- `[codebase-memory-mcp]` reporta MISSING quando binário está ausente

### B4. `vscode-sync.ps1` — estender Sync-Mcp

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

### B5. Criar `commands/codememory_docktree.md`

Invocado como `/codememory_docktree` no OpenCode.
Sincronizado automaticamente como `codememory_docktree.prompt.md` no
VS Code via `vscode-sync.ps1`.

Conteúdo: guia o agente a:
1. Chamar `index_repository` no projeto atual
2. Verificar doctree com `search_documents`
3. Reportar status e exibir cheatsheet dos tools

---

## PARTE C — Limpeza final

### C1. Remover planos

- Deletar `plan/codememory_docktree-integracao-repo.md`
- Deletar `plan/integracao-codememory-docktree.md` (este arquivo)

### C2. Validação

- Executar `make test` — garantir suite completa passa
- Executar via WSL: `wsl -- bash -ic "cd <repo> && make test"`

---

## Resumo de arquivos

### Remoções (7 deletados)

| Arquivo | Motivo |
|---|---|
| `.opencode/plugins/graphify.js` | Plugin removido |
| `scripts/graphify/install` | Script removido |
| `skills/graphify/` | Skill removida (pasta) |
| `tests/scripts/graphify/` | Testes removidos (pasta) |
| `plan/graphify-context-test.md` | Plano removido |
| `plan/codememory_docktree-integracao-repo.md` | Plano original — substituído |
| `plan/integracao-codememory-docktree.md` | Este plano — auto-destruir |

### Modificações (5 arquivos)

| Arquivo | Mudança |
|---|---|
| `AGENTS.md` | Remover seção graphify |
| `.opencode/opencode.json` | Remover plugin graphify |
| `opencode.json` | Adicionar MCPs codebase-memory + doctree |
| `scripts/bootstrap_repo/opencode-install-deps` | Remover graphify, adicionar bun + codebase-memory |
| `tests/scripts/bootstrap_repo/opencode-install-deps-test.bats` | Atualizar comentário, adicionar 4 testes |
| `scripts/bootstrap_repo/vscode-sync.ps1` | Adicionar MCPs codebase-memory + doctree |

### Criações (1 arquivo)

| Arquivo | Conteúdo |
|---|---|
| `commands/codememory_docktree.md` | Command /codememory_docktree |

---

## Ordem de execução

1. **Remoções graphify** (A1-A5)
2. **Adições codebase-memory + doctree** (B1-B5)
3. **Limpeza e validação** (C1-C2)
4. **Commit** (após validação do humano)
