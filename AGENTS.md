# Regras Globais

## Idioma
- PT-BR (ASCII ok).

## Concisao
- Responda de forma curta por padrao.
- Detalhe apenas quando o humano pedir explicitamente ou quando houver risco de ambiguidade/erro.
- Prefira listas curtas a textos longos.

## Acao
- Nao execute mudancas (edicao de arquivos, comandos destrutivos) sem confirmacao explicita do humano.
- Perguntas do humano nao sao ordens de execucao; responda a pergunta e aguarde instrucao explicita para agir.

## Configuracao Global via Links Simbolicos

- Este repo `opencode-config` e o fonte de verdade das configs globais do OpenCode.
- Para o OpenCode enxergar estes arquivos de forma global, usamos links simbolicos a partir de `~/.config/opencode`.

Padrao de links (exemplo neste ambiente WSL):

```bash
mkdir -p ~/.config/opencode

ln -s /mnt/c/Users/ur5y/Projetos/opencode-config/AGENTS.md \
      ~/.config/opencode/AGENTS.md

ln -s /mnt/c/Users/ur5y/Projetos/opencode-config/agents \
      ~/.config/opencode/agents

ln -s /mnt/c/Users/ur5y/Projetos/opencode-config/opencode.json \
      ~/.config/opencode/opencode.json

ln -s /mnt/c/Users/ur5y/Projetos/opencode-config/skills \
      ~/.config/opencode/skills

ln -s /mnt/c/Users/ur5y/Projetos/opencode-config/scripts \
      ~/.config/opencode/scripts
```

- Assim voce mantem estas configs versionadas em um repo Git separado (`opencode-config`), mas o OpenCode continua lendo tudo a partir de `~/.config/opencode`.

## Skills disponiveis

### mermaid-to-image
Converte blocos Mermaid em imagens PNG. Para usar:
1. Passe o texto com o bloco ```mermaid``` via stdin para `~/.config/opencode/scripts/opencode-mermaidtoimage`.
2. Receba JSON com `imagePath` e `markdown` prontos para exibir ao usuario.

Requisito: `mmdc` instalado (`npm install -g @mermaid-js/mermaid-cli`).
