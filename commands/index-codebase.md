---
description: Indexa o repositorio no codebase-memory, configura knowledge-rag por repo e instala git hook post-commit
---

Indexe o repositorio atual no codebase-memory e configure o knowledge-rag.

Siga este fluxo estritamente.

## Modo de execucao obrigatorio: etapas sequenciais e bloqueantes

- Este fluxo e composto por **7 etapas sequenciais e bloqueantes**.
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
- Nao espere nova mensagem do humano quando a etapa atual ja estiver concluida e a proxima etapa nao depender de confirmacao, decisao humana ou tratamento de erro.
- O fluxo e bloqueante apenas no sentido de ordem: a etapa N+1 depende do termino completo da etapa N.
- O fluxo nao exige pausa entre etapas ja resolvidas.
- O agente deve apenas registrar brevemente o resultado da etapa concluida e seguir adiante.
- Excecao importante deste fluxo: se a Etapa 3 ja resolveu `.env-knowledge-rag`, a Etapa 4 deve materializar automaticamente a configuracao derivada, sem pedir nova confirmacao para editar `~/.config/mcp/servers.json`, criar `.github/copilot-knowledge-rag.instructions.md` ou escrever a configuracao local equivalente.
- Pare somente quando:
  - houver necessidade de confirmacao para criar, editar, sobrescrever ou appendar arquivos **fora** da materializacao automatica da Etapa 4
  - houver necessidade de escolher entre alternativas
  - houver erro bloqueante
  - houver inconsistencia que exija esclarecimento

## Regra central sobre `.env-knowledge-rag`

- A existencia de `.env-knowledge-rag` na raiz do repo indica **configuracao especifica por repositorio**.
- Nessa situacao, **nao basta** manter ou usar o MCP generico `knowledge-rag`.
- O fluxo **deve materializar** uma entrada MCP especifica por repo para que `KNOWLEDGE_RAG_COLLECTIONS` seja realmente aplicada.
- Sem essa materializacao, a configuracao tende a cair no comportamento generico, o que e insuficiente quando o repo declarou multiplas collections.
- Portanto, sempre trate `.env-knowledge-rag` como fonte de verdade e como sinal de especificidade do projeto.

## Etapa 1 - Verificar estado atual no codebase-memory

**Objetivo:** descobrir se o repositorio atual ja esta indexado.

**Acoes permitidas nesta etapa:**
- listar projetos no `codebase-memory`
- comparar os projetos encontrados com o repositorio atual
- informar ao humano se o repo ja estava indexado ou nao

**Acoes proibidas nesta etapa:**
- indexar o repositorio
- ler ou criar `.env-knowledge-rag`
- configurar knowledge-rag
- indexar knowledge-rag
- ler, verificar, criar ou modificar `.git/hooks/post-commit`

**Execucao:**
- No **GitHub Copilot**, execute: `mcp codebase-memory list_projects`
- No **OpenCode**, use o fluxo nativo equivalente para listar projetos.
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

**Acoes proibidas nesta etapa:**
- ler ou criar `.env-knowledge-rag`
- configurar knowledge-rag
- indexar knowledge-rag
- ler, verificar, criar ou modificar `.git/hooks/post-commit`

**Execucao:**
- No **GitHub Copilot**, execute com JSON posicional unico e `repo_path` absoluto, por exemplo:
  `mcp codebase-memory index_repository '{"repo_path":"/mnt/c/Users/ur5y/Projetos/opencode-config"}'`
