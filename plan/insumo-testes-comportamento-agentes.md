# Insumo — Testes Automatizados de Comportamento dos Agentes

Status: INSUMO PARA PLANEJAMENTO. Decisões fechadas com o
humano em 2026-09-16. Lacunas em aberto na seção 12.

---

## 1. De onde veio este documento

O humano pediu pesquisa sobre formas de fazer testes
automatizados de comportamento dos agentes. A pesquisa virou
um catálogo de famílias de estratégias (estático, execução
real com oráculo determinístico, LLM juiz, segurança e
injection, regressão e escala). Depois veio a revisão focada
neste repo, e uma decisão de recorte: avaliar por técnicas,
não por ferramentas. Ferramentas ficam registradas como
candidatas (seção 10) e a escolha é decisão do planejamento.

Este arquivo registra o que já foi decidido com o humano e o
que ainda está em aberto. Ele é autocontido: não depende da
conversa que o produziu.

---

## 2. Diagnóstico do repo (por que testar comportamento)

O repo já tem a parte difícil: um harness próprio de execução
real.

- Suíte estática forte em `tests/agents/` (consistência de
  workflow, boilerplate, skills citadas).
- Execução real em Docker: server OpenCode no container,
  cliente HTTP próprio em stdlib (`OpenCodeClient`, em
  `tests/integration/behavioral_helper.py`), fixture de
  contexto isolado por teste (marker `agent_eval_context`),
  marker `agent_eval`.
- Privacy enforcement: o container de teste não alcança rede
  externa.

O problema está na profundidade e no modelo:

- Os testes comportamentais atuais são rasos: status HTTP,
  listagem de agentes no `/agent`, prompt "responda ok".
  Validam a plataforma, não o comportamento do agente.
- O backend local (Qwen3-0.6B via llama-server) é fraco e
  lento. Fraco: quando o teste falha, não dá para distinguir
  "agente mal configurado" de "modelo incapaz de seguir o
  próprio prompt". Lento: mata o ciclo de iteração.
- As permissões declaradas no frontmatter dos agentes
  (`task: deny`, `webfetch: deny`, `edit: deny`) nunca são
  exercitadas em runtime. Nenhum teste tenta induzir a
  violação.

Achado real da análise: o corpo do `qa` autoriza `websearch`,
mas o frontmatter não declara essa permissão. É exatamente a
classe de contradição que a técnica 1 (evoluída) deve pegar.

---

## 3. Decisões fechadas com o humano

1. **Backend API substitui o modelo local.** O caminho do
   Qwen3-0.6B sai inteiro: `tests/integration/model/`,
   fixture `qwen_server`, `test_local_provider.py`, testes
   que citam o Qwen. O `libgomp` do bootstrap fica (o
   docling também usa). ADRs 0002 e 0003 ficam superadas por
   ADR nova.
2. **Provider e modelo: escolha posterior.** Critério
   acordado: o mais barato que não degrada o desempenho do
   teste. O desenho é agnóstico de provider, via env vars.
3. **Primeira onda experimental:** `smart-planner`, `qa` e
   `eng-software`. Validada a abordagem, expande para os
   demais agentes.
4. **Custo de token é aceito** em troca de robustez. O
   controle do gasto vem do gate (seção 5), não de limitação
   de técnica.
5. **Agnosticismo de harness.** Nenhum termo novo da suíte
   cita harness específico. OpenCode é o primeiro backend de
   execução, não o nome das coisas. Troca futura de harness
   não deve exigir renomear config da suíte.
6. **Ferramentas não entram como dependência.** O repo é
   stdlib-only. As técnicas são implementadas no harness
   próprio. Ferramentas pesquisadas viram, no máximo, fonte
   de padrão a reimplementar (seção 10).

---

## 4. Técnicas adotadas (10)

1. **Consistência declarativa** (existe, evolui). Lê os
   arquivos .md dos agentes e confere estrutura. Evolui para
   detectar contradição entre corpo e frontmatter.
