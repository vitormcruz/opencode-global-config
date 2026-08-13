# Adapter OpenCode

Este adapter configura o OpenCode usando links simbólicos para a fonte
canônica deste repositório.

## Uso

Execute após instalar o pacote editável:

```bash
opencode-adapter --yes
```

O adapter cria ou atualiza links em `~/.config/opencode/` para os agentes,
comandos, skills, scripts e `opencode.json` deste repositório.

O adapter funciona em Linux e WSL. No Windows, use o adapter do Copilot.

O bootstrap principal também executa este adapter automaticamente. Para
evitar sua execução, use `OPENCODE_SKIP_OPENCODE_ADAPTER=1`.

O adapter não altera os arquivos do repositório. Para sincronizar skills
upstream, execute separadamente `opencode-skills sync NOME`.
