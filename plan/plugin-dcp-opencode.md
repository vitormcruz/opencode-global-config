# Plano: incorporação do plugin DCP (Dynamic Context Pruning) ao OpenCode

Status: VALIDAÇÃO

Workflow aberto em 2026-09-27. Escopo deste ciclo: até a aprovação do plano
(fase REVISÃO DO PLANO). Construção e fases seguintes só se o humano decidir
após a aprovação.

Controle do humano (2026-09-27): "esperar para tudo". Nenhuma fase executa
sem confirmação explícita; único spawn autorizado é o commit deste plano
pelo eng-software (com pesquisa do ref do modelo luna).

## Insumo do humano (2026-09-27)

### Contexto

Este projeto usa OpenCode como ferramenta de desenvolvimento assistido.
Sessões longas enchem a janela de contexto. O `/compact` nativo é comando de
usuário e apresentou falhas recentes (anomalyco/opencode#17557: o contexto
aumentava em vez de diminuir). A decisão foi adotar o plugin DCP, que expõe
a compactação como ferramenta chamável pelo próprio agente. Este prompt é
autocontido; nenhuma conversa anterior é necessária.

### O que é o DCP

- Pacote npm: `@tarquinen/opencode-dcp`
- Repo: https://github.com/Opencode-DCP/opencode-dynamic-context-pruning
- Registra a tool `compress` no contexto do modelo: o agente decide quando
  comprimir, escolhe os ranges (IDs `mNNNN`/`bN`) e escreve os sumários. O
  histórico original nunca é modificado; o plugin substitui conteúdo por
  placeholders antes de enviar requisições ao LLM.
- Nudges: lembretes injetados no prompt quando o contexto passa de
  `maxContextLimit`, empurrando o agente a chamar `compress`.
- Instalação: `opencode plugin @tarquinen/opencode-dcp@latest --global` ou
  `"plugin": ["@tarquinen/opencode-dcp"]` no `opencode.json`.
- Config principal: `compress.permission` (allow|ask|deny), `compress.mode`
  (range|message), `maxContextLimit`, `minContextLimit`, `nudgeFrequency`,
  `iterationNudgeThreshold`, `protectedFilePatterns`, `protectedTools`,
  `protectUserMessages`, `manualMode`, `strategies` (deduplication,
  purgeErrors), `experimental.allowSubAgents`.
- Comandos: `/dcp` (painel TUI), `/dcp-compress [focus]`.
- Licença: AGPL-3.0-or-later.

### Ressalva de escopo (importante para o plano)

Não existe alternativa equivalente no GitHub Copilot: a compactação é
host-level, o agente não tem tool para dispará-la (o hook `preCompact` é
apenas notificação). O MCP `compaction-mcp` até gera resumos, mas não evicta
mensagens da janela do host; recuperar tokens exige re-seed em chat novo.
Conclusão: o ganho desta implementação vale apenas onde o fluxo roda
OpenCode. Partes do workflow que rodarem no Copilot continuam sem compactação
acionável pelo agente. O plano deve mapear quais fluxos rodam em qual
ferramenta.

### O que planejar (entregável: plano em fases, sem implementar)

1. Inventário: versão do OpenCode em uso, plugins e MCP servers já
   configurados, uso de subagents (suporte do DCP a subagents é experimental
   via `experimental.allowSubAgents`; validar se os subagents do projeto
   funcionam com ele ativo).
2. Escopo de ativação: global vs por projeto; modo (`range` vs `message`) e
   thresholds iniciais coerentes com o tamanho de contexto dos modelos
   usados no projeto.
3. Riscos: interação com hooks/plugins que também transformam prompt
   (transformações concorrentes), AGPL-3.0 (relevante só se o projeto
   distribuir código derivado), permission gate (`allow` vs `ask`) diante
   das regras de permissão existentes.
4. Validação: critérios objetivos para aceitar o plugin (tokens de contexto
   caem após `compress`, prompt cache não degradado, subagents sem regressão)
   e rollback (remover do config e reiniciar).
5. Rollout: fases com pontos de verificação e critério de decisão explícito
   por fase.

## Contexto adicional levantado pelo devflow (2026-09-27)

- Política de compactação vigente (decisão D11 do plano
  `otimizacao-custo-contexto.md`, commit `c24068d`): o `AGENTS.base.md`
  orienta todos os agentes a preferir mecanismos automatizados (auto
  compactação por threshold, nova sessão com estado persistido) e, sem
  alternativa, pedir `/compact` ao humano. A tool `compress` do DCP muda
  essa premissa: prever atualização do texto do `AGENTS.base.md` e da
  premissa 7 de `docs/workflow-agentes-dev.md` (exceção de compactação).
- Plugin ai-memory ativo em user-space
  (`~/.config/opencode/plugins/ai-memory.ts`) com hooks em
  `experimental.session.compacting`/`session.compacted`; MCP ai-memory com
  provisionamento no bootstrap (decisão P1 do ciclo vizinho). O risco de
  "transformações concorrentes" citado no insumo INCLUI esse plugin.
- Baseline de compactação (Task 12 do ciclo vizinho, 2026-09-23): `/compact`
  reduziu o contexto de ~88,6k para ~55,4k tokens/chamada (-37%); payback
  ~1,1 chamada; provider zai reporta `cost`=0 (medição em tokens; US$ só
  com tarifa externa). Método de medição: sqlite em
  `~/.local/share/opencode/opencode.db`, tabela `message`.
- Mapa de modelos decidido em 2026-09-27 no ciclo vizinho: executores =
  `opencode/gpt-6-luna` (reasoning high); revisor =
  `zai-coding-plan/glm-5.3`.
- Config canônica do OpenCode: `harness-conf/opencode.json` (symlink global
  no Linux/WSL; cópia sincronizada no Windows). Regra do repo: toda mudança
  em workflow ou agentes passa pelo humano; consistência guardada por
  `tests/agents/test_workflow_consistency.py`.
- Regra do repo para skills/plugins importados: revisão de segurança
  obrigatória na importação (ler TODO o conteúdo copiado procurando prompt
  injection, comandos, URLs e exfiltração) e registro de proveniência.

## Mapa de modelos deste workflow

Decidido pelo humano em 2026-09-27:

- VALIDAÇÃO e execução (CONSTRUÇÃO/TESTES, se ocorrerem neste ciclo): modelo
  luna com reasoning `max`. Ref exato pendente de verificação: o humano
  indicou provider "opencode-go"; o repo só registra `opencode/gpt-6-luna`
  (provider `opencode`, zen). Confirmar a saída de `opencode models` antes
  do primeiro spawn dessas fases.
- PLANEJAMENTO e REVISÃO DO PLANO: `zai-coding-plan/glm-5.3` (modelo
  corrente da sessão), reasoning default.
- Nada executa sem confirmação do humano (decisão "esperar para tudo",
  2026-09-27); único spawn autorizado: commit deste plano pelo eng-software.

## Perguntas

1. ABERTA (2026-09-27): ref exato do modelo luna para validação/execução.
   Humano indicou provider "opencode-go" e reasoning `max` como effort (não
   como parte do nome). Verificar com `opencode models`; se o provider
   "opencode-go" não existir, confirmar com o humano antes de spawnar.

## VALIDAÇÃO

(a preencher pelo curador-produto)

## PLANEJAMENTO

(a preencher pelos especialistas)

## REVISÃO DO PLANO

(a preencher pelo rev)
