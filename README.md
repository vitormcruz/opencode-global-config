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

Se ja existir algo em `~/.config/opencode`, o script pode perguntar se voce quer importar as diferencas para dentro deste repo antes de criar os links (para nao perder customizacoes locais e conseguir versionar depois).

Modo nao-interativo (bom para automatizar):

```bash
./scripts/opencode-link --yes
```

## Bootstrap (OpenCode / agente)

Quando o usuario pedir algo como "configure este repo", o comando canonico é:

```bash
bash ./scripts/opencode-link --yes
```
