# Plano — Knowledge-RAG MCP por repo para OpenCode e Copilot

Status: IMPLEMENTADO

---

## 1. Resumo

Separar a configuracao do Knowledge-RAG por projeto, sem depender de um unico
servidor MCP global com variaveis de ambiente compartilhadas entre varios repos.

O Knowledge-RAG (v4.0.0+) substitui o doctree-mcp como servidor MCP de
documentacao, oferecendo busca hibrida (semantica + BM25 + cross-encoder reranking).

A ideia e tratar dois cenarios distintos:
- OpenCode
- GitHub Copilot via `avelino/mcp`

O bootstrap deste repo continua cuidando apenas da instalacao global das
ferramentas. A configuracao do Knowledge-RAG para um projeto especifico passa a ser
responsabilidade do fluxo `/indexar-codebase` executado dentro do repo alvo.

Regra obrigatoria de compatibilidade: o fluxo atual do `/indexar-codebase`
precisa ser preservado. Antes de qualquer configuracao MCP do Knowledge-RAG, ele deve
continuar verificando se existe `.env-knowledge-rag` e, se nao existir, continuar
perguntando ao humano quais pastas deseja indexar. Esse comportamento nao pode
ser removido nem atropelado pela nova arquitetura.

---

## 2. Problema

Conflito entre:
- configuracao MCP global do `avelino/mcp`
- configuracao de collections do Knowledge-RAG por repo
- necessidade de indexar conjuntos de documentos diferentes por projeto

Exemplos:
- um repo pode usar apenas `./docs`
- outro pode usar `KNOWLEDGE_RAG_COLLECTIONS` com `./docs`, `./agents`, `./skills`, `./plan`

Se todos os projetos reutilizam o mesmo nome de servidor MCP e as mesmas vars de
ambiente globais, um projeto pode sobrescrever a configuracao do outro.

Isso e especialmente problematico quando ha varios projetos ativos no mesmo
ambiente.

---

## 3. Objetivo

Permitir que cada projeto tenha sua propria configuracao Knowledge-RAG, com regras
claras para:
- instalacao do servidor no contexto do OpenCode
- instalacao da entrada no `servers.json` do `avelino/mcp` para Copilot
- definicao explicita de qual MCP o Copilot deve usar naquele repo
- fallback para configuracao generica quando o repo nao define collections customizadas
- preservacao do fluxo atual de definicao de `.env-knowledge-rag` pelo humano

---

## 4. Decisoes arquiteturais

### 4.1 Remover scripts e configuracoes legadas do doctree

Scripts removidos/replace:
- `scripts/doctree/doctree-run.sh` - substituido por `knowledge-rag --mcp`
- `scripts/doctree/start-doctree.sh` - nao mais necessario
- `.env-doctree` - migrado para `.env-knowledge-rag`

### 4.2 Configuracao global vs configuracao por repo

#### Bootstrap deste repo
O bootstrap deste repo:
- instala ferramentas globais (incluindo knowledge-rag via pipx)
- nao configura um repo especifico para usar Knowledge-RAG

Portanto, ele nao deve assumir collections de um projeto arbitrario.

#### `/indexar-codebase`
O comando `/indexar-codebase`, executado no repo alvo, passa a ser o ponto
responsavel por configurar o Knowledge-RAG daquele projeto.

---

## 5. Regras por ambiente

### 5.1 OpenCode

No OpenCode, a configuracao sera escrita no proprio projeto, dentro de
`.opencode/`.

O fluxo `/indexar-codebase` deve:
1. verificar se o Knowledge-RAG esta instalado
2. se nao estiver, instalar via pipx
3. escrever a configuracao MCP do projeto em `.opencode/`
4. usar configuracao:
   - especifica, quando houver `.env-knowledge-rag` com `KNOWLEDGE_RAG_COLLECTIONS`
   - generica, quando nao houver configuracao especifica

#### Regra de configuracao OpenCode
- se existir `.env-knowledge-rag` com collections especificas, escrever essa configuracao no
  MCP local do projeto
- se nao existir, usar configuracao generica
- o fluxo deve avisar explicitamente quando estiver usando a configuracao
  generica

### 5.2 Copilot + `avelino/mcp`

No Copilot, a configuracao MCP fica no arquivo global do `avelino/mcp`:
- `~/.config/mcp/servers.json`

Como esse arquivo e global, o projeto precisa receber uma entrada nomeada de
forma unica.

#### Nome da entrada
Padrao:
- `knowledge-rag-<basename-do-repo>`

Exemplo:
- repo `opencode-config` -> `knowledge-rag-opencode-config`

#### Regra de criacao da entrada
O fluxo `/indexar-codebase` deve:
- editar diretamente `~/.config/mcp/servers.json`
- criar ou atualizar a entrada `knowledge-rag-<basename>` quando o projeto tiver
  collections de docs especificas
