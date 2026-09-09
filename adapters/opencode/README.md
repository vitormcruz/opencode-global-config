# Adapter OpenCode

Este adapter configura o OpenCode a partir da fonte canônica deste
repositório, no formato do sistema corrente.

## Uso

Execute após instalar o pacote editável:

```bash
opencode-adapter --yes
```

No Linux/WSL, o adapter cria ou atualiza links em `~/.config/opencode/`
para os agentes, comandos, skills e `opencode.json` de `harness-conf/`
(e para `scripts/`, que fica na raiz do repo) deste repositório, e
garante as env vars no `~/.bashrc`.

No Windows, o adapter materializa cópia sincronizada dos quatro destinos
de `harness-conf/` em `%USERPROFILE%\.config\opencode` a cada execução e
persiste `OPENCODE_ENABLE_EXA` em `HKCU\Environment` com broadcast de
`WM_SETTINGCHANGE` (novos processos, sem logoff).

O bootstrap principal também executa este adapter automaticamente. Para
evitar sua execução, use `OPENCODE_SKIP_OPENCODE_ADAPTER=1`.

O adapter não altera os arquivos do repositório. Para sincronizar skills
upstream, execute separadamente `opencode-skills sync NOME`.
