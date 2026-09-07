---
description: Indexa o repositorio no codebase-memory (auto-index gerencia atualizacoes automaticamente)
---

Indexe o repositorio atual no codebase-memory.

> **Nota:** O auto-index ja esta configurado globalmente (`auto_index=true`) durante a instalacao. 
> Novos projetos sao indexados automaticamente na primeira conexao, e projetos existentes 
> sao monitorados pelo background watcher para deteccao de mudancas baseada em git.
> Nao e necessario configurar hooks git manualmente.

Siga este fluxo estritamente.

## Modo de execucao obrigatorio: etapas sequenciais e bloqueantes

- Este fluxo e composto por **3 etapas sequenciais e bloqueantes**.
- Execute **somente uma etapa por vez**.
- **Nao inicie a etapa N+1 antes de concluir totalmente a etapa N**.
- Concluir uma etapa significa:
  - executar apenas as acoes permitidas daquela etapa
  - obter os resultados esperados daquela etapa
  - registrar/exibir esses resultados ao humano quando a propria etapa exigir
  - confirmar internamente que nenhuma acao pendente daquela etapa ficou para depois
- Enquanto a etapa atual nao estiver concluida, **e proibido**:
  - ler arquivos de etapas futuras
  - inspecionar configuracoes de etapas futuras
  - executar comandos de etapas futuras
  - pedir confirmacoes relativas a etapas futuras
  - preparar mudancas relativas a etapas futuras
- Antes de qualquer acao, valide mentalmente: `esta acao pertence a etapa atual?`
- Se a resposta for nao, nao execute.
- Se violar a ordem, pare, reconheca o erro e retome a partir da ultima etapa concluida corretamente, sem adiantar nada.

## Regra de progressao automatica entre etapas

- Ao concluir uma etapa, o agente deve prosseguir automaticamente para a etapa seguinte.
- Nao espere nova mensagem do humano quando a etapa atual ja estiver
  concluida e a proxima etapa nao depender de confirmacao, decisao humana ou
  tratamento de erro.
- O fluxo e bloqueante apenas no sentido de ordem: a etapa N+1 depende do termino completo da etapa N.
- O fluxo nao exige pausa entre etapas ja resolvidas.
- O agente deve apenas registrar brevemente o resultado da etapa concluida e seguir adiante.
- Pare somente quando:
  - houver necessidade de confirmacao para criar, editar, sobrescrever ou appendar arquivos
  - houver necessidade de escolher entre alternativas
  - houver erro bloqueante
  - houver inconsistencia que exija esclarecimento

## Etapa 1 - Verificar estado atual no codebase-memory

**Objetivo:** descobrir se o repositorio atual ja esta indexado.

**Acoes permitidas nesta etapa:**
- listar projetos no `codebase-memory`
- comparar os projetos encontrados com o repositorio atual
- informar ao humano se o repo ja estava indexado ou nao

**Execucao:**
- No **GitHub Copilot**, execute: `codebase-memory-mcp cli list_projects '{}'`
- No **OpenCode**, execute o mesmo CLI no WSL:
  `codebase-memory-mcp cli list_projects '{}'`
- Se o repositorio atual ja estiver indexado, informe isso ao usuario antes de reindexar.

**Condicao de encerramento da etapa:**
- o estado atual de indexacao do repo foi determinado e comunicado ao humano.

## Etapa 2 - Indexar repositorio no codebase-memory

**Dependencia obrigatoria:**
- so pode comecar apos o encerramento da **Etapa 1**.

**Objetivo:** indexar o repositorio atual no `codebase-memory`.

**Acoes permitidas nesta etapa:**
- executar a indexacao no `codebase-memory`
- capturar e exibir o resultado da indexacao

**Execucao:**
- No **GitHub Copilot**, execute com JSON posicional unico e `repo_path` absoluto, por exemplo:
  `codebase-memory-mcp cli index_repository '{"repo_path":"C:\\Users\\<usuario>\\Projetos\\opencode-config"}'`
- Use `repo_path` absoluto em ambos os ambientes para evitar ambiguidades.
- No **OpenCode** ou em hooks/scripts locais, use o mesmo CLI:
  `codebase-memory-mcp cli index_repository '{"repo_path": "."}'`
- Exiba o resultado da indexacao.

**O que e indexado:**
- O `codebase-memory` indexa **codigo e documentacao** em uma unica base de conhecimento.
- Arquivos Markdown sao indexados como nos do tipo `Section`, permitindo buscas semanticas.
- Use Cypher para buscar em documentos: `MATCH (s:Section) WHERE s.name CONTAINS "termo" RETURN s.name, s.file`

**Condicao de encerramento da etapa:**
- a indexacao no `codebase-memory` terminou e o resultado foi exibido.

## Etapa 3 - Verificar instrucoes de codebase-memory no AGENTS.md

**Dependencia obrigatoria:**
- so pode comecar apos o encerramento da **Etapa 2**.

**Objetivo:** garantir que o AGENTS.md do repositorio documenta a
descoberta de codigo via codebase-memory.

**Acoes permitidas nesta etapa:**
- verificar se o `AGENTS.md` do repositorio documenta o uso do
  codebase-memory para descoberta de codigo
- informar ao humano o estado dessas instrucoes

**Execucao:**
- Verifique se o `AGENTS.md` do repo contem uma secao de descoberta de
  codigo mencionando o codebase-memory (regra de usar o CLI antes de
  grep/glob).
- Se nao existir, informe ao humano e sugira o texto da secao. Nao edite
  o `AGENTS.md` sem confirmacao explicita.
- Se existir, verifique se a regra esta coerente com o fluxo deste
  comando e pergunte ao humano se precisa de atualizacao.

**Condicao de encerramento da etapa:**
- o estado das instrucoes de codebase-memory no `AGENTS.md` foi
  determinado e comunicado ao humano.

## Resumo final

Ao finalizar todas as etapas, informe ao humano:

1. **Status da indexacao:** numero de nos e arestas no grafo
2. **Instrucoes locais:** estado das instrucoes de codebase-memory no
   `AGENTS.md` do repositorio
3. **Auto-index:** confirmacao de que o auto-index global esta habilitado - o
   grafo sera mantido automaticamente atualizado via background watcher
4. **Uso:** exemplos de comandos para explorar codigo e documentacao
