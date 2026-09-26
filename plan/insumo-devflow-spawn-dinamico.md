# Insumo para o devflow: spawn dinâmico de subagentes com modelo por chamada

Data: 2026-09-26. Status: PROVISÓRIO, aguardando revisão do devflow.
Leitor esperado: o orquestrador devflow. Este documento é autocontido.

## Contexto

O OpenCode (verificado na versão 1.18.32) não aceita `model` na tool `task`.
Um orquestrador não conseguia escolher o modelo do subagente por chamada.
A alternativa nativa exigia um agente pré-criado para cada modelo.

O repo adotou o plugin npm `opencode-task-model`, versão pinada `1.3.1`.
O plugin sobrescreve a tool `task` e aceita `model` e `reasoning` por
chamada. O status é PROVISÓRIO: o plugin sai do config quando o OpenCode
suportar `model` nativamente na `task`.

Rastreio do suporte nativo (confirmado em 2026-09-26):

- Issue `anomalyco/opencode#6651`: seleção dinâmica de modelo para
  subagentes via tool `task`. Aberta, confirmada.
- PR `anomalyco/opencode#34947`: adiciona controles de despacho à tool
  `task`, incluindo `model`. Em review, não mergeado na data deste
  documento.
- Issue `anomalyco/opencode#17595`: override de modelo em runtime,
  relacionada ao PR #34947.

Revisão de segurança (barreira de adoção, já executada):

- Fonte: repo `lars-hagen/opencode-task-model`, tag `v1.3.1`, commit
  `baedc8977fb16127016ca6cbf4a772e9e9693be2` (2026-07-30).
- O tarball npm `1.3.1` é idêntico, byte a byte, ao commit revisado.
- Nenhum finding bloqueante. O plugin não tem dependências de runtime,
  não executa comandos, não acessa hosts externos e fala apenas com a
  API local do OpenCode.
- Registro completo:
  `harness-conf/plugins/opencode-task-model/UPSTREAM.md`.

## O que foi implementado

- `harness-conf/opencode.json`: o array `plugin` recebeu a entrada
  `opencode-task-model@1.3.1` (pin exato, sem range e sem `@latest`).
- `README.md`: nova seção "Plugins" com status PROVISÓRIO, rastreio e
  procedimento de remoção.
- `harness-conf/AGENTS.base.md`: guarda de uso da tool `task` para todos
  os agentes (detalhes em "Como usar" abaixo).
- `harness-conf/plugins/opencode-task-model/UPSTREAM.md`: origem, SHA,
  findings e instruções de atualização.
- `tests/test_opencode_plugins.py`: testes unitários. O primeiro exige
  pin exato semver em toda entrada de `plugin`. O segundo exige o par
  config ↔ README: se a entrada do plugin sumir de um dos dois, o teste
  quebra e lembra a remoção completa.
- `tests/integration/test_task_model_spawn.py`: teste de integração que
  valida o spawn dinâmico pelo caminho real de uso (detalhes em
  "Validação executada").

Commits: `0f1ce5e`, `cdde56f`, `1041452`. Nenhum arquivo de `src/` ou
`adapters/` foi alterado.

## Como usar

- A tool `task` aceita `model` no formato `provider/model`, por exemplo
  `zai-coding-plan/glm-5.3-flash`, e aceita `reasoning`
  (`default`, `low`, `medium`, `high`; valores sem suporte são ignorados
  pelo OpenCode).
- Sem `model` e sem `reasoning`, a precedência nativa permanece intacta:
  vale o modelo do frontmatter do agente; agente sem frontmatter herda o
  modelo da sessão que chama. Esse é o comportamento canônico e o
  padrão dos agentes do repo.
- Instrução permanente aos agentes (guarda do `AGENTS.base.md`): omita
  `model` e `reasoning` por padrão. Use `model` apenas quando o briefing
  do humano ou do plano pedir um modelo específico para a subtask.
- `background` e `worktree` não fazem parte do fluxo aprovado e não
  foram validados neste ciclo. A guarda restringe `background: true` a
  escopo aprovado. O argumento `worktree` não existe no pin `1.3.1`;
  o parágrafo do README e a guarda citam `worktree` para a remoção
  futura, e o devflow deve tratar essa citação como aspiracional.
