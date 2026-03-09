# opencode-config

Repo com as configuracoes globais do OpenCode para este usuario/maquina.

## Como funciona

- O OpenCode le configuracoes globais a partir de `~/.config/opencode`.
- Este repo fica em outro lugar (ex.: `/mnt/c/Users/<usr>/Projetos/opencode-config`) e e conectado por links simbolicos.

Links usados neste ambiente WSL:

```bash
mkdir -p ~/.config/opencode

ln -s /mnt/c/Users/<usr>/Projetos/opencode-config/AGENTS.md \
      ~/.config/opencode/AGENTS.md

ln -s /mnt/c/Users/<usr>/Projetos/opencode-config/agents \
      ~/.config/opencode/agents

ln -s /mnt/c/Users/<usr>/Projetos/opencode-config/opencode.json \
      ~/.config/opencode/opencode.json
```

## Bootstrap (usuario)

Depois de clonar este repo em qualquer caminho, rode:

```bash
./scripts/opencode-link
```
