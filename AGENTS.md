# Regras Globais

## Descoberta de Código e Documentação (LEIA ANTES DE BUSCAR)

Use SEMPRE `codebase-memory-mcp cli` antes de grep/glob. O CLI retorna
resultados estruturados, consome menos tokens e entende a arquitetura do
projeto.

### codebase-memory CLI (CÓDIGO)

Use para funções, classes, rotas, callers, data flow, arquitetura e seções de
documentos Markdown (arquivos `.md` são indexados como nós do tipo Section).

Para buscar em documentacao, use `query_graph` com Cypher para consultar
nos do tipo `Section`:

```cypher
MATCH (s:Section) WHERE s.name CONTAINS "termo" RETURN s.name, s.file
```

Ordem:
  1. `search_graph` — encontrar funcoes, classes, rotas, variaveis, secoes de doc
  2. `trace_path` — quem chama / quem e chamado
  3. `get_code_snippet` — ler fonte de simbolo especifico
  4. `query_graph` — padroes complexos multi-entidade (Cypher), busca em docs
  5. `get_architecture` — visao geral do projeto

### grep/glob (FALLBACK — apenas quando o CLI não resolve)

  - `grep` — strings literais, mensagens de erro e valores de config
  - `glob` — arquivos por nome ou padrão

### Recovery obrigatório

Se o CLI retornar `"project not found"`:
  1. Execute `codebase-memory-mcp cli list_projects '{}'`
  2. Copie o nome exato do projeto indexado
  3. Retente a busca com o nome correto
  4. Só caia para grep/glob se o projeto não estiver indexado

### Acesso por cliente

| Cliente | Ambiente | codebase-memory |
|---|---|---|
| OpenCode | WSL | `codebase-memory-mcp cli <tool> '<json>'` |
| GitHub Copilot | Windows | `codebase-memory-mcp cli <tool> '<json>'` |

Ambos os clientes usam o CLI nativo, com JSON posicional único, `repo_path`
absoluto para indexação e `project` explícito nas consultas. Consulte
`.github/copilot-specific.instructions.md` para detalhes.

## Idioma
- PT-BR (ASCII ok).
- REGRA IMPORTANTE: sempre use acentuação quando estiver escrevendo texto em PT-BR.

### Atalho: "configure este repo"

- Se o humano pedir explicitamente "configure este repo" (ou equivalente),
  isso conta como confirmacao para executar o bootstrap.
- Comando canonico:

```bash
bash ./scripts/bootstrap_repo/configurar-repo.sh --yes
```
- Se a configuracao exigir pacotes com `sudo`, primeiro entregue ao humano os
  comandos prontos para copia e cola em um bloco unico.
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

- Assim voce mantem estas configs versionadas em um repo Git separado
  (`opencode-config`), mas o OpenCode continua lendo tudo a partir de
  `~/.config/opencode`.

## Bootstrap

Depois de clonar este repo, rode:

```bash
./scripts/bootstrap_repo/configurar-repo.sh --yes
```

O script executa quatro fases:
1. **Instala dependencias** (`scripts/bootstrap_repo/wsl-install-deps.sh`)
2. **Executa o adapter Copilot CLI** (`adapters/copilot-cli/copilot-cli-adapter.sh`)
3. **Executa o adapter OpenCode** (`adapters/opencode/opencode-adapter.sh`)
4. **Instala ferramentas globais** — `crwl` e `codebase-memory-mcp`

Cada parte pode ser pulada via variaveis de ambiente:
- `OPENCODE_SKIP_DEPS=1` — pula instalacao de dependencias
- `OPENCODE_SKIP_COPILOT_ADAPTER=1` — pula o adapter Copilot CLI
- `OPENCODE_SKIP_OPENCODE_ADAPTER=1` — pula o adapter OpenCode
- `OPENCODE_SKIP_CODEBASE_MEMORY=1` — pula configuracao do codebase-memory CLI

Para aplicar a variavel `OPENCODE_ENABLE_EXA` no shell atual:

```bash
source ~/.bashrc
```

No ambiente WSL deste repo, o script faz duas coisas:

- cria/atualiza os links simbolicos em `~/.config/opencode`
- garante `export OPENCODE_ENABLE_EXA=1` em `~/.bashrc`

Para aplicar a variavel no shell atual depois do bootstrap:

```bash
source ~/.bashrc
```

## Concisao
- Responda de forma curta por padrao.
- Detalhe apenas quando o humano pedir explicitamente ou quando houver risco de ambiguidade/erro.
- Prefira listas curtas a textos longos.
- Textos de resposta com mais de 20 linhas são supeitos. Humanos não gostam de ler muita coisa, então respostas muito
  longas não são eficientes e deixam de ser lidas
