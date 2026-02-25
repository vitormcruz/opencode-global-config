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

ln -s /mnt/c/Users/<usr>/Projetos/opencode-config/AGENTS.md \
      ~/.config/opencode/AGENTS.md

ln -s /mnt/c/Users/<usr>/Projetos/opencode-config/agents \
      ~/.config/opencode/agents

ln -s /mnt/c/Users/<usr>/Projetos/opencode-config/opencode.json \
      ~/.config/opencode/opencode.json

ln -s /mnt/c/Users/<usr>/Projetos/opencode-config/skills \
      ~/.config/opencode/skills

ln -s /mnt/c/Users/<usr>/Projetos/opencode-config/scripts \
      ~/.config/opencode/scripts
```

- Assim voce mantem estas configs versionadas em um repo Git separado (`opencode-config`), mas o OpenCode continua lendo tudo a partir de `~/.config/opencode`.

## Imagens e diagramas

- Quando o humano pedir para criar, visualizar ou converter imagens, diagramas, fluxogramas ou similares:
  - Se o pedido envolver SVG (fornecido pelo humano ou gerado pelo agente):
    - Envie o SVG completo via stdin para a skill `svg-to-image` (`~/.config/opencode/scripts/opencode-svgtoimage`).
    - Leia o JSON de resposta.
    - Use o campo `markdown` diretamente na resposta ao humano para exibir a imagem.
  - Nao tente converter SVG em PNG manualmente; sempre prefira a skill `svg-to-image`.

## Skills disponiveis

- svg-to-image
  - Converte um SVG recebido via stdin em PNG salvo em `/tmp`.
  - Implementacao: script `~/.config/opencode/scripts/opencode-svgtoimage`.
  - Saida: JSON com `imagePath` (caminho do PNG) e `markdown` (`![](<caminho_png>)`).
  - Agentes devem usar esta skill sempre que o humano pedir para criar ou converter imagens/diagramas baseados em SVG.
