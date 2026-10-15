# ADR-0012: Permissões de delegação (tool task) abertas

- **Status:** Aceita
- **Data:** 2026-10-14
- **Escopo:** `harness-conf/agents/`, adapter Copilot
  (`src/opencode_config/harnesses/copilot.py`), guardas de teste
- **Revoga:** política de permissões de task fechada introduzida nos
  commits `b416dbe` e `9b185cb` (2026-09-26), incluindo a guarda que
  proibia wildcard allow

## Contexto

Os agentes globais carregavam `permission.task` com `"*": deny` mais
allowlist estática de agentes. A política nasceu como hardening contra
dois problemas: falha de spawn de agente `mode: primary` em runtime
("Unknown subagent type") e permissão ampla considerada inauditável.

O cenário de projetos consumidores não foi considerado na época. Um
projeto que adota a config global pode definir agentes próprios e
usá-los com os orquestradores (devflow, smart-planner). A allowlist
estática é texto fixo no markdown: agente fora da lista é negado, e
reiniciar o opencode não resolve. Cada agente novo de projeto
exigiria editar a config global.

O adapter Copilot materializava a allowlist no prompt ("use a
ferramenta task somente com estes agent_type"), propagando o
fechamento para o outro harness.

## Decisão

A delegação (tool task) é aberta em todos os agentes do
`harness-conf/agents/`:

1. **Bloco uniforme `"*": allow`.** Os agentes declaram
   `permission.task` com exatamente `"*": allow`, incluindo os que
   não tinham o bloco. Explícito e uniforme: não depende do default
   do opencode nem do modo de permissão da sessão.
2. **Adapter Copilot sem allowlist no prompt.** Com wildcard allow,
   a prosa de delegação instrui o uso de qualquer `agent_type`
   disponível (perfis do sync e builtins), sem enumerar lista. A
   instrução restritiva permanece no adapter para políticas fechadas
   de repositórios consumidores.
3. **Guarda anti-regressão.** O teste reprova qualquer entrada
   `deny` em `permission.task` (wildcard ou nomeada) e valida que
   allows nomeados residuais apontam para agente spawnável
   (`mode: subagent` ou `all`). A decisão fica protegida em código.
4. **Risco conhecido aceito.** Spawn de agente `mode: primary`
   continua falhando em runtime ("Unknown subagent type");
   comportamento do opencode. Os orquestradores instruem instância
   nova de executor/revisor, e o erro é claro e acionável.

### Decisão complementar: mapa de skills mantido

A política de skills (deny global em `opencode.json` + allow por
agente no frontmatter, validada por
`tests/agents/test_workflow_consistency.py`) permanece inalterada. A
abertura vale só para a delegação (tool task).

## Consequências

- Projetos consumidores podem definir agentes próprios e spawná-los
  com os orquestradores sem editar a config global.
- A allowlist estática deixa de existir; a superfície de auditoria
  passa a ser a guarda anti-regressão e esta ADR.
- A prosa do adapter Copilot para agentes com wildcard allow não
  enumera agent_type; perfil novo do sync fica automaticamente
  delegável.
- Nomes de agente `mode: primary` continuam não spawnáveis; o erro
  de runtime é o mecanismo de detecção.

## Alternativas consideradas

- Atualizar a allowlist estática com os agentes novos: rejeitada
  porque recoloca o problema a cada agente de projeto e mantém a
  config global como gargalo de mudança do consumidor.
- Abrir o wildcard só nos orquestradores e manter deny nos demais:
  rejeitada porque cria categorias de agente com política distinta;
  a decisão foi política única para todos os agentes.
- Revogar também o mapa de skills: rejeitada; o mapa atende outra
  preocupação (escopo de domínio por agente) e segue válido.

## Asserções executáveis

A fixture Concordion deste ADR expõe `executarVerificacoes()` e
`veredito`. A diretiva `execute` executa as verificações da decisão.
A diretiva `assertEquals` fixa o veredito esperado.

- [Executar as verificações deste ADR](#execute=executarVerificacoes()).
- A fixture valida a decisão implementada: nenhum agente em
  `harness-conf/agents/` declara `deny` na seção `permission.task`,
  e todo bloco `task:` declarado usa o wildcard `"*": allow`; o
  adapter Copilot emite instrução de delegação aberta quando há
  wildcard allow; a guarda anti-regressão existe em
  `tests/agents/test_task_spawnable_modes.py` e cita esta ADR.
- O veredito agregado da implementação é [pass](#assertEquals=veredito).