- Nao use `--repo_path "."` no Copilot, pois essa sintaxe falha com o wrapper `mcp` neste ambiente.
- No **OpenCode** ou em hooks/scripts locais, use:
  `codebase-memory-mcp cli index_repository '{"repo_path": "."}'
- Exiba o resultado da indexacao.

**Condicao de encerramento da etapa:**
- a indexacao no `codebase-memory` terminou e o resultado foi exibido.

## Etapa 3 - Resolver `.env-knowledge-rag`

**Dependencia obrigatoria:**
- so pode comecar apos o encerramento da **Etapa 2**.

**Objetivo:** determinar a fonte de verdade do knowledge-rag neste repo.

**Acoes permitidas nesta etapa:**
- verificar se `.env-knowledge-rag` existe
- ler e exibir seu conteudo, se existir
- listar pastas da raiz, se o arquivo nao existir
- perguntar ao humano se deseja criar `.env-knowledge-rag`
- se houver confirmacao, perguntar quais pastas/collections indexar
- criar `.env-knowledge-rag` somente se o humano confirmar

**Acoes proibidas nesta etapa:**
- materializar configuracao MCP do knowledge-rag antes de resolver o `.env-knowledge-rag`
- indexar knowledge-rag
- ler, verificar, criar ou modificar `.git/hooks/post-commit`

**Execucao:**
- Verifique se o arquivo `.env-knowledge-rag` ja existe na raiz do repo.
- Se ja existir, exiba o conteudo, trate-o como fonte de verdade do repo e pule a criacao.
- Se nao existir, liste as pastas detectadas na raiz e pergunte primeiro se o humano quer criar o `.env-knowledge-rag` para este repo.
- Somente se o humano confirmar a criacao, pergunte:
  `Quais diretorios indexar no knowledge-rag? [docs/agents/skills/plan — padrao: docs]`
- Se o humano nao quiser criar o arquivo, nao crie `.env-knowledge-rag`; siga com fallback generico e deixe isso explicito no status final.
- Se o usuario escolher **uma pasta**, crie `.env-knowledge-rag` com:
  ```bash
  KNOWLEDGE_RAG_COLLECTIONS="./docs:docs"
  ```
  Ajuste o caminho e nome da collection conforme a pasta escolhida.
- Se o usuario quiser **multiplas pastas**, crie `.env-knowledge-rag` com:
  ```bash
  KNOWLEDGE_RAG_COLLECTIONS="./docs:docs,./agents:agents,./skills:skills,./plan:plan"
  ```
  Ajuste os caminhos e nomes das collections conforme escolha do usuario.
- **Importante:** o formato do knowledge-rag e `path:collection` (diferente do doctree que usava `path:peso`).

**Condicao de encerramento da etapa:**
- o repo ficou com uma fonte de verdade resolvida para knowledge-rag: `.env-knowledge-rag` existente, `.env-knowledge-rag` criado com confirmacao, ou fallback generico explicitamente assumido.

## Etapa 4 - Materializar configuracao knowledge-rag por repo

**Dependencia obrigatoria:**
- so pode comecar apos o encerramento da **Etapa 3**.

**Objetivo:** transformar a decisao da etapa anterior em configuracao efetiva para OpenCode e Copilot.

**Acoes permitidas nesta etapa:**
- derivar configuracao a partir de `.env-knowledge-rag`
- usar fallback generico quando `.env-knowledge-rag` nao definir `KNOWLEDGE_RAG_COLLECTIONS`
- escrever configuracao local do OpenCode em `.opencode/`
- editar `~/.config/mcp/servers.json` no Copilot
- gerar `.github/copilot-knowledge-rag.instructions.md`

**Acoes proibidas nesta etapa:**
- indexar knowledge-rag antes de concluir a materializacao
- ler, verificar, criar ou modificar `.git/hooks/post-commit`

**Execucao:**
- Esta etapa e **automatizada** depois que a Etapa 3 estiver resolvida.
- Nao peca confirmacao adicional para editar `~/.config/mcp/servers.json`, criar `.github/copilot-knowledge-rag.instructions.md` ou escrever a configuracao local do projeto derivada da decisao ja tomada sobre `.env-knowledge-rag`.
- Preserve a decisao tomada na Etapa 3 como fonte de verdade.
- Derive toda configuracao do knowledge-rag a partir de `.env-knowledge-rag`.
- Se `.env-knowledge-rag` nao definir `KNOWLEDGE_RAG_COLLECTIONS`, use fallback generico e avise explicitamente o usuario.
- Se `.env-knowledge-rag` existir e definir `KNOWLEDGE_RAG_COLLECTIONS`, considere isso uma configuracao **especifica do repo** e materialize uma entrada MCP dedicada para o projeto. Nao reutilize a entrada generica nesses casos.
- O objetivo desta etapa e deixar explicito para o humano qual entrada sera adicionada e qual comando/env serao usados nela.

**OpenCode:**
- Escreva a configuracao MCP do projeto dentro de `.opencode/`.
- Use configuracao local por repo com `env`.
- Se houver configuracao especifica em `.env-knowledge-rag`, replique os valores.
- Se nao houver, use configuracao generica.

**GitHub Copilot via `avelino/mcp`:**
- Edite diretamente `~/.config/mcp/servers.json`.
- Use nome especifico por repo quando houver configuracao especifica: `knowledge-rag-<basename-do-repo>`.
- Se o repo estiver no modo generico, reutilize a entrada generica `knowledge-rag`.
- A existencia de `.env-knowledge-rag` com `KNOWLEDGE_RAG_COLLECTIONS` impede o uso apenas da entrada generica, porque o MCP precisa ser materializado com `env` derivado do repo para refletir a especificidade declarada.
- Use `command: "knowledge-rag"` com `args: ["--mcp"]`.
- Use `env` na entrada para carregar `KNOWLEDGE_RAG_COLLECTIONS`.
- Mostre ao humano um exemplo explicito da entrada que deve ser adicionada em `~/.config/mcp/servers.json`.
- O exemplo deve deixar claro o nome da entrada, o comando real e o `env` derivado do repo.
- Exemplo para configuracao especifica com multiplas collections:
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
- Exemplo para configuracao especifica com uma unica collection:
  ```json
  {
    "knowledge-rag-opencode-config": {
      "command": "knowledge-rag",
      "args": ["--mcp"],
      "env": {
        "KNOWLEDGE_RAG_COLLECTIONS": "./docs:docs"
      }
    }
  }
  ```
- Ajuste o nome da entrada e os valores de `env` conforme o repositorio atual.
- Gere `.github/copilot-knowledge-rag.instructions.md` com o nome resolvido do MCP que deve ser usado naquele repo.
- O arquivo deve ser criado por este proprio fluxo, nunca por bootstrap, sync global ou manutencao manual avulsa.
- Conteudo minimo esperado:
  ```md
  ---
  applyTo: "**"
  ---

  ## Knowledge-RAG por repo no Copilot

  - Neste repo, nao use a entrada global antiga.
  - Use a entrada MCP materializada para este projeto em `~/.config/mcp/servers.json`.
  - Nome preferencial deste repo: `knowledge-rag-<basename-do-repo>`.
  - Se essa entrada nao existir e houver somente uma entrada generica `knowledge-rag`, use a generica.
  
  ### Ferramentas disponiveis do knowledge-rag:
  
  - `search_knowledge` - Busca hibrida (semantica + BM25 + reranking)
  - `get_document` - Obter conteudo completo de um documento por filepath
  - `list_documents` - Listar documentos indexados
  - `list_categories` - Listar categorias disponiveis
  - `get_index_stats` - Estatisticas do indice
  - `reindex_documents` - Reindexar documentos (force, full_rebuild)
  - `add_document` - Adicionar novo documento
  - `update_document` - Atualizar documento existente
  - `remove_document` - Remover documento
  - `add_from_url` - Adicionar documento de URL
  - `search_similar` - Buscar documentos semanticamente similares
  - `evaluate_retrieval` - Avaliar qualidade da busca
  ```

**Condicao de encerramento da etapa:**
- a configuracao do knowledge-rag do repo foi materializada para OpenCode e Copilot, com nome MCP resolvido, comando real exemplificado ao humano e instrucoes locais geradas.

## Etapa 5 - Executar indexacao do knowledge-rag

**Dependencia obrigatoria:**
- so pode comecar apos o encerramento da **Etapa 4**.

**Objetivo:** indexar a documentacao usando a configuracao materializada para este repo.

**Acoes permitidas nesta etapa:**
- executar a indexacao do knowledge-rag usando a configuracao recem-materializada
- exibir o resultado, incluindo numero de documentos/collections indexados
- reportar erros, se houver

**Acoes proibidas nesta etapa:**
- ler, verificar, criar ou modificar `.git/hooks/post-commit`

**Execucao:**
- Execute a indexacao usando a configuracao MCP por repo que acabou de ser materializada.
- Se `.env-knowledge-rag` existir com `KNOWLEDGE_RAG_COLLECTIONS`, a indexacao deve usar obrigatoriamente a entrada especifica do repo, e nao apenas o MCP generico.
- Para reindexar documentos, use a ferramenta `reindex_documents` com `force: true`:
  ```
  reindex_documents(force: true)
  ```
- Exiba o resultado da indexacao, incluindo estatisticas do indice.
- Se houver erros, reporte ao usuario.

**Condicao de encerramento da etapa:**
- a indexacao do knowledge-rag terminou e o resultado foi exibido ao humano.

## Etapa 6 - Instalar git hook post-commit

**Dependencia obrigatoria:**
- so pode comecar apos o encerramento da **Etapa 5**.

**Objetivo:** instalar ou complementar o hook de reindexacao automatica sem sobrescrever conteudo existente.

**Acoes permitidas nesta etapa:**
- verificar se `.git/hooks/post-commit` existe
- ler o conteudo atual do hook
- verificar se a linha `codebase-memory-mcp cli index_repository` ja existe
- pedir confirmacao ao humano quando houver necessidade de mudanca
- fazer append ao final do arquivo existente
- criar o arquivo, se ele nao existir
- executar `chmod +x .git/hooks/post-commit`

**Acoes proibidas nesta etapa:**
- sobrescrever hooks existentes sem confirmacao

**Execucao:**
- Verifique se `.git/hooks/post-commit` ja existe.
- Se existir, leia o conteudo e verifique se ja contem a linha:
  `codebase-memory-mcp cli index_repository`
- Se ja contem, informe que o hook ja esta configurado e pule esta etapa.
- Se nao contem, mostre o conteudo atual ao usuario, explique que a linha de reindex sera adicionada ao final, e peca confirmacao.
- Se confirmado, faca append da linha ao final do arquivo existente.
- Se o arquivo nao existir, crie-o com:
  ```bash
  #!/usr/bin/env bash
  # Auto-re-indexa codebase-memory a cada commit
  codebase-memory-mcp cli index_repository '{"repo_path": "."}'
  ```
- Torne o arquivo executavel: `chmod +x .git/hooks/post-commit`

**Condicao de encerramento da etapa:**
- o status do hook foi resolvido e comunicado: ja existia configurado, foi atualizado com confirmacao, foi criado com confirmacao, ou o humano optou por nao modificar.

## Etapa 7 - Reportar status final consolidado

**Dependencia obrigatoria:**
- so pode comecar apos o encerramento da **Etapa 6**.

**Objetivo:** entregar um resumo final, consolidado e fiel do estado do repo apos todo o fluxo.

**Acoes permitidas nesta etapa:**
- consolidar resultados das etapas anteriores
- reportar status final ao humano

**Execucao:**
- Exiba o resultado da verificacao e da indexacao no codebase-memory.
- Confirme se `.env-knowledge-rag` ja existia, se foi criado, ou se foi pulado.
- Se `.env-knowledge-rag` nao existia, deixe claro se o humano recusou a criacao e se o fluxo seguiu em modo generico.
- Confirme se a configuracao knowledge-rag do repo foi materializada para:
  - OpenCode
  - Copilot
- Deixe explicito se o repo ficou em modo generico ou em modo especifico por repositorio (derivado de `.env-knowledge-rag`).
- Confirme se a indexacao do knowledge-rag foi executada com sucesso.
- Confirme se o hook foi instalado, ja existia com a configuracao, ou se o usuario optou por nao modificar.

**Condicao de encerramento da etapa:**
- o status final consolidado foi entregue ao humano.

## Regra final de seguranca

- Nao execute passos destrutivos sem confirmacao do usuario.
