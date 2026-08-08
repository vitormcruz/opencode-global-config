# Bootstrap

Os entrypoints finos configuram as plataformas e dependências deste
repositório. Ambos delegam a mesma lógica ao pacote Python.

## Linux e WSL

```bash
./scripts/bootstrap_repo/configurar-repo.sh --yes
```

O entrypoint verifica Python >= 3.10, executa a detecção e seleção interativa e
configura o adapter OpenCode.

## Windows

Execute no PowerShell:

```powershell
.\scripts\bootstrap_repo\configurar-repo.ps1 --yes
```

O entrypoint verifica Python >= 3.10 e configura somente o adapter Copilot CLI.
Ele não cria links em `~/.config/opencode`.

## Opções

Use `--yes` para instalar tudo que estiver ausente, `--quiet` para suprimir a
tabela de detecção ou `--check-only` para apenas exibir o diagnóstico. O
bootstrap não usa `sudo` nem exige privilégios de administrador.