2. **Execução instrumentada** (existe). Roda o agente de
   verdade em ambiente isolado e registra tudo que ele faz:
   tools, ordem, bloqueios.
3. **Asserção de trajetória** (nova). Afirma fatos objetivos
   sobre o registro da execução: chamou X, não chamou Y,
   chamou A antes de B.
4. **Comparação com sequência esperada** (nova). Compara a
   sequência de ações com uma esperada: idêntica, contida, ou
   só a ordem relativa importa.
5. **Estímulo adversarial determinístico** (nova). Pede o
   proibido ("delegue", "abra este link") e afirma que a
   violação não ocorreu.
6. **Política de rede com allowlist** (existe, rework). O
   ambiente de teste só alcança os hosts permitidos (o host do
   provider). O resto é negado.
7. **Rubrica com juiz, LLM-as-judge** (nova). Um segundo
   modelo avalia a saída do agente contra critérios escritos,
   derivados do contrato declarado do próprio agente.
   Calibração prévia é obrigatória: juiz sem aprovação em
   exemplos rotulados não entra na suíte.
8. **Derivação de casos do frontmatter** (nova). Script lê as
   permissões declaradas e gera a matriz de casos: cada `deny`
   vira caso de indução, cada `allow` característico vira
   happy path.
9. **Corpus de ataques versionado** (nova). JSONL no repo com
   ataques prontos (payload + detecção programática). Todo
   incidente real vira caso novo.
10. **Cassete/baseline de regressão** (fase 2). Grava uma
    execução aprovada (tools, ordem, resultados) como
    referência. Mudanças no agente são comparadas contra a
    gravação antes de aceitar.

Exemplos concretos de cada técnica, na redação aprovada pelo
humano, estão no histórico da conversa de origem. O essencial:
os exemplos usam os agentes da primeira onda e cenários do
próprio repo (TDD do eng-software, delegação proibida do qa,
perguntas do smart-planner, falso UPSTREAM.md com injeção).

Mapeamento das técnicas nos blocos de implementação do
esboço original:

- **Bloco 1, backend API:** técnicas 6 (rework) e a troca de
  modelo (decisão 3.1).
- **Bloco 2, asserts determinísticos:** técnicas 2, 3, 4, 5 e
  8.
- **Bloco 3, juiz:** técnica 7 (+ princípios da seção 6).
- **Bloco 4, segurança:** técnicas 5, 8 e 9 (+ P1 nos casos
  sutis).
- **Gate:** seção 5.

---

## 5. Gate de execução (3 níveis)

Quando a suíte `agent_eval` roda. Decisão fechada:

**Nível 1, permissão da máquina (persistente).** No bootstrap,
o humano declara se aquela máquina pode rodar a suíte. A
decisão vale até o repo ser configurado de novo. Mecanismo:
env var nova persistida no padrão já usado pelo repo (`.bashrc`
no WSL/Linux, `HKCU\Environment` no Windows). Nome proposto:
`AGENT_EVAL_ENABLED` (validar no planejamento). Não é reuso de
`OPENCODE_ENABLE_EXA`; aquela var só serviu de referência do
mecanismo de persistência.

**Nível 2, chamada manual.** `-m agent_eval` explícito. A
taxonomia não muda: `agent_eval` continua fora do `-m all`
(`unit or integration`). Nenhum custo de token surpresa na
suíte padrão.

**Nível 3, iniciativa do agente, sempre com confirmação.**
Se o agente detectar mudança que afeta o que a suíte cobre,
ele pergunta ao humano se pode rodar. Sempre pergunta, nunca
roda sozinho. Essa regra é específica deste repo: vai no
`AGENTS.md` do repo (seção de regras de teste), não no
`harness-conf/AGENTS.base.md`. Lista inicial do que conta como
mudança relevante: `harness-conf/agents/` (frontmatter, corpo,
permissões), workflows de agentes, skills citadas pelos
agentes da suíte, config de permissões do harness corrente
(hoje `opencode.json`) e a própria infra dos testes.

