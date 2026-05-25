# Guia de Instalação — Combo 1: codebase-memory-mcp + doctree-mcp

**Data:** 25/05/2026
**Status:** Guia finalizado — pronto para uso

---

## 1. Resumo

Navegação estrutural de código (grafo AST, 155 linguagens) +
navegação hierárquica de documentação (BM25, sem embeddings).
Agnóstico de linguagem e stack. Ambos MIT. Zero custo de API.

| Ferramenta | Stars | Licença | Redução de tokens |
|---|---|---|---|
| codebase-memory-mcp | 2.493 | MIT | 120x (paper arXiv:2603.27277) |
| doctree-mcp | 1 | MIT | 2K–8K tokens vs 4K–20K de RAG |

---

## 2. Pré-requisitos

| Ferramenta | Para que | Verificar |
|---|---|---|
| `curl` ou `wget` | Baixar binário | `curl --version` |
| `bun` | Executar doctree-mcp via bunx | `bun --version` |

**Instalar bun** (se ausente):

```bash
curl -fsSL https://bun.sh/install | bash
```

---

## 3. Instalar codebase-memory-mcp

Binário estático — zero dependências de runtime.

```bash
curl -fsSL \
  https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh \
  | bash
```

Verificar:

```bash
codebase-memory-mcp --version
```

> **Nota**: o comando `codebase-memory-mcp install` auto-detecta e configura
> agentes (OpenCode, VS Code, etc.) automaticamente. Use-o se não gerenciar
> o `opencode.json` por um repo de config central — nesse caso pule as
> seções 4 e 5 e execute apenas `codebase-memory-mcp install`.

---

## 4. Configurar OpenCode

Adicione ao `~/.config/opencode/opencode.json`, seção `mcp`:

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

> `DOCS_ROOT` não é definido aqui — doctree-mcp usa o default `./docs`
> relativo à raiz do projeto onde o OpenCode for iniciado.
> Para sobrescrever: `export DOCS_ROOT=/caminho/para/docs` antes de abrir
> o OpenCode, ou defina `"env": {"DOCS_ROOT": "."}` para indexar todo o
> projeto.

---

## 5. Configurar VS Code (Copilot Chat)

Adicione ao arquivo global de MCP do VS Code:
- Windows: `%APPDATA%\Code\User\mcp.json`
- Linux/macOS: `~/.config/Code/User/mcp.json`

Seção `servers`:

```json
"codebase-memory": {
  "command": "codebase-memory-mcp",
  "args": []
},
"doctree": {
  "command": "bunx",
  "args": ["doctree-mcp"],
  "env": {
    "DOCS_ROOT": "${workspaceFolder}"
  }
}
```

> `${workspaceFolder}` resolve dinamicamente para a raiz do workspace aberto.

---

## 6. Smoke test

Reinicie o agente após configurar. Então:

**codebase-memory-mcp:**
```
use the tool get_architecture to describe this project
```
Esperado: linguagens, packages, entry points em ~200 tokens.

**doctree-mcp:**
```
use search_documents to find documentation about authentication
```
Esperado: lista ranked de seções relevantes.

---

## 7. Referência rápida de uso

### codebase-memory-mcp

| Quando usar | Tool |
|---|---|
| Primeira vez no projeto | `index_repository` |
| Visão geral da arquitetura | `get_architecture` |
| Quem chama função X? | `trace_call_path` |
| Busca por nome de símbolo | `search_graph` |
| Corpo de uma função específica | `get_code_snippet` |
| Impacto de uma mudança | `detect_changes` |
| Busca semântica | `semantic_query` |

### doctree-mcp — ordem obrigatória

```
1. search_documents("termo")        → docs/seções rankeados
2. get_tree(doc_id)                 → outline hierárquico
3. navigate_tree(doc_id, node_id)   → seção + descendentes
4. get_node_content(doc_id, [...])  → conteúdo exato
```

> Nunca pule `get_tree` — evita buscar conteúdo de seções erradas.

---

## 8. Erros comuns

**`codebase-memory-mcp: command not found`**
Binário fora do PATH. Adicione ao shell:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

**`bunx: command not found`**
Bun não instalado ou fora do PATH. Reinstale e reinicie o terminal.

**doctree-mcp não encontra documentos**
`DOCS_ROOT` aponta para diretório sem `.md`. Teste local:
```bash
DOCS_ROOT=./docs bunx doctree-mcp
```

**`get_architecture` retorna grafo vazio**
`index_repository` não foi chamado ainda nesta instalação.
O grafo persiste entre sessões mas precisa ser indexado ao menos uma vez.

**Arquivos novos não aparecem no grafo**
O background watcher pode ter falhado. Force reindex chamando
`index_repository` — é incremental e rápido.
