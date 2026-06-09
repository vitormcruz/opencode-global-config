---
description: Indexa o repositorio no codebase-memory, configura doctree por repo e instala git hook post-commit
---

Indexe o repositorio atual no codebase-memory e configure o doctree.

Siga este fluxo estritamente:

1. **Verificar se o projeto ja esta indexado no codebase-memory**:
   - No **GitHub Copilot**, execute: `mcp codebase-memory list_projects`
   - No **OpenCode**, use o fluxo nativo equivalente para listar projetos.
   - Se o repositorio atual ja estiver indexado, informe isso ao usuario antes
     de reindexar.

2. **Indexar repo no codebase-memory**:
   - No **GitHub Copilot**, execute com JSON posicional unico e `repo_path`
     absoluto, por exemplo:
     `mcp codebase-memory index_repository '{"repo_path":"/mnt/c/Users/ur5y/Projetos/opencode-config"}'`
   - Nao use `--repo_path "."` no Copilot, pois essa sintaxe falha com o
     wrapper `mcp` neste ambiente.
   - No **OpenCode** ou em hooks/scripts locais, use:
     `codebase-memory-mcp cli index_repository '{"repo_path": "."}'
   - Exiba o resultado da indexacao.

3. **Configurar doctree (.env-doctree)**:
   - Verifique se o arquivo `.env-doctree` ja existe na raiz do repo.
   - Se ja existir, exiba o conteudo, trate-o como fonte de verdade do repo e
     pule a criacao. Nao tente migrar automaticamente entre `DOCS_ROOT` e
     `DOCS_ROOTS`, nem sobrescrever o arquivo sem confirmacao do usuario.
   - Se nao existir, liste as pastas detectadas na raiz e pergunte:
     "Quais pastas indexar no doctree? [docs/agents/skills/plan — padrao: docs]"
   - Se o usuario escolher **uma pasta**, crie `.env-doctree` com:
     ```bash
     DOCS_ROOT="./docs"
     ```
     Ajuste o caminho conforme a pasta escolhida.
   - Se o usuario quiser **multiplas pastas**, crie `.env-doctree` com:
     ```bash
     DOCS_ROOTS="./docs:1.0,./agents:0.9,./skills:0.7,./plan:0.5"
     ```
     Ajuste as pastas e pesos conforme escolha do usuario.

4. **Configurar doctree por repo**:
   - Preserve a decisao tomada no passo 3 como fonte de verdade.
   - Derive toda configuracao de Doctree a partir de `.env-doctree`.
   - Se `.env-doctree` nao definir `DOCS_ROOT` nem `DOCS_ROOTS`, use fallback
     generico para `./docs` e avise explicitamente o usuario.

   **OpenCode**:
   - Escreva a configuracao MCP do projeto dentro de `.opencode/`.
   - Use configuracao local por repo com `env`.
   - Se houver configuracao especifica em `.env-doctree`, replique os valores.
   - Se nao houver, use configuracao generica apontando para `./docs`.

   **GitHub Copilot via `avelino/mcp`**:
   - Edite diretamente `~/.config/mcp/servers.json`.
   - Use nome especifico por repo quando houver configuracao especifica:
     `doctree-mcp-<basename-do-repo>`.
   - Se o repo estiver no modo generico `./docs`, reutilize a entrada
     generica `doctree-mcp`.
   - Use `env` na entrada para carregar `DOCS_ROOT` ou `DOCS_ROOTS`.
   - Gere `.github/copilot-doctree.instructions.md` com o nome resolvido do MCP
     que deve ser usado naquele repo.
   - O arquivo deve ser criado por este proprio fluxo, nunca por bootstrap,
     sync global ou manutencao manual avulsa.
   - Conteudo minimo esperado:
     ```md
     ---
     applyTo: "**"
     ---

     ## Doctree por repo no Copilot

     - Neste repo, nao use a entrada global antiga `doctree`.
     - Use a entrada MCP materializada para este projeto em `~/.config/mcp/servers.json`.
     - Nome preferencial deste repo: `doctree-mcp-<basename-do-repo>`.
     - Se essa entrada nao existir e houver somente uma entrada generica `doctree-mcp`, use a generica.
     ```

5. **Executar indexacao do doctree**:
   - Execute a indexacao usando a configuracao MCP por repo que acabou de ser
     materializada.
   - Nao use mais `scripts/doctree/doctree-run.sh`.
   - Exiba o resultado da indexacao, incluindo numero de documentos indexados.
   - Se houver erros, reporte ao usuario.

6. **Instalar git hook post-commit (append, nunca sobrescrever)**:
   - Verifique se `.git/hooks/post-commit` ja existe.
   - Se existir, leia o conteudo e verifique se ja contem a linha:
     `codebase-memory-mcp cli index_repository`
   - Se ja contem, informe que o hook ja esta configurado e pule esta etapa.
   - Se nao contem, mostre o conteudo atual ao usuario, explique que a linha
     de reindex sera adicionada ao final, e peca confirmacao.
   - Se confirmado, faca append da linha ao final do arquivo existente.
   - Se o arquivo nao existir, crie-o com:
     ```bash
     #!/usr/bin/env bash
     # Auto-re-indexa codebase-memory a cada commit
     codebase-memory-mcp cli index_repository '{"repo_path": "."}'
     ```
   - Torne o arquivo executavel: `chmod +x .git/hooks/post-commit`

7. **Reportar status**:
   - Exiba o resultado da verificacao e da indexacao no codebase-memory.
   - Confirme se `.env-doctree` ja existia, se foi criado, ou se foi pulado.
   - Confirme se a configuracao Doctree do repo foi materializada para:
     - OpenCode
     - Copilot
   - Confirme se a indexacao do doctree foi executada com sucesso.
   - Confirme se o hook foi instalado, ja existia com a configuracao, ou se o
     usuario optou por nao modificar.

Nao execute passos destrutivos sem confirmacao do usuario.
