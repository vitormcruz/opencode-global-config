# Bootstrap

`configurar-repo.sh` é o ponto de entrada para configurar as plataformas e
dependências deste repositório.

## Uso

```bash
./scripts/bootstrap_repo/configurar-repo.sh --yes
```

O script executa, nesta ordem:

1. Instala dependências com `wsl-install-deps.sh`.
2. Executa `opencode-copilot-adapter` via o módulo Python do repositório.
3. Executa `opencode-adapter` via o módulo Python do repositório.
4. Configura as ferramentas CLI globais.

Use `OPENCODE_SKIP_DEPS=1`, `OPENCODE_SKIP_COPILOT_ADAPTER=1`,
`OPENCODE_SKIP_OPENCODE_ADAPTER=1` ou `OPENCODE_SKIP_CODEBASE_MEMORY=1`
para pular etapas específicas.
