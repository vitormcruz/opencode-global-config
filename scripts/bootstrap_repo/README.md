# Bootstrap

`configurar-repo.sh` é o ponto de entrada para configurar as plataformas e
dependências deste repositório.

## Uso

```bash
./scripts/bootstrap_repo/configurar-repo.sh --yes
```

O entrypoint fino verifica Python 3.10+ e delega para
`opencode_config.bootstrap.main`. O módulo detecta dependencias, executa a
selecao interativa e configura o adapter pertinente ao sistema operacional.

Use `--yes`, `--quiet` ou `--check-only`.
