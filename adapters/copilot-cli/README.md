# Adapter Copilot CLI

Este adapter transforma a fonte canônica deste repositório para os formatos e
diretórios usados pelo Copilot CLI.

## Uso

Execute após instalar o pacote editável:

```text
opencode-copilot-adapter --yes
```

O mesmo comando funciona em Linux, WSL e Windows.

O adapter sincroniza agentes, skills, comandos convertidos e artefatos
auxiliares para `~/.copilot/`. O bootstrap principal também executa este
adapter automaticamente. Para evitar sua execução, use
`OPENCODE_SKIP_COPILOT_ADAPTER=1`.
