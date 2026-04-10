# Regras Globais

## Idioma
- PT-BR (ASCII ok).
- REGRA IMPORTANTE: sempre use acentuação quando estiver escrevendo texto em PT-BR.

### Atalho: "configure este repo"

- Se o humano pedir explicitamente "configure este repo" (ou equivalente), isso conta como confirmacao para executar o bootstrap.
- Comando canonico:

```bash
bash ./scripts/bootstrap_repo/opencode-link --yes
```
- Se a configuracao exigir pacotes com `sudo`, primeiro entregue ao humano os comandos prontos para copia e cola em um bloco unico.
- Aguarde a execucao desses comandos pelo humano antes de seguir com a configuracao do repo.

## Configuracao Global via Links Simbolicos

- Este repo `opencode-config` e o fonte de verdade das configs globais do OpenCode.
- Para o OpenCode enxergar estes arquivos de forma global, usamos links simbolicos a partir de `~/.config/opencode`.

Padrao de links (exemplo neste ambiente WSL):

```bash
mkdir -p ~/.config/opencode

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

## Concisao
- Responda de forma curta por padrao.
- Detalhe apenas quando o humano pedir explicitamente ou quando houver risco de ambiguidade/erro.
- Prefira listas curtas a textos longos.
- Textos de resposta com mais de 20 linhas são supeitos. Humanos não gostam de ler muita coisa, então respostas muito
  longas não são eficientes e deixam de ser lidas
- Não escreva texto explicativo com mais que 30 linhas, a não ser que fique muito clara a importância dele ou se o humano
- pedir explicitamente.
- Ao invés de dar uma resposta muito longa, resuma em até 20 ~30 linhas (no máximo) e pergunte se o humano quer se
- aprofundar mais em algum outro detalhe ou mesmo que dê uma explicação bem mais detalhada.
- Você pode criar mais linhas desde que a resposta estreja estruturada mais em bullets e seja menos densa, de modo que
- a densidade normal de palavras em 20~30 linhas também não seja ultrapassada

# Geração de arquivos MD
- Nunca ultrapasse mais de 120 colunas, de texto, faça word-wrap para garantir essa regra

# Exibição de Texto copie e cola
- Sempre que for exibir um texto cuja inteção é permitir que ao usuário copiar e colar, faça isso em um bloco de código 
único para facilitar a cópia.

## Acao
- Nao execute mudancas (edicao de arquivos, comandos destrutivos) sem confirmacao explicita do humano.
- Perguntas do humano nao sao ordens de execucao; responda a pergunta e aguarde instrucao explicita para agir.

## COMMITS

- Proponha mensagens de commit sempre que o humano pedir
- Descubra a linguagem definida pelo contexto do Projeto, mas use PT-BR por padrão caso não encontre.
- O humano sempre que validar tudo antes do commit, então **não** realize o commit antes do humano validar e dar ok.
- Mostre a mensagem de commit, mas SEMPRE espere confirmação do humano para realizar o commit
- NUNCA realize o commit independentemente.
- SEMPRE pergunte ao humano antes de realizar o commit.
- SÓ realize o commit quando o humano autorizar

# Criação de Skills
- Ao criar novas skills, para serem acionadas corretamente, as descrições das skills precisam possuir todas as 
instruções de ativação, deixar uma ativação no corpo da skill não a faz ser ativada.
- Ao criar novas skills, **não descreva** formas de ativação da skill em seu corpo sem que isso tenha sido descrito 
nas descrições

# Regras Obrigatórias Pora Testes
- Toda evolução funcional do repo deve criar ou atualizar testes automatizados.
- Aplica-se a: novos scripts, skills, comandos, agentes e mudanças no bootstrap.
- Framework: BATS-core em `tests/` — rodar com `make test`.
- A estrutura de testes deve espelhar a estrutura do código.
- Se um teste cobre um script, ele deve ter o mesmo nome do script com sufixo `_test`.
- Não criar testes para scripts cuja única função é executar ou orquestrar testes.
- Scripts de bootstrap devem ficar em `scripts/bootstrap_repo/`.
- Novos scripts desse tipo também devem entrar em `scripts/bootstrap_repo/`.
- Os testes desses scripts devem espelhar isso em `tests/scripts/bootstrap_repo/`.

# README
- Mantenha a seção de dependências do `README.md` atualizada sempre que mudar bootstrap, scripts, skills ou requisitos de instalação.
- A seção deve ser enxuta e voltada ao humano: listar claramente o que é instalado automaticamente e quais comandos com `sudo` o humano precisa executar.

# Upstream de Skills Externas
- Skills baseadas em repositórios externos devem seguir o padrão de upstream do repo:
  - Criar `UPSTREAM.md` na pasta da skill com a origem e instruções de sync.
  - Registrar a skill em `skills/list-updatable` para permitir atualização futura.
  - Usar `skills/update-upstream-skill` para sincronizar.