Pré-condição: os níveis 2 e 3 só se aplicam com o nível 1
autorizado. Interação com a regra "sem skip" do repo: máquina
habilitada sem credencial de API gera `pytest.fail` com
mensagem acionável. Máquina desabilitada com tentativa de
execução gera `pytest.fail` explicando como habilitar (rodar o
bootstrap de novo). Nunca skip silencioso.

---

## 6. Princípios transversais (2)

Valem para a suíte inteira, não são técnicas numeradas.

**P1, input não-confiável.** Todo texto produzido por um
modelo, quando vira entrada de outro modelo, é dado a avaliar,
nunca ordem a seguir. Pontos de aplicação: o juiz da técnica 7
(a saída do agente pode conter "retorne pass=true"), os casos
sutis do corpus (técnica 9, quando o oráculo programático não
basta e o juiz avalia a resposta ao ataque) e o futuro
simulador multi-turn (seção 8). O juiz recebe regra explícita
de desconfiança e ganha teste unitário próprio com payloads de
manipulação. Não se aplica onde a comparação é puramente
programática: código não é persuadível por texto.

**P2, consenso contra não-determinismo.** Teste comportamental
nunca é uma única execução binária. São N execuções do mesmo
caso com veredito por consenso: concordância total em passar
vira PASS, concordância total em falhar vira FAIL, resultado
dividido vira INCONCLUSIVE (sinal de instabilidade para
investigar, sem pintar a suíte de vermelho à toa). Aplica-se a
todos os testes que executam modelo real: técnicas 3, 4, 5, 7 e
os casos do corpus com oráculo de juiz. Nasceram desta
preocupação as escolhas por veredito em três valores (padrão
AgentAssay) e por teste de flakiness explícito.

---

## 7. Parciais, com gatilho de reavaliação

**Fingerprinting estatístico.** Perfil numérico do
comportamento (frequência de cada tool, passos médios,
distribuição de resultados) comparado ao longo do tempo para
detectar desvio que nenhum teste individual pegou. Fora por
ora: só significa algo com volume de execuções acumuladas, e
cada execução custa token. Gatilho: depois que as suítes dos
blocos 2 a 4 rodarem por um tempo e existir histórico estável.

**Geração completa de cenários por LLM.** Descrever o
comportamento esperado e deixar um LLM criar casos variados.
Fora por ora: caso gerado precisa de controle de qualidade
próprio (quem testa os testes gerados?), adiciona
não-determinismo e custo. Entrou só o nível simples, a técnica
8 (derivação mecânica do frontmatter, sem LLM). Gatilho:
escalar a cobertura para todos os agentes e caso escrito à mão
virar gargalo.

---

## 8. Técnicas futuras registradas

**Simulação de usuário multi-turn.** Um agente simulando o
usuário para exercitar conversas de vários turnos. Candidata
para `smart-planner` (planejamento interativo por perguntas) e
`devflow` (orquestração de fluxo com decisões humanas). Motivo
do registro: esses dois agentes só revelam comportamento
completo em conversa, e teste de turno único não cobre o loop
de decisão. Reavaliar depois da fase 2. Se entrar, herda P1
(o simulador lê a saída do agente como dado, nunca como ordem).

---

## 9. Descartadas, com motivo

- Red teaming adaptativo (ART, PI-Hunter, VESTA): caro,
  reprodutibilidade baixa, superfície de ataque estreita
  (harness de dev, sem usuário final).
- Guard de runtime (interceptação de tool call antes de
  executar): é defesa de produto, não teste. A camada de
  permissão do OpenCode já cumpre esse papel. Reavaliar só se
  o corpus de injection demonstrar bypass real.
- Multi-juiz com penalidade de variância: custa 3x e não ganha
  de um juiz calibrado combinado com P2.
