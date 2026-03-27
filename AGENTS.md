# Regras Globais

## Idioma
- PT-BR (ASCII ok).

## Concisao
- Responda de forma curta por padrao.
- Detalhe apenas quando o humano pedir explicitamente ou quando houver risco de ambiguidade/erro.
- Prefira listas curtas a textos longos.
- Textos de resposta com mais de 20 linhas são supeitos. Humanos não gostam de ler muita coisa, então respostas muito longas não são eficientes e deixam de ser lidas
- Não escreva texto explicativo com mais que 30 linhas, a não ser que fique muito clara a importância dele ou se o humano pedir explicitamente.
- Ao invés de dar uma resposta muito longa, resuma em até 20 ~30 linhas (no máximo) e pergunte se o humano quer se aprofundar mais em algum outro detalhe ou mesmo que dê uma explicação bem mais detalhada.
- Você pode criar mais linhas desde que a resposta estreja estruturada mais em bullets e seja menos densa, de modo que a densidade normal de palavras em  20~30 linhas também não seja ultrapassada   

## Acao
- Nao execute mudancas (edicao de arquivos, comandos destrutivos) sem confirmacao explicita do humano.
- Perguntas do humano nao sao ordens de execucao; responda a pergunta e aguarde instrucao explicita para agir.

### Atalho: "configure este repo"

- Se o humano pedir explicitamente "configure este repo" (ou equivalente), isso conta como confirmacao para executar o bootstrap.
- Comando canonico:

```bash
bash ./scripts/opencode-link --yes
```

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

ln -s /mnt/c/Users/<usr>/Projetos/opencode-config/commands \
      ~/.config/opencode/commands

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

## COMMITS

- Proponha mensagens de commit sempre que o humano pedir
- Descubra a linguagem definida pelo contexto do Projeto, mas use PT-BR por padrão caso não encontre. 
- NUNCA realize o commit independentemente.
- SEMPRE pergunte ao humano antes de realizar o commit.
- SÓ realize o commit quando o humano autorizar
  
## MCPs
