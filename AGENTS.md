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
- Comandos canônicos por sistema:

```bash
bash ./scripts/bootstrap_repo/configurar-repo.sh --yes
```

```powershell
.\scripts\bootstrap_repo\configurar-repo.ps1 --yes
```
- Se uma dependencia nao estiver disponivel, use os comandos user-space
  exibidos pelo bootstrap e aguarde a execucao pelo humano antes de seguir.
  Nao introduza instrucoes que exijam `sudo` ou administrador.

## Configuracao Global via Links Simbolicos

- Este repo `opencode-config` e o fonte de verdade das configs globais do OpenCode.
- Para o OpenCode enxergar estes arquivos de forma global, usamos links simbolicos a partir de `~/.config/opencode`.

Padrao de links (exemplo neste ambiente WSL):

```bash
mkdir -p ~/.config/opencode
REPO_ROOT="$(pwd)"

ln -s "$REPO_ROOT/agents" \
      ~/.config/opencode/agents

ln -s "$REPO_ROOT/commands" \
      ~/.config/opencode/commands

ln -s "$REPO_ROOT/opencode.json" \
      ~/.config/opencode/opencode.json

ln -s "$REPO_ROOT/skills" \
      ~/.config/opencode/skills

ln -s "$REPO_ROOT/scripts" \
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

No Windows, execute `.\scripts\bootstrap_repo\configurar-repo.ps1 --yes` no
PowerShell. O bootstrap detecta e instala dependências em user-space, sem
`sudo` ou administrador. Linux/WSL configura o OpenCode; Windows configura
somente o Copilot CLI. Use `--yes`, `--quiet` ou `--check-only`.

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

As variáveis de ambiente do pacote, incluindo os overrides de diagnóstico
`OPENCODE_SKIP_*`, estão documentadas na seção "Variáveis de ambiente" do
`README.md`. Não use esses overrides em uma validação completa.

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
- Sempre que for exibir um texto cuja inteção é permitir que ao usuário copiar e
  colar, faça isso em um bloco de código único para facilitar a cópia.

## Acao
- Nao execute mudancas (edicao de arquivos, comandos destrutivos) sem confirmacao explicita do humano.
- Perguntas do humano nao sao ordens de execucao; responda a pergunta e aguarde instrucao explicita para agir.

## SmartPlanner — Restricao Comportamental
- O agente `smart-planner` **nunca** edita codigo de aplicacao durante planejamento.
- Apenas le arquivos para entender contexto. A unica escrita permitida e o arquivo de planejamento.

## COMMITS

- Use Conventional Commits. Formato: `tipo(escopo): descricao curta`
  Tipos: feat, fix, docs, style, refactor, test, chore, ci, build, perf.
- Mensagem de commit concisa e resumida: sem filler, direta ao ponto.
- Proponha mensagens de commit sempre que o humano pedir.
- Descubra a linguagem definida pelo contexto do Projeto, mas use PT-BR por padrão caso não encontre.
- O humano sempre que validar tudo antes do commit, então **não** realize o commit antes do humano validar e dar ok.
- Mostre a mensagem de commit, mas SEMPRE espere confirmação do humano para realizar o commit
- NUNCA realize o commit independentemente.
- SEMPRE pergunte ao humano antes de realizar o commit.
- SÓ realize o commit quando o humano autorizar
- **Exceção — smart-planner:** durante o planejamento, depois que o humano
  confirma a modificação do plano, o smart-planner commita o arquivo de
  planejamento automaticamente, sem perguntar "posso commitar?" por commit.
  O agrupamento de modificações em cada commit é decidido pelo agente
  (nem micro-commits ruidosos, nem batches grandes que perdem atomicidade).
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

# Regras Obrigatórias Para Testes
- Toda evolução funcional do repo deve criar ou atualizar testes automatizados.
- Aplica-se a: novos scripts, skills, comandos, agentes e mudanças no bootstrap.
- Framework: `pytest` em `tests/`. No WSL/Linux, use
  `.venv/bin/pytest -m "unit or tools or opencode"`; no Windows, use
  `.\.venv\Scripts\pytest.exe -m "unit or tools or copilot"`.
- Execute os testes no ambiente alvo. A integração OpenCode requer Docker e o
  llama-server local do Bonsai no WSL/Linux; a integração Copilot roda no
  Windows.
- O servidor Bonsai fica em `tests/integration/model/` e deve ser iniciado com
  `python3 tests/integration/model/bonsai_server.py --up` antes da integração.
- Não use `skip`: quando uma dependência externa não estiver disponível,
  use `pytest.fail` com uma mensagem clara e acionável.
- A estrutura de testes deve espelhar a estrutura do código.
- Testes de scripts devem ficar em `tests/scripts/` com nomes `test_*.py`.
- Não crie testes para scripts cuja única função é executar ou orquestrar testes.
- Scripts de bootstrap devem ficar em `scripts/bootstrap_repo/`.
- Novos scripts desse tipo também devem entrar em `scripts/bootstrap_repo/`.
- Os testes desses scripts devem espelhar isso em `tests/scripts/bootstrap_repo/`.
- **Nenhum teste pode usar `skip`** — quando um pré-requisito externo não estiver
  disponível, o teste deve usar `pytest.fail("mensagem clara")`. Testes de integração que
  dependem de ferramentas externas (pandoc, docling, playwright, etc.) devem
  falhar com instrução de instalação. Testes unitários nunca devem depender de
  ferramentas externas — usam mocks/stubs. Silenciar testes esconde problemas de
  ambiente.

# README
- Mantenha a seção de dependências do `README.md` atualizada sempre que mudar
  bootstrap, scripts, skills ou requisitos de instalação.
- A seção deve ser enxuta e voltada ao humano: listar claramente o que é
  instalado automaticamente e quais comandos user-space o humano pode
  executar.

# Upstream de Skills Externas
- Skills baseadas em repositórios externos devem seguir o padrão de upstream do repo:
  - Criar `UPSTREAM.md` na pasta da skill com a origem e instrucoes de sync.
  - Registrar a skill no comando `opencode-skills list` para permitir atualização futura.
  - Usar `opencode-skills update NOME` para sincronizar.

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
5. Rodar os testes no executável pytest do SO para garantir que nada quebrou:
   WSL/Linux com `.venv/bin/pytest -m "unit or tools"` ou Windows com
   `.\.venv\Scripts\pytest.exe -m "unit or tools"`.

### Scripts de sync disponiveis

| Skill(s) | Comando |
|---|---|
| prompt-improver | `opencode-skills sync prompt-improver` |
| 12 skills addyosmani | `opencode-skills sync addyosmani` |
| accessibility-audit | `opencode-skills sync accessibility-audit` |

Todos suportam `--yes` e `--check-only`.

# Sincronizacao dos Adaptadores
- A fonte canonica fica em `agents/`, `skills/`, `commands/` e `docs/`.
- `adapters/opencode/` cria links simbolicos para a configuracao nativa.
- `adapters/copilot-cli/` documenta o adapter Python que converte e copia
  artefatos para `~/.copilot/`.
- O comportamento canônico fica em
  `src/opencode_config/adapters/copilot.py`, com o mesmo comando em Linux,
  WSL e Windows.
- Os entrypoints finos `configurar-repo.sh` e `configurar-repo.ps1` apenas
  verificam Python e delegam ao pacote; não existem adapters paralelos por
  shell para sincronizar.
- Ao alterar o comportamento de um adapter, atualize o módulo Python e seus
  testes correspondentes. Verifique também o outro adapter quando a mudança
  afetar o contrato entre plataformas.
