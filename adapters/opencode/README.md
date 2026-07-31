# Adapter OpenCode

Este adapter configura o OpenCode usando links simbólicos para a fonte
canônica deste repositório.

## Uso

Execute a partir da raiz do repositório:

```bash
./adapters/opencode/opencode-adapter.sh --yes
```

O adapter cria ou atualiza links em `~/.config/opencode/` para os agentes,
comandos, skills, scripts e `opencode.json` deste repositório.

O bootstrap principal também executa este adapter automaticamente. Para
evitar sua execução, use `OPENCODE_SKIP_OPENCODE_ADAPTER=1`.