- Prompts delegados não resolvem `@arquivo`. Inclua o conteúdo do
  arquivo no texto do prompt.

O agente `worker` (`harness-conf/agents/worker.md`) mantém `model:` no
frontmatter como fallback. O plugin não altera a precedência sem
argumento explícito.

## Validação executada em 2026-09-26

Pré-requisito cumprido: providers reais `zai-coding-plan/glm-5.3-flash`
e `zai-coding-plan/glm-5.3` configurados no ambiente do usuário. Os dois
modelos pertencem ao mesmo plano z.ai; o storage registra custo 0,0000
para as sessões (o plano não tarifa por token).

### Validação automatizada

- Teste: `tests/integration/test_task_model_spawn.py`, marker
  `integration`. O teste executa `opencode run` headless com o plugin
  carregado pela config global do OpenCode. O plugin chega ao ambiente
  pelo symlink `~/.config/opencode/opencode.json` →
  `harness-conf/opencode.json`, criado pelo bootstrap. O teste não
  altera o ambiente global.
- Cenário: o agente primário (modelo flash) chama a tool `task` três
  vezes sobre o MESMO subagente built-in `general`, sem agente
  pré-criado por modelo. Chamada 1 com `model` flash. Chamada 2 com
  `model` `glm-5.3`. Chamada 3 sem `model`.
- Verificação: o teste lê a coluna `model` da tabela `session` do
  storage local (`~/.local/share/opencode/opencode.db`) e compara o
  modelo efetivo de cada child. O teste também confere o texto devolvido
  por cada child. Nenhuma chamada direta a API de provider; nenhuma
  sessão child fora da tool `task`.
- Resultado observado (run `it-task-model-105cf808`, duração 81 s):

  | Spawn | Esperado | Efetivo no storage |
  |---|---|---|
  | `general` com `model` flash | `glm-5.3-flash` | `glm-5.3-flash` ✓ |
  | `general` com `model` `glm-5.3` | `glm-5.3` | `glm-5.3` ✓ |
  | `general` sem `model` | herda `glm-5.3-flash` do pai | `glm-5.3-flash` ✓ |

- Suíte: `JAVA_HOME=/home/vitor/.local/share/jdk .venv/bin/pytest -m
  integration` → 75 passed. `JAVA_HOME=/home/vitor/.local/share/jdk
  .venv/bin/pytest -m all` → 836 passed (2026-09-26).

### Runbook manual (segunda execução, independente do teste)

Passos reproduzíveis:

1. Crie o diretório de trabalho. O OpenCode recusa projeto sob `/tmp`
   nesta máquina e exige o diretório pré-existente:
   `mkdir -p ~/.local/state/runbook-spawn-dinamico`.
2. Execute um run headless com o plugin carregado (a config global já
   declara o plugin):

   ```
   opencode run --model zai-coding-plan/glm-5.3-flash \
     --title "runbook-spawn-dinamico" \
     --dir ~/.local/state/runbook-spawn-dinamico \
     "Use a tool task duas vezes, em sequencia, sem nenhuma outra tool.
   Primeira: subagent_type=general, description='execucao rapida',
   model='zai-coding-plan/glm-5.3-flash', prompt='Responda apenas com a
   palavra: RAPIDO'. Segunda: subagent_type=general, description=
   'execucao robusta', model='zai-coding-plan/glm-5.3', prompt='Responda
   apenas com a palavra: ROBUSTO'. Nenhum agente customizado foi criado
   para isso; use o subagente built-in general nas duas. Ao terminar,
   liste as duas respostas recebidas."
   ```

3. Verifique o modelo efetivo de cada child no storage (leitura
   somente-leitura):

   ```
   sqlite3 "file:$HOME/.local/share/opencode/opencode.db?mode=ro" \
     "SELECT id, parent_id, agent, model FROM session
      WHERE directory LIKE '$HOME/.local/state/runbook-spawn-dinamico%'"
   ```

   A coluna `model` contém JSON com `providerID` e `id`. Para ver a
   resposta de um child, consulte `SELECT data FROM part WHERE
   session_id = '<id>'` e filtre `type = 'text'`.