- Não escreva texto explicativo com mais que 30 linhas, a não ser que fique
  muito clara a importância dele ou se o humano
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

## SmartPlanner — Restricao Comportamental
- O agente `smart-planner` **nunca** edita codigo de aplicacao durante planejamento.
- Apenas le arquivos para entender contexto. A unica escrita permitida e o arquivo de planejamento.

## COMMITS

- Use Conventional Commits. Formato: `tipo(escopo): descricao curta`
  Tipos: feat, fix, docs, style, refactor, test, chore, ci, build, perf.
- Mensagem de commit sempre no modo caveman (skill skills/caveman):
  terse, sem filler, sem artigos, so substancia.
- Proponha mensagens de commit sempre que o humano pedir
- **Use a skill `cave-man`** para definir o formato das mensagens de commit.
- Descubra a linguagem definida pelo contexto do Projeto, mas use PT-BR por padrão caso não encontre.
- O humano sempre que validar tudo antes do commit, então **não** realize o commit antes do humano validar e dar ok.
- Mostre a mensagem de commit, mas SEMPRE espere confirmação do humano para realizar o commit
- NUNCA realize o commit independentemente.
- SEMPRE pergunte ao humano antes de realizar o commit.
- SÓ realize o commit quando o humano autorizar
- NUNCA simular rename ou move como delete + create.
- Sempre usar `git mv` para mover ou renomear arquivos versionados, preservando histórico.
- Se um arquivo versionado precisar ser movido e editado, primeiro fazer o `git mv` e só depois editar.
- Essa regra não tem exceção.

# Criação de Skills
- Ao criar novas skills, para serem acionadas corretamente, as descrições das skills precisam possuir todas as 
instruções de ativação, deixar uma ativação no corpo da skill não a faz ser ativada.
- Ao criar novas skills, **não descreva** formas de ativação da skill em seu corpo sem que isso tenha sido descrito 
nas descrições

# Sincronização Workflow ↔ Agentes
- As definições de agentes ficam em `agents/` e devem estar sempre
  sincronizadas com os workflows em `docs/workflow-agentes-dev.md`
  e `docs/workflow-curadoria.md`.
- **Ao criar ou modificar um agente em `agents/`:** leia primeiro os
  workflows e verifique se a mudança proposta está alinhada com o que
  o workflow define para aquele agente.
- **Ao alterar um workflow:** identifique quais agentes em `agents/`
  precisam ser atualizados para refletir a mudança, e liste-os ao humano.
- Toda mudança — em workflow **ou** em agentes — **sempre** passa
  pelo humano antes de ser aplicada. Sem exceção.

# Regras Obrigatórias Pora Testes
- Toda evolução funcional do repo deve criar ou atualizar testes automatizados.
- Aplica-se a: novos scripts, skills, comandos, agentes e mudanças no bootstrap.
- Framework: BATS-core em `tests/` — rodar com `make test-opencode-opencode`.
- **Execução sempre via WSL** — os testes usam Bash/BATS e devem
  ser executados dentro do WSL.
  - **Regra**: sempre use `wsl -- bash -ic "COMANDO"` para executar
    comandos no WSL a partir do PowerShell/cmd. Nunca use
    `wsl -e bash -c` — esse modo não carrega `~/.bashrc` e
    ferramentas como `node`, `fnm`, `bats` não estarão no PATH.
  - Exemplo canônico:
    `wsl -- bash -ic "cd /mnt/c/Users/<usr>/Projetos/opencode-config && make test-opencode"`
  - Se já estiver dentro do WSL (terminal Linux), execute
    diretamente sem prefixo `wsl`.
- **Line endings obrigatoriamente LF** — arquivos `.bats` e scripts Bash
  executados no WSL/Linux devem usar LF (`\n`), nunca CRLF (`\r\n`).
  CRLF causa falhas silenciosas (ex: `grep "^---$"` não encontra `---\r`).
  Ao criar esses arquivos no Windows, garantir conversão para LF antes do commit.
- A estrutura de testes deve espelhar a estrutura do código.
- Se um teste cobre um script, ele deve ter o mesmo nome do script com sufixo `-test`.
- Não criar testes para scripts cuja única função é executar ou orquestrar testes.
- Scripts de bootstrap devem ficar em `scripts/bootstrap_repo/`.
- Novos scripts desse tipo também devem entrar em `scripts/bootstrap_repo/`.
- Os testes desses scripts devem espelhar isso em `tests/scripts/bootstrap_repo/`.
- **Nenhum teste pode usar `skip`** — quando um pré-requisito externo não estiver
  disponível, o teste deve usar `fail "mensagem clara"`. Testes de integração que
  dependem de ferramentas externas (pandoc, docling, resvg, playwright, etc.) devem
  falhar com instrução de instalação. Testes unitários nunca devem depender de
  ferramentas externas — usam mocks/stubs. Silenciar testes esconde problemas de
  ambiente.

