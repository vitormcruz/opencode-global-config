# Bootstrap

Os entrypoints finos configuram as plataformas e dependências deste
repositório. Ambos delegam a mesma lógica ao pacote Python.

O bootstrap detecta o SO corrente e configura todos os harnesses
instalados (OpenCode e Copilot CLI); harness ausente no PATH é ignorado
com aviso. A flag `--harness a,b` restringe a subconjunto.

## Linux e WSL

```bash
./scripts/bootstrap_repo/configurar-repo.sh --yes
```

O entrypoint verifica Python >= 3.10, executa a detecção e seleção
interativa, instala as dependências em user-space e configura os
harnesses instalados: OpenCode com links em `~/.config/opencode` e
Copilot CLI com cópia sincronizada em `~/.copilot`.

## Windows

Execute no PowerShell:

```powershell
.\scripts\bootstrap_repo\configurar-repo.ps1 --yes
```

O entrypoint verifica Python >= 3.10 e configura os harnesses
instalados: OpenCode com cópia sincronizada em
`%USERPROFILE%\.config\opencode` e Copilot CLI com cópia sincronizada
em `%USERPROFILE%\.copilot`.

## Opções

Use `--yes` para instalar tudo que estiver ausente, `--quiet` para
suprimir a tabela de detecção, `--check-only` para apenas exibir o
diagnóstico ou `--harness a,b` para configurar apenas os harnesses
listados. O bootstrap não usa `sudo` nem exige privilégios de
administrador.