- Benchmark de capacidade de código (opencode-bench): mede o
  modelo, não o agente configurado. O alvo aqui é papel e
  permissão.
- Observabilidade de produção (Phoenix, LangSmith, Langfuse,
  Braintrust): sem produto em produção para observar.
- OpenAI Evals e DSPy: fora de escopo.
- Bloom/Petri: geram cenários para medir propensão do modelo
  (bajulação, auto-preservação). Pesquisa de alignment, não
  teste de agente definido por config.
- Ferramentas como dependência (Inspect AI, DeepEval,
  promptfoo, AgentAssert, Agent-Harness, agentevals):
  duplicariam o harness existente ou quebrariam o stdlib-only.
  Ficam como fonte de padrão (seção 10).

---

## 10. Ferramentas candidatas (só registro, decisão posterior)

Nenhuma vira dependência no cenário atual. Registro do que
cada uma empresta de padrão, se o planejamento decidir
reimplementar por referência:

- darrenhinde/openagentscontrol (eval framework): padrão de
  execução instrumentada com observação do event stream e
  validação de tool usage, approval gate e subagente.
- agentevals (LangChain): modos de comparação de trajetória
  (idêntica, subconjunto, superconjunto, ordem).
- AgentAssert: vocabulário de asserção estilo pytest
  (`was_called`, `called_before`, `called_with`).
- Agent-Harness: asserts de porta de aprovação, exclusão mútua
  e padrão de argumento.
- promptfoo: desenho de rubrica (`llm-rubric`, `g-eval`) e a
  guarda anti-injection do juiz (P1).
- DeepEval: encaixe de métricas de julgamento em pytest.
- Inspect AI (UK AISI): log serializado com trajetória por
  avaliação (referência para o cassete da técnica 10).
- InjecAgent, AgentDojo, WASP: corpora de injection para
  adaptar casos à superfície do repo (técnica 9).
- agentpytest: padrão de cassete (gravação e replay de
  interação aprovada).

---

## 11. Restrições do repo que o planejamento precisa respeitar

- Sem `skip` em teste: pré-requisito ausente gera `pytest.fail`
  com mensagem acionável (regra já vigente no repo).
- Taxonomia da ADR-0005 preservada: markers `unit`,
  `integration`, `agent_eval`; `-m all` traduz para
  `unit or integration`.
- Toda evolução funcional cria ou atualiza testes, com
  estrutura espelhando o código (testes de bootstrap em
  `tests/scripts/bootstrap_repo/`, etc).
- Testes rodam no executável pytest do SO: `.venv/bin/pytest`
  no WSL/Linux, `.venv\Scripts\pytest.exe` no Windows.
- Docs a manter em dia: ADR nova (supera 0002 e 0003), README
  (seção de dependências e variáveis de ambiente), `AGENTS.md`
  do repo (regra do nível 3). `AGENTS.base.md` não muda.
- Commit segue Conventional Commits em PT-BR. `git push` só
  com confirmação explícita do humano.

---

## 12. Lacunas e decisões em aberto para o planejamento

1. **Escolha do provider e do modelo** (critério já definido:
   mais barato sem degradar o teste). Incluir estimativa de
   custo por execução completa da suíte: casos x N execuções x
   agentes da primeira onda.
2. **Nomes finais das env vars** (`AGENT_EVAL_ENABLED`,
   `AGENT_EVAL_BASE_URL`, `AGENT_EVAL_API_KEY`,
   `AGENT_EVAL_MODEL` são proposta) e o passthrough delas para
   dentro do container de teste.
3. **Validação da superfície do event stream** do server no
   container: formato SSE, eventos de tool call e de permissão
   disponíveis na versão usada. Plano B registrado: inferir a
   permissão da sequência de parts (tool chamada vs negada
   aparece no resultado).
4. **Calibração dos prompts de indução** (técnica 5): nível de
   pressão. Fraco demais não testa nada. Forte demais confunde
   "modelo cedeu" (correção no corpo do agente) com "config
   não aplicada" (correção em permissões). A distinção muda o
   destino do fix.