# README
- Mantenha a seção de dependências do `README.md` atualizada sempre que mudar
  bootstrap, scripts, skills ou requisitos de instalação.
- A seção deve ser enxuta e voltada ao humano: listar claramente o que é
  instalado automaticamente e quais comandos com `sudo` o humano precisa
  executar.

# Upstream de Skills Externas
- Skills baseadas em repositórios externos devem seguir o padrão de upstream do repo:
  - Criar `UPSTREAM.md` na pasta da skill com a origem e instrucoes de sync.
  - Registrar a skill em `skills/list-updatable` para permitir atualização futura.
  - Usar `skills/update-upstream-skill` para sincronizar.

## Manutencao de Upstream — Padrao do Repo

### Estrutura obrigatoria por skill externa

```
skills/<nome>/
  SKILL.md        # adaptado localmente — NUNCA sobrescrito pelo sync
  UPSTREAM.md     # metadados de sync (SHA, data, origem, licenca)
  references/     # arquivos de referencia copiados do upstream (se houver)
```

### O que o UPSTREAM.md deve conter

- URL do repositorio + branch
- Commit SHA + data do commit upstream
- Data do ultimo sync
- Lista de arquivos sincronizados (o que muda a cada sync)
- Lista do que NAO e sincronizado (SKILL.md adaptado)
- Instrucoes de como rodar o sync
- Licenca do upstream
- `description_lang` + `description_note` (lingua e decisao de adaptacao)

### Lingua da description de skills externas

- Ao importar uma skill externa, **perguntar ao humano**: manter lingua de
  origem ou converter para PT-BR?
- Registrar a decisao no `UPSTREAM.md` da skill:
  ```
  description_lang: en
  description_note: >
    Kept in English (source language). Triggers extracted from
    "When to Use" section to improve activation.
  ```
- Padrao recomendado: manter lingua de origem — LLMs entendem associacoes
  semanticas cross-language e isso preserva proximidade com o upstream.
- A description **deve ser enriquecida** com triggers explícitos extraídos
  do corpo da skill (secao "When to Use"), pois o OpenCode ativa a skill
  com base exclusivamente na description.

### Regra de ouro do sync

O script de sync **nunca sobrescreve** `SKILL.md`. Ele so copia na criacao
inicial. Atualizacoes upstream devem ser aplicadas manualmente via merge.

### Checklist pos-sync

1. Revisar diff do conteudo copiado (references, assets, etc.)
2. Verificar se mudancas upstream afetam o `SKILL.md` local
3. Atualizar `SKILL.md` manualmente se necessario
4. Atualizar `UPSTREAM.md` com novo SHA (feito automaticamente pelo script)
5. Rodar `make test-opencode` para garantir que nada quebrou

### Scripts de sync disponiveis

| Skill(s) | Script |
|---|---|
| prompt-improver | `scripts/prompt-improver/sync.sh` |
| 12 skills addyosmani | `scripts/addyosmani/sync.sh` |
| accessibility-audit | `scripts/accessibility-audit/sync.sh` |

Todos suportam `--yes` e `--check-only`.

# Sincronizacao dos Adaptadores
- A fonte canonica fica em `agents/`, `skills/`, `commands/` e `docs/`.
- `adapters/opencode/` cria links simbolicos para a configuracao nativa.
- `adapters/copilot-cli/` converte e copia artefatos para `~/.copilot/`.
- Os scripts `adapters/copilot-cli/copilot-cli-adapter.ps1` e
  `adapters/copilot-cli/copilot-cli-adapter.sh`
  sao adaptadores do mesmo repo para o GitHub Copilot em plataformas diferentes.
- O comportamento canonico nao pertence a apenas um deles: o canonico e que ambos sao adaptadores
  deste repo para a estrutura de artefatos que o Copilot aceita em cada plataforma.
- Regra obrigatoria: os dois devem permanecer semanticamente sincronizados e devem ser alterados
  juntos sempre que houver mudanca no mapeamento `repo -> artefatos do Copilot`.
- Ao implementar a mudanca, adapte apenas diferencas de plataforma, paths e formato de deploy,
  preservando a mesma intencao e a mesma cobertura funcional nos dois ambientes.
- Se uma mudanca tocar apenas um desses scripts, o agente deve tratar isso como possivel
  divergencia, verificar imediatamente o outro e informar isso ao humano.