- usar a entrada generica `knowledge-rag` quando o projeto nao tiver configuracao
  especifica
- avisar explicitamente quando estiver usando a entrada generica

#### Regra de env no Copilot
Como o `avelino/mcp` suporta `env` no `servers.json`, a entrada do projeto deve
carregar diretamente:
- `KNOWLEDGE_RAG_COLLECTIONS`: formato `"./path1:collection1,./path2:collection2,..."`

Exemplo:
```json
{
  "knowledge-rag-opencode-config": {
    "command": "knowledge-rag",
    "args": ["--mcp"],
    "env": {
      "KNOWLEDGE_RAG_COLLECTIONS": "./docs:docs,./agents:agents,./skills:skills,./plan:plan"
    }
  }
}
```

Sem wrapper para resolver repo em runtime.

---

## 6. Instrucao local do Copilot no repo

Para evitar ambiguidade sobre qual MCP usar no projeto atual, o fluxo
`/indexar-codebase` deve gerar uma instruction local do Copilot dentro de:
- `.github/`

Arquivo previsto:
- `.github/copilot-knowledge-rag.instructions.md`

Essa instruction deve conter:
- o nome ja resolvido do MCP para aquele projeto
- lista completa das ferramentas disponiveis no knowledge-rag

Exemplo conceitual:
- usar `knowledge-rag-opencode-config` neste repo
- ou usar `knowledge-rag` quando o projeto estiver na configuracao generica

Objetivo:
- nao depender de descoberta dinamica via wrapper
- deixar explicito para o agente qual servidor Knowledge-RAG consultar

---

## 7. Ferramentas disponiveis no Knowledge-RAG v4.0.0

Lista completa das 12 ferramentas MCP:

| Nome | Descricao |
|------|-----------|
| `search_knowledge` | Busca hibrida (semantica + BM25 + reranking) |
| `get_document` | Obter conteudo completo por filepath |
| `list_documents` | Listar documentos indexados |
| `list_categories` | Listar categorias disponiveis |
| `get_index_stats` | Estatisticas do indice |
| `reindex_documents` | Reindexar documentos (force/full_rebuild) |
| `add_document` | Adicionar novo documento |
| `update_document` | Atualizar documento existente |
| `remove_document` | Remover documento |
| `add_from_url` | Adicionar documento de URL |
| `search_similar` | Buscar documentos semanticamente similares |
| `evaluate_retrieval` | Avaliar qualidade da busca |

---

## 8. Fonte de verdade para configuracao especifica

A configuracao especifica do Knowledge-RAG por projeto sera derivada de:
- `.env-knowledge-rag`

Campo relevante:
- `KNOWLEDGE_RAG_COLLECTIONS`

Regra:
- formato: `"./path1:collection1,./path2:collection2,..."`
- cada par `path:collection` representa um diretorio e seu nome de collection
- ausencia do arquivo ou variavel implica fallback generico
- antes de assumir esse fallback, o `/indexar-codebase` deve preservar o fluxo
  atual: verificar se `.env-knowledge-rag` existe e, se nao existir, perguntar ao
  humano quais pastas deseja indexar

---

## 9. Regras de naming

### 9.1 Identificador do projeto

Usado:
- `basename` do diretorio do repo

Exemplo:
- `/mnt/c/Users/ur5y/Projetos/opencode-config` -> `opencode-config`

---

## 10. Fluxo detalhado do `/indexar-codebase`

Ver `commands/index-codebase.md` para o fluxo completo atualizado.

---

## 11. Migracao do doctree-mcp legado

Para repos que ainda usam `.env-doctree`:

1. Converter formato: `DOCS_ROOTS="./docs:1.0,..."` -> `KNOWLEDGE_RAG_COLLECTIONS="./docs:docs,..."`
2. Remover pesos (nao sao mais usados no knowledge-rag)
3. Renomear arquivo: `.env-doctree` -> `.env-knowledge-rag`
4. Atualizar `~/.config/mcp/servers.json`: trocar `doctree-mcp-*` por `knowledge-rag-*`
5. Atualizar comandos: `bunx doctree-mcp` -> `knowledge-rag --mcp`
6. Atualizar nome das ferramentas nas documentacoes

---

## 12. Checklist de Implementacao

- [x] Instalacao do knowledge-rag via pipx
- [x] Configuracao em ~/.config/mcp/servers.json
- [x] Arquivo .env-knowledge-rag criado
- [x] commands/index-codebase.md atualizado
- [x] .github/copilot-specific.instructions.md atualizado
- [x] .github/copilot-knowledge-rag.instructions.md criado
- [x] skills/doc-read/SKILL.md (pendente - referencia doctree)
- [ ] Testar indexacao em um repo
