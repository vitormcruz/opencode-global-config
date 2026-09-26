# Metadados do Upstream

plugin: opencode-task-model (npm)
versao_pinada: 1.3.1
repositorio: https://github.com/lars-hagen/opencode-task-model
commit: baedc8977fb16127016ca6cbf4a772e9e9693be2 (tag v1.3.1)
data_commit: 2026-07-30 02:38:11 +0200
revisado_em: 2026-09-26
decisao: GO (nenhum finding bloqueante)

## Conteúdo do pacote (tarball npm 1.3.1)

- LICENSE (MIT, Copyright (c) 2026 Lars Hagen)
- package.json (sem dependências de runtime; `sideEffects: false`; sem hooks
  pre/post-install)
- src/index.ts (868 linhas: override da tool `task`)
- scripts/opencode-config.js (50 linhas: conveniência do mantenedor)
- README.md

## Paridade tarball npm ↔ repo upstream

Comparado `npm pack opencode-task-model@1.3.1` com `git show v1.3.1:<arquivo>`
do repo: os 5 arquivos são idênticos, byte a byte. Nada no tarball diverge do
commit revisado.

## Findings da revisão de segurança

Lido na íntegra: `src/index.ts`, `scripts/opencode-config.js`,
`package.json`, `README.md` e workflow de publish (`.github/workflows/
publish.yml` na tag v1.3.1).

Bloqueantes: nenhum.

- `src/index.ts`: sem `import` nenhum (zero dependências). Todo tráfego de
  rede passa pelo client do OpenCode (`client.session.*`, `client.app.agents`,
  `client.config.get`, `client.tui.showToast`), que fala com o servidor local.
  O único PATCH usa o próprio SDK HTTP (`client._client`) contra rota relativa
  `/session/{id}/message/{messageID}/part/{partID}`. Sem `child_process`, sem
  `fs`, sem `fetch` para hosts externos, sem URLs externas, sem escrita em
  disco fora da API do OpenCode.
- Permissões do subagente: foreground herda as deny rules da sessão pai e
  nega `task`/`todowrite`/`primary_tools` não declarados; background usa
  sandbox deny-all exceto `read`/`glob`/`grep`/`webfetch`. `verifyChildSession`
  revalida no servidor que as regras foram preservadas; `enforceSubagentDepth`
  limita aninhamento; `authorizeTask` passa pelo fluxo `ctx.ask` de permissões.
- `scripts/opencode-config.js`: roda apenas sob invocação manual
  (`bun run opencode:local` / `opencode:install`); edita o `opencode.json` do
  usuário substituindo a entrada do plugin e, no modo npm, consulta a versão
  no registry. Não é executado pelo OpenCode.
- Publish workflow: disparado só por tag; npm OIDC trusted publishing (sem
  token armazenado); valida tag = `package.json` version.

Riscos aceitos e mitigados (nenhum impede a adoção):

- O plugin sobrescreve a tool `task` nativa para todos os agentes (é o
  propósito). Mitigação: pin exato no `opencode.json`, status PROVISÓRIO,
  deny rules do config como kill switch, remoção documentada no README.
- `background: true` permite `webfetch` no sandbox do child. Mitigação:
  guarda no `AGENTS.base.md` (usar só com escopo aprovado, preferindo
  `worktree`/foreground para escrita).
- Projeto de mantenedor único e baixa adoção; HEAD já tem um commit grande
  (`b66ff17`, 2026-09-04, controles de subagente + TUI) ainda sem release npm.
  Mitigação: pin na 1.3.1; nova revisão obrigatória antes de qualquer bump.

## Rastreio do suporte nativo (confirmado em 2026-09-26 via API GitHub)

- Issue `anomalyco/opencode#6651`: "[FEATURE]: Dynamic model selection for
  subagents via Task tool". Open, assignee `thdxr`, criada 2026-01-02,
  atualizada 2026-09-17.
- PR `anomalyco/opencode#34947`: "feat(opencode): add dispatch controls to
  the task tool". Open, NÃO mergeado (atualizado 2026-09-25). Fecha #17595 e
  cobre #6651, #26925, #29984. Adiciona `model`/`variant` gated pela permissão
  `model_override` (default deny). Supersede #29447 e #32122.
- Issue `anomalyco/opencode#17595`: "[FEATURE]: Runtime model override for
  task tool subagents". Confirmada, referenciada pelo PR #34947.
- Outros PRs concorrentes em review, sem merge: #11377 (model tiers),
  #31694, #35800.

Remover o plugin quando qualquer implementação nativa de `model` na `task`
for mergeada e lançada; o procedimento está na seção "Plugins" do README.

## Como atualizar

1. Reexecutar esta revisão de segurança na nova versão (ler o tarball novo,
   comparar com o commit da tag correspondente, refazer os findings).
2. Atualizar `versao_pinada` e `commit` aqui.
3. Atualizar o pin em `harness-conf/opencode.json` e a versão na seção
   "Plugins" do `README.md`.
4. Rodar `.venv/bin/pytest -m all`.

Sem comando de sync automatizado: o repo não versiona o código do plugin,
apenas este registro e o pin.
