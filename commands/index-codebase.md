---
description: Indexa o repositorio no codebase-memory, configura doctree e instala git hook post-commit
---

Indexe o repositorio atual no codebase-memory e configure o doctree.

Siga este fluxo estritamente:

1. **Indexar repo no codebase-memory**:
   Execute: `codebase-memory-mcp cli index_repository '{"repo_path": "."}'`
   Exiba o resultado da indexacao.

2. **Configurar doctree**:
   - Verifique se a pasta `docs/` existe na raiz do repo.
   - Se existir, configure `DOCS_ROOT=./docs` e indexe com doctree.
   - Se nao existir, avise o usuario e pule esta etapa.

 3. **Instalar git hook post-commit (append, nunca sobrescrever)**:
    - Verifique se `.git/hooks/post-commit` ja existe.
    - Se existir, leia o conteudo e verifique se ja contem a linha:
      `codebase-memory-mcp cli index_repository`
    - Se ja contem, informe que o hook ja esta configurado e pule esta etapa.
    - Se nao contem, mostre o conteudo atual ao usuario, explique que a linha
      de reindex sera adicionada ao final, e peca confirmacao.
    - Se confirmado, faça append da linha ao final do arquivo existente.
    - Se o arquivo nao existir, crie-o com:
      ```bash
      #!/usr/bin/env bash
      # Auto-re-indexa codebase-memory a cada commit
      codebase-memory-mcp cli index_repository '{"repo_path": "."}'
      ```
    - Torne o arquivo executavel: `chmod +x .git/hooks/post-commit`

 4. **Reportar status**:
    - Exiba o resultado da indexacao no codebase-memory.
    - Confirme se doctree foi configurado ou se foi pulado.
    - Confirme se o hook foi instalado, ja existia com a configuracao, ou se o
      usuario optou por nao modificar.

Nao execute passos destrutivos sem confirmacao do usuario.
