# Plano de Remocao: knowledge-rag

## Contexto

O knowledge-rag esta sendo removido completamente do repositorio.
O codebase-memory ja indexa documentacao Markdown (nos do tipo Section),
tornando o knowledge-rag redundante.

## Fases Concluidas

### Fase 1: Remover Diretorios e Arquivos
- [x] `/scripts/knowledge-rag/` (install.sh e run.sh)
- [x] `/data/chroma_db/` (banco ChromaDB)
- [x] `/data/index_metadata.json`
- [x] `/plan/knowledge-rag-por-repo.md`
- [x] `/tests/scripts/knowledge-rag/` (3 arquivos .bats)

### Fase 2: Atualizar Bootstrap e Scripts
- [x] `scripts/bootstrap_repo/configurar-repo.sh` - removido run_knowledge_rag
- [x] `scripts/bootstrap_repo/wsl-install-deps.sh` - removido 50+ linhas de verificacao
- [x] `scripts/bootstrap_repo/copilot-sync.ps1` - removido sync do knowledge-rag
- [x] `scripts/bootstrap_repo/wsl-copilot-sync.sh` - removido sync do knowledge-rag

### Fase 3: Atualizar Configuracoes
- [x] `opencode.json` - removida entrada do MCP
- [x] `AGENTS.md` - removida secao do knowledge-rag
- [x] `.github/copilot-specific.instructions.md` - atualizado para codebase-memory
- [x] `.github/copilot-codebase-memory.instructions.md` - atualizado (renomeado de knowledge-rag)

### Fase 4: Atualizar Makefile
- [x] Removido `/scripts/knowledge-rag` do target `test-tools`

### Fase 5: Atualizar Documentacao
- [x] `README.md` - removidas referencias
- [x] `commands/index-codebase.md` - reescrito para codebase-memory unificado

### Fase 6: Atualizar Skills
- [x] `skills/code-explorer-priority/SKILL.md` - atualizado para codebase-memory

### Fase 7: Commit Final
- [ ] Executar `git add .`
- [ ] Executar `git commit` com mensagem

## Resultado

O repositorio agora usa apenas `codebase-memory` para indexacao de codigo
**e** documentacao, simplificando a arquitetura e eliminando redundancia.
