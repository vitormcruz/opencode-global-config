# Adapter Copilot CLI

Este adapter transforma a fonte canônica deste repositório para os formatos e
diretórios usados pelo Copilot CLI.

## Uso

No WSL ou Linux, execute:

```bash
./adapters/copilot-cli/copilot-cli-adapter.sh --yes
```

No Windows, execute a versão PowerShell:

```powershell
.\adapters\copilot-cli\copilot-cli-adapter.ps1 -Yes
```

O adapter sincroniza agentes, skills, comandos convertidos e artefatos
auxiliares para `~/.copilot/`. O bootstrap principal também executa este
adapter automaticamente. Para evitar sua execução, use
`OPENCODE_SKIP_COPILOT_ADAPTER=1`.
