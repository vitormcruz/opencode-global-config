---
description: Indexa o repositorio no codebase-memory, configura doctree e instala git hook post-commit
---

Indexe o repositorio atual no codebase-memory e configure o doctree.

Siga este fluxo estritamente:

1. **Verificar se o projeto ja esta indexado no codebase-memory**:
   - No **GitHub Copilot**, execute: `mcp codebase-memory list_projects`
   - No **OpenCode**, use o fluxo nativo equivalente para listar projetos.
   - Se o repositorio atual ja estiver indexado, informe isso ao usuario antes
     de reindexar.

2. **Indexar repo no codebase-memory**:
   - No **GitHub Copilot**, execute: `mcp codebase-memory index_repository --repo_path "."`
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

4. **Executar indexacao do doctree**:
   - Execute obrigatoriamente o script `scripts/doctree/doctree-run.sh` para
     indexar os documentos no doctree-mcp.
   - Na raiz do repo, execute:
     ```bash
     bash scripts/doctree/doctree-run.sh
     ```
   - Este script faz source de `.env-doctree` e indexa todas as pastas
     configuradas.
   - Exiba o resultado da indexacao (numero de documentos indexados).
   - Se houver erros, reporte ao usuario.

5. **Instalar git hook post-commit (append, nunca sobrescrever)**:
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

6. **Reportar status**:
   - Exiba o resultado da verificacao e da indexacao no codebase-memory.
   - Confirme se `.env-doctree` ja existia, se foi criado, ou se foi pulado.
   - Confirme se a indexacao do doctree foi executada com sucesso.
   - Confirme se o hook foi instalado, ja existia com a configuracao, ou se o
     usuario optou por nao modificar.

Nao execute passos destrutivos sem confirmacao do usuario.
