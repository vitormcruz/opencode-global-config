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

### B1. `opencode.json` — adicionar MCPs como stdio

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

**Bloco `[codebase-memory-mcp]`** — binário via npm:
- `has_cmd codebase-memory-mcp` → OK
- Ausente: `confirm_action` → `npm install -g codebase-memory-mcp`
- **Não** roda `codebase-memory-mcp install` após (evita sobrescrever
  `opencode.json` gerenciado por este repo)

### B3. `opencode-install-deps-test.bats` — 4 novos testes

- `[bun]` reporta OK quando bun está disponível
- `[bun]` reporta MISSING quando bun está ausente
- `[codebase-memory-mcp]` reporta OK quando binário está disponível
- `[codebase-memory-mcp]` reporta MISSING quando binário está ausente

### B4. Criar `commands/index-codebase.md`

Comando `/index-codebase`. Prompt que instrui o agente a:

1. **Indexar repo no codebase-memory**:
   `codebase-memory-mcp cli index_repository '{"repo_path": "."}'`
2. **Configurar doctree**:
   - Verificar se pasta `docs/` existe no repo
   - Se existir, configurar `DOCS_ROOT=./docs` e indexar
   - Se não existir, avisar o usuário e pular
3. **Instalar git hook `post-commit`**:
   - Criar `.git/hooks/post-commit` executável
   - Hook roda `codebase-memory-mcp cli index_repository` automaticamente
   - Re-indexa o codebase-memory a cada commit
   - Se hook já existe, perguntar antes de sobrescrever
4. **Reportar status**:
   - Exibir resultado da indexação
   - Confirmar se doctree foi configurado
   - Confirmar se hook foi instalado

Sincroniza automaticamente como `index-codebase.prompt.md` no
VS Code via `vscode-sync.ps1`.

### B5. Testes de integração dos MCPs (padrão crawl4ai)

Criar pastas de testes seguindo o padrão de `tests/scripts/crawl4ai/`:

**`tests/scripts/codebase-memory/`**:
- `install-codebase-memory-test.bats` — testes do script de instalação
- `codebase-memory-real-test.bats` — testes do MCP real (se disponível)

**`tests/scripts/doctree/`**:
- `install-doctree-test.bats` — testes do script de instalação
- `doctree-real-test.bats` — testes do MCP real (se disponível)

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

### Modificações (4 arquivos)

| Arquivo | Mudança |
|---|---|
| `AGENTS.md` | Remover seção graphify |
| `.opencode/opencode.json` | Remover plugin graphify |
| `opencode.json` | Adicionar MCPs codebase-memory + doctree |
| `scripts/bootstrap_repo/opencode-install-deps` | Remover graphify, adicionar bun + codebase-memory |
| `tests/scripts/bootstrap_repo/opencode-install-deps-test.bats` | Atualizar comentário, adicionar 4 testes |

### Criações (5 arquivos + 2 pastas)

| Arquivo | Conteúdo |
|---|---|
| `commands/index-codebase.md` | Comando /index-codebase (prompt) |
| `tests/scripts/codebase-memory/` | Pasta de testes |
| `tests/scripts/codebase-memory/install-codebase-memory-test.bats` | Testes de instalação |
| `tests/scripts/codebase-memory/codebase-memory-real-test.bats` | Testes do MCP real |
| `tests/scripts/doctree/` | Pasta de testes |
| `tests/scripts/doctree/install-doctree-test.bats` | Testes de instalação |
| `tests/scripts/doctree/doctree-real-test.bats` | Testes do MCP real |

---

## Ordem de execução

1. **Remoções graphify** (A1-A5)
2. **Adições codebase-memory + doctree** (B1-B5)
3. **Limpeza e validação** (C1-C2)
4. **Commit** (após validação do humano)
