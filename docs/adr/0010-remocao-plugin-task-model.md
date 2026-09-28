# ADR-0010: Remoção do plugin opencode-task-model no suporte nativo

- **Status:** Aceita
- **Data:** 2026-09-28
- **Escopo:** `harness-conf/opencode.json`, `README.md`,
  `harness-conf/AGENTS.base.md`, `tests/test_opencode_plugins.py`

## Contexto

O repo pina o plugin npm `opencode-task-model@1.3.1` para a tool `task`
aceitar `model` e `reasoning` por chamada. O status é PROVISÓRIO: quando
o OpenCode aceitar `model` nativamente na `task`, o plugin sai do
config.

O procedimento de remoção vivia só no arquivo de planejamento do ciclo
(`plan/insumo-devflow-spawn-dinamico.md`), que é descartado ao fim do
ciclo. O `UPSTREAM.md` do plugin apontava para a seção "Plugins" do
`README.md`, que carrega apenas o gatilho em frase. A doc durável
prometia um procedimento que não existia nela (achado 6 do rev,
2026-09-27).

## Decisão

O procedimento de remoção é a especificação executável abaixo: sete
passos em ordem, cada um com comando exato ou critério de verificação
objetivo. A verificação de um passo passa antes do início do seguinte.
Comandos são executados a partir da raiz do repo.

### Passo 1: confirmar o suporte nativo

- Ação: confirmar em release estável do OpenCode que a tool `task`
  aceita `model` nativamente.
- Verificação: `opencode --version` aponta release cujo changelog
  registra o merge do PR `anomalyco/opencode#34947` (ou equivalente
  que implemente `model` na `task`). Candidatas acompanhadas na seção
  "Rastreio do suporte nativo" de
  `harness-conf/plugins/opencode-task-model/UPSTREAM.md`.

### Passo 2: remover o pin do config

- Ação: remover a entrada `opencode-task-model@1.3.1` do array
  `plugin` em `harness-conf/opencode.json`.
- Verificação: `grep -n opencode-task-model harness-conf/opencode.json`
  termina sem nenhuma linha de saída.

### Passo 3: remover a citação do README

- Ação: remover o bullet do `opencode-task-model` da seção "Plugins"
  do `README.md` (a seção inteira, se nenhum outro plugin restar).
- Verificação: `grep -n opencode-task-model README.md` termina sem
  nenhuma linha de saída.

### Passo 4: remover a guarda dos agentes

- Ação: remover a seção "Tool task (plugin opencode-task-model)" de
  `harness-conf/AGENTS.base.md`.
- Verificação: `grep -n opencode-task-model
  harness-conf/AGENTS.base.md` termina sem nenhuma linha de saída.

### Passo 5: inverter a guarda de teste

- Ação: atualizar `tests/test_opencode_plugins.py` para exigir a
  ausência da entrada do plugin em `harness-conf/opencode.json` e de
  citação no `README.md`. O par de paridade quebra em estado
  intermediário; esse é o lembrete de segurança do repo.
- Verificação: o teste contém asserção de ausência nas duas pontas e
  falha se a entrada reaparecer em qualquer uma delas.

### Passo 6: executar a suíte completa

- Ação: `JAVA_HOME=/home/vitor/.local/share/jdk .venv/bin/pytest -m
  all` (no Windows, `.\.venv\Scripts\pytest.exe -m all`). O bootstrap
  instala o JDK e persiste `JAVA_HOME`; premissa ambiental ratificada.
- Verificação: resumo da execução sem `failed`; qualquer falha é
  investigada, nunca contornada com seleção reduzida de testes.

### Passo 7: commit

- Ação: commit único do estado final.
- Verificação: `git log -1 --format=%s` exibe a mensagem exata abaixo
  e `git show --stat HEAD` lista somente os arquivos dos passos 2 a 5.

  ```
  chore(harness): remove plugin provisorio opencode-task-model (suporte nativo)
  ```

## Consequências

- Estado intermediário (plugin citado em uma ponta e ausente em outra)
  deixa a suíte vermelha por design: a remoção completa cabe em um
  commit.
- O teste de paridade invertido vira guarda permanente contra a
  reaparição do plugin sem nova revisão de segurança.
- Este ADR e o `UPSTREAM.md` do plugin permanecem como histórico;
  ADRs nunca são deletados.
- Sem o plugin, a precedência nativa volta a valer integralmente:
  modelo do frontmatter do agente ou herança da sessão que chama.

## Alternativas consideradas

- Manter o procedimento só no insumo do ciclo: rejeitada porque o
  arquivo de planejamento é descartado ao fim do ciclo e a doc durável
  prometia o procedimento sem carregá-lo.
- Mover o procedimento para o `UPSTREAM.md`: rejeitada porque o
  registro upstream documenta origem e revisão de segurança do
  pacote, não decisões de arquitetura; decisão relevante exige ADR
  com asserção executável na convenção deste repo.
- Deixar o plugin instalado indefinidamente: rejeitada porque ele
  sobrescreve a tool `task` para todos os agentes e o suporte nativo
  elimina essa superfície.

## Asserções executáveis

A fixture Concordion deste ADR expõe `executarVerificacoes()` e
`veredito`. A diretiva `execute` executa as verificações da decisão.
A diretiva `assertEquals` fixa o veredito esperado.

- [Executar as verificações deste ADR](#execute=executarVerificacoes()).
- A fixture valida a coerência do estado em qualquer momento: a citação
  a `opencode-task-model` está presente nas três pontas duráveis
  (`harness-conf/opencode.json`, `README.md` e
  `harness-conf/AGENTS.base.md`) enquanto o plugin está instalado, ou
  ausente das três depois do procedimento executado; estado misto
  reprova. Enquanto instalado, a entrada do config casa com
  `versao_pinada` do `UPSTREAM.md`.
- O veredito agregado da implementação é [pass](#assertEquals=veredito).
