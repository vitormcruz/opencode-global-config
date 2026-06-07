---
description: Indexa o repositorio no codebase-memory, configura doctree e instala git hook post-commit
---

Indexe o repositorio atual no codebase-memory e configure o doctree.

Siga este fluxo estritamente:

1. **Indexar repo no codebase-memory**:
   Execute: `codebase-memory-mcp cli index_repository '{"repo_path": "."}'`
   Exiba o resultado da indexacao.

2. **Configurar doctree (.env-doctree)**:
   - Verifique se o arquivo `.env-doctree` ja existe na raiz do repo.
   - Se ja existir, exiba o conteudo e pule a criacao.
   - Se nao existir, liste as pastas detectadas na raiz e pergunte:
     "Quais pastas indexar no doctree? [docs/agents/skills/plan — padrao: todas]"
   - Crie `.env-doctree` com as pastas escolhidas (ou todas se o usuario
     aceitar o padrao). Formato:
     ```bash
     DOCS_ROOTS="./docs:1.0,./agents:0.9,./skills:0.7,./plan:0.5"
     ```
   - Explique: o wrapper `opencode-doctree-run` usa este arquivo. Para aplicar,
     reinicie o doctree (reinicie o OpenCode ou `mcp doctree`).
   - Se o usuario recusar todas as pastas, informe que o doctree usara
     fallback `./docs`.

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
     - Confirme se `.env-doctree` foi criado, se ja existia, ou se foi pulado.
     - Confirme se o hook foi instalado, ja existia com a configuracao, ou se o
       usuario optou por nao modificar.

Nao execute passos destrutivos sem confirmacao do usuario.