Evidência registrada (execução de 2026-09-26 20:02:01 a 20:02:48,
horário -03:00, duração 46,5 s, custo 0,0000):

- Sessão pai: `ses_f200bb57dffeuLqLGCk1dSYDTI`, agente `build`,
  modelo `zai-coding-plan/glm-5.3-flash`.
- Child 1: `ses_f200b84e0ffe8EVmThzf388rS3`, agente `general`, modelo
  `zai-coding-plan/glm-5.3-flash`, resposta `RAPIDO`.
- Child 2: `ses_f200b533dffeWqf6nGcG77Y7bR`, agente `general`, modelo
  `zai-coding-plan/glm-5.3`, resposta `ROBUSTO`.

O mesmo tipo de subagente (`general`) rodou com dois modelos distintos
na mesma execução, sem agente pré-criado por modelo.

## Remoção do plugin quando o suporte nativo chegar

1. Confirme na release do OpenCode que a tool `task` aceita `model`
   nativamente (acompanhe a issue #6651 e o PR #34947).
2. Remova a entrada `opencode-task-model@1.3.1` de
   `harness-conf/opencode.json`.
3. Remova a seção "Plugins" do `README.md` ou o parágrafo do plugin.
4. Remova a guarda "Tool task (plugin opencode-task-model)" do
   `harness-conf/AGENTS.base.md`.
5. Atualize `tests/test_opencode_plugins.py`: o teste de paridade
   config ↔ README quebra até a remoção ficar completa; esse é o
   lembrete de segurança do repo.
6. Execute a suíte completa:
   `JAVA_HOME=/home/vitor/.local/share/jdk .venv/bin/pytest -m all`.
7. Commit sugerido: `chore(harness): remove plugin provisorio
   opencode-task-model (suporte nativo)`.

Para atualizar o pin antes da remoção: execute primeiro uma nova
revisão de segurança da versão nova (ler o tarball, comparar com a tag
correspondente, refazer os findings) e atualize o
`UPSTREAM.md`. Só então suba o pin no config e a versão no README.

## Pedido ao devflow

Revisar o implementado e promover a aderência ao repo. O escopo da
revisão fecha no que este documento descreve; não há sugestões novas de
adoção ou funcionalidade.

Checklist de revisão e aderência:

1. Execute a suíte completa no ambiente corrente:
   `JAVA_HOME=/home/vitor/.local/share/jdk .venv/bin/pytest -m all`.
   A variável `JAVA_HOME` é pré-requisito ambiental já conhecido do
   repo; sem ela a suíte falha por motivo ambiental pré-existente.
2. Execute `tests/agents/test_workflow_consistency.py` e confirme que
   nada ficou órfão. O plugin não criou agente, command nem skill
   novos; a guarda do `AGENTS.base.md` é o único texto novo voltado a
   agentes.
3. Valide `harness-conf/plugins/opencode-task-model/UPSTREAM.md` contra
   o padrão de registro de origem do repo (origem, SHA, data, findings,
   instruções de atualização).
4. Valide a seção "Plugins" do `README.md`: enxuta, com status
   PROVISÓRIO, rastreio e procedimento de remoção.
5. Cheque a guarda "Tool task (plugin opencode-task-model)" do
   `AGENTS.base.md` contra o comportamento validado neste documento. Ao
   revisar, considere o fato registrado em "Como usar": a citação a
   `worktree` é aspiracional no pin `1.3.1`.
6. Confirme que nenhum arquivo de `src/` ou `adapters/` mudou nos
   commits `0f1ce5e`, `cdde56f` e `1041452`.

Pendência conhecida, fora do escopo deste trabalho:
`@slkiser/opencode-quota` segue sem pin no array `plugin` e flutua para
a versão mais recente. O teste de pin exato do repo aceita entradas
escopadas sem versão. Decidir pinar ou ajustar o critério é decisão de
ciclo futuro.