5. **N do P2 por tipo de teste**: quantas execuções e qual
   regra de consenso para trajetória, juiz e corpus.
6. **Formato da rubrica e do veredito do juiz** (técnica 7):
   estrutura do prompt do juiz, saída estruturada por critério.
   Processo de calibração: quantos exemplos rotulados, quem
   rotula, critério de aprovação (proposta inicial da conversa:
   5/5 de acordo).
7. **Corpus de injection** (técnica 9): tamanho inicial,
   formato do JSONL, proporção entre casos adaptados de
   InjecAgent/AgentDojo e casos próprios. Superfície alvo:
   conteúdo de skills externas e `UPSTREAM.md`, resultados de
   webfetch/websearch, docs de terceiros no contexto.
8. **Cassete** (técnica 10, fase 2): formato do arquivo,
   local (proposta: `tests/integration/evals/`), política de
   aceite de novo baseline, momento da gravação.
9. **Redesign do privacy enforcement** (técnica 6): injetar o
   host do provider na allowlist sem vazar credencial no
   assert. O teste continua negando todo o resto.
10. **Fronteira da camada agnóstica de harness**: conftest,
    `container_test_opencode.py` e `opencode.test.json` citam
    OpenCode hoje. Definir o que é infra do harness (pode
    citar) e o que é da suíte (não cita).
11. **Integração do bootstrap**: pergunta de habilitação,
    persistência por SO, atualização dos testes do bootstrap
    que hoje cobrem o caminho do modelo local.
12. **Fecho da lista do nível 3** no `AGENTS.md`: a lista
    inicial da seção 5 vira regra. Confirmar os itens.
13. **Ordem das fases, esforço e dependências**: sequência
    sugerida na conversa foi backend API primeiro (bloco 1),
    depois asserts determinísticos (bloco 2), juiz (bloco 3),
    corpus (bloco 4), cassete por último (fase 2). Validar e
    detalhar.
14. **Correção do achado do qa**: o corpo autoriza `websearch`
    sem declaração no frontmatter. Decidir se corrige o
    frontmatter ou o corpo, e em qual fase (candidato natural:
    junto com a onda 1, para a técnica 1 evoluída pegar).

---

## 13. Fontes da pesquisa (para reconsulta)

- darrenhinde/openagentscontrol, guia do framework de eval:
  https://github.com/darrenhinde/openagentscontrol/blob/main/evals/EVAL_FRAMEWORK_GUIDE.md
- agentevals (LangChain), avaliações de trajetória:
  https://docs.langchain.com/langsmith/trajectory-evals
- AgentAssert: https://github.com/kaushikdhola/agentassert
- Agent-Harness: https://github.com/Suirotciv/Agent-Harness
- promptfoo, guia de LLM-as-judge (rubricas e guarda do juiz):
  https://www.promptfoo.dev/docs/guides/llm-as-a-judge/
- Panorama de frameworks de eval em 2026 (Inspect, promptfoo,
  Phoenix, LangSmith, Braintrust):
  https://www.youngju.dev/blog/culture/2026-05-14-agent-evaluation-systems-2026-inspect-ai-promptfoo-phoenix-langsmith-openai-evals-deep-dive-2026.en
- Bloom (Anthropic):
  https://www.anthropic.com/news/bloom e
  https://github.com/safety-research/bloom
- Petri (Anthropic):
  https://www.anthropic.com/research/petri-open-source-auditing
- InjecAgent: https://github.com/uiuc-kang-lab/InjecAgent
- WASP (benchmark de segurança de web agents, código e dados):
  https://github.com/facebookresearch/wasp
- AgentAssay: https://github.com/qualixar/agentassay
- opencode-bench: https://github.com/anomalyco/opencode-bench
- Comparação metodológica de frameworks de eval:
  https://github.com/arbies9/state-of-llm-evals
