# Plano: Experimento — Plataformas e Frameworks para UI com Painéis Dinâmicos

> STATUS: SPIKES 1, 2 E 3 CONCLUÍDOS E APROVADOS (2026-09-11: executor
> concluiu, revisor independente aprovou sem achados bloqueantes, humano
> validou visualmente no browser — persistência e painéis dinâmicos com
> backend real confirmados). Decisão de rumo pendente: encerrar o
> experimento declarando o Dockview aprovado como base do cockpit, ou
> spike 4 (challenger).

## Overview

Experimento comparativo para escolher plataforma e framework para uma tela
com múltiplas seções/janelas dinâmicas:
- painéis criados/removidos em runtime, conforme necessidade;
- conteúdo por painel heterogêneo: HTML, texto puro, Markdown, SVG, imagem,
  diagramas Mermaid — permissivo, "qualquer coisa";
- processo iterativo: planejar → implementar spike → avaliar → ajustar ou
  tentar outra abordagem;
- decisões podem exigir estudo prévio do humano (ensino, prompt para agente
  professor, ou links).

Localização do plano: `plan/experimento-paineis-dinamicos.md` no repo
`opencode-global-config`. Antes da aprovação viveu em `/tmp/opencode`
(repo em mutação simultânea; localização final ajustada após o término
daquele trabalho, conforme combinado).

## Architecture Decisions

- **D1 — Uso final:** cockpit pessoal do próprio humano, ligado ao contexto
  do projeto `opencode-global-config`. Ferramenta interna: sem requisitos de
  multiusuário, autenticação ou distribuição como produto.
- **D2 — Escopo de plataformas:** apenas web (browser). Desktop
  (Electron/Tauri) e TUI ficam fora do experimento.
- **D3 — Repositório dos spikes:** repo Git separado, público no GitHub do
  humano. Este plano permanece fora do repo `opencode-global-config`
  (localização final a ajustar depois).
- **D4 — Critério principal:** flexibilidade — criar/remover painéis em
  runtime e suportar conteúdo heterogêneo (HTML, texto, MD, SVG, imagem,
  Mermaid, "qualquer coisa").
- **D5 — Processo de seleção:** planejador pesquisa na web e retorna
  shortlist comparativa + links para o humano estudar, antes de decidir.
  Vaadin é o candidato preferido do humano, condicionado a atender os
  requisitos (painéis dinâmicos + conteúdo heterogêneo).
- **D6 — Paradigma de UI:** docking IDE-style (janelas com tabs, splits
  livres, painéis flutuantes, popout — estilo VS Code), em vez de dashboard
  grid. Consequência: **Dockview** passa a ser a lib líder do experimento;
  Vaadin Dashboard (grid) não atende esse paradigma como base.
- **D7 — Vaadin:** descartado do experimento. O candidato preferido inicial
  não atende o paradigma docking escolhido; não haverá spike via Hilla.
- **D8 — Framework base do spike 1:** React + `dockview-react`.
- **D9 — Escopo do spike 1:** criar/remover painéis em runtime + renderers
  de conteúdo: texto puro, Markdown, Mermaid, SVG inline, imagem e HTML
  arbitrário via `iframe sandbox`. Persistência de layout e backend
  dinâmico ficam para spikes seguintes.
- **D10 — Nome do repo:** `painel-dinamico-lab`, público, na conta
  `vitormcruz`. Push autorizado pelo humano (D3) neste repo, sem nova
  confirmação por push.
- **D11 — Localização do plano:** `plan/experimento-paineis-dinamicos.md`
  no repo `opencode-global-config`, aprovada após o término do trabalho
  paralelo que motivou o isolamento em `/tmp/opencode`.

## Research Notes

### Shortlist pós-pesquisa (2026-09-06)

Dois paradigmas distintos de "painéis dinâmicos" emergiram:

**A) Dashboard grid (widgets em grade):**
- **Vaadin Dashboard** — componente oficial, estável desde 24.8, presente na
  25.x. Editável pelo usuário: drag & drop, resize, remover widgets,
  persistir/carregar configuração, WCAG AA. Estilo Grafana, não IDE.
  Docs: https://vaadin.com/docs/latest/components/dashboard
  Atenção: componente do plano Pro (verificar licença/custo para uso pessoal).
- **Vaadin Markdown** — renderiza MD nativamente (sanitizado).
  Docs: https://vaadin.com/docs/latest/components/markdown
- **Mermaid no Vaadin:** sem suporte oficial atual; só add-on de 2017 para
  Vaadin 7 (https://vaadin.com/directory/component/component/mermaid).
  Integração moderna exige wrapper custom (executar mermaid.js no cliente).

**B) Docking IDE-style (janelas, tabs, splits, floating):**

Levantamento completo da categoria (2026-09-06), por maturidade:

*Maduras/ativas:*
- **Dockview** — zero-dep, TS puro, bindings React/Vue/Angular/vanilla,
  v8.x ativa, MIT no core. Tabs, drag & drop, floating, popout,
  serialização. https://dockview.dev
- **FlexLayout** (caplin) — React-only, ativo, MIT. Tabsets ricos,
  borders, popout, submodels. https://github.com/caplin/FlexLayout
- **Lumino** (@lumino/widgets, do JupyterLab) — vanilla TS, robusto,
  API de baixo nível. Base do JupyterLab.
  Wrapper novo de alto nível: **dock-it** (dufeutech).
- **rc-dock** (ticlo) — React, ~811 stars, alfa 4.0.0-alpha.2 (~1 ano
  sem release estável). Apache-2.0.
- **Golden Layout** — 6.7k stars, referência histórica, sem release
  desde ~2022. Estagnado.
- **dock-spawn-ts** (node-projects) — fork TS do dock-spawn, ~146 stars,
  commits recentes. Visual Studio-style.

*Novatas (menor adoção, acompanhar):*
- **dockmanager** (widgetstools) — zero-dep, React/Angular, <30KB,
  undo/redo, auto-hide strips, 14 temas.
  https://github.com/widgetstools/dockmanager
- **react-dockable-desktop** — React, zero-unmount (DOM movido, não
  destruído), floating rico.
- **Apane** — framework-agnostic, split/stack, runtime API rica.
- **tilery** (yangshun) — tiling layout, core agnóstico + React adapter.
- **react-splitkit** — headless React primitives.
- **dynamix-layout** — core TS + React/Solid.
- **WinBox** — só janelas flutuantes (não docking completo).

No paradigma B, o conteúdo de cada painel é 100% responsabilidade do app:
qualquer renderer (markdown-it, mermaid, iframe sandbox, img, SVG inline)
cabe sem limitação da lib.

**Backend dinâmico:** confirmado que todas as libs permitem conteúdo
alimentado por backend — cada painel é um componente que faz fetch de API
REST, WebSocket ou SSE e re-renderiza. O layout manager não restringe.

## Task List

Contexto de execução: repo NOVO (`painel-dinamico-lab`), fora do repo
`opencode-global-config`. As regras de teste do repo de configs NÃO se
aplicam aqui — a validação do spike é visual/manual + build.

### Phase 1 — Fundação

- [x] **Task 1: Criar repo e scaffold Vite + React + TS**
  - **Description:** criar repo público `vitormcruz/painel-dinamico-lab`
    via `gh repo create` (o gh já está autenticado), clonar em diretório
    de trabalho do humano (fora do repo de configs), scaffold
    `npm create vite@latest . -- --template react-ts`, commit inicial
    (Conventional Commits PT-BR) e push.
  - **Acceptance criteria:**
    - [ ] repo público acessível no GitHub
    - [ ] `npm run dev` sobe o app React default
    - [ ] `npm run build` passa
    - [ ] README curto com objetivo do lab
  - **Verification:** `gh repo view vitormcruz/painel-dinamico-lab`;
    `npm run build` local.
  - **Dependencies:** None
  - **Files likely touched:** scaffold Vite (`package.json`, `index.html`,
    `src/App.tsx`, `src/main.tsx`), `README.md`
  - **Estimated scope:** S

- [x] **Task 2: Integrar Dockview com docking básico**
  - **Description:** instalar `dockview-react`, trocar o `App` por
    `DockviewReact` com registry de componentes, criar 2 painéis demo
    (texto estático), tema dark, altura 100vh.
  - **Acceptance criteria:**
    - [ ] grid docking renderiza com 2 painéis em split
    - [ ] drag & drop entre painéis funciona no browser
    - [ ] fechar painel (X) funciona
    - [ ] `npm run build` passa
  - **Verification:** validação manual no browser (dev server) + build.
  - **Dependencies:** Task 1
  - **Files likely touched:** `src/App.tsx`, `src/main.tsx` (import css),
    `package.json`
  - **Estimated scope:** S

### Checkpoint: Fundação (commit + push)
- [ ] App roda com docking nativo do Dockview (mover/fechar painéis)
- [ ] Commits atômicos por task; push autorizado (D10)

### Phase 2 — Renderers de conteúdo

- [x] **Task 3: Painéis Texto e Markdown**
  - **Description:** componente `PainelTexto` (bloco monoespaçado) e
    `PainelMarkdown` com `react-markdown` e conteúdo demo rico (headings,
    listas, code block, tabela, blockquote).
  - **Acceptance criteria:**
    - [ ] painel texto exibe texto plano em `<pre>` com wrap
    - [ ] painel MD renderiza headings, listas, code e tabela
    - [ ] build passa
  - **Verification:** manual no browser + build.
  - **Dependencies:** Task 2
  - **Files likely touched:** `src/paineis/Texto.tsx`,
    `src/paineis/Markdown.tsx`, registry em `src/App.tsx`
  - **Estimated scope:** S

- [x] **Task 4: Painel Mermaid**
  - **Description:** `PainelMermaid` usando o pacote `mermaid` npm.
    Render assíncrono (`mermaid.render` ou `mermaid.initialize` + API),
    diagrama demo (flowchart), tema dark, cuidado com re-render
    (cleanup + id único) para não duplicar SVG.
  - **Acceptance criteria:**
    - [ ] flowchart Mermaid renderiza como SVG no painel
    - [ ] re-render (StrictMode double-render) não duplica nem quebra
    - [ ] build passa
  - **Verification:** manual no browser (diagrama visível) + build.
  - **Dependencies:** Task 2
  - **Files likely touched:** `src/paineis/Mermaid.tsx`
  - **Estimated scope:** S

- [x] **Task 5: Painéis SVG e Imagem**
  - **Description:** `PainelSvg` (SVG inline demo, escalável) e
    `PainelImagem` (img com asset LOCAL — sem dependência de rede).
  - **Acceptance criteria:**
    - [ ] SVG renderiza e escala com o resize do painel
    - [ ] imagem local carrega no painel
    - [ ] build passa
  - **Verification:** manual no browser (resize do painel) + build.
  - **Dependencies:** Task 2
  - **Files likely touched:** `src/paineis/Svg.tsx`, `src/paineis/Imagem.tsx`,
    `src/assets/` (imagem demo)
  - **Estimated scope:** S

- [x] **Task 6: Painel HTML arbitrário (iframe sandbox)**
  - **Description:** `PainelHtml` com `iframe sandbox` (`srcdoc`),
    conteúdo demo com CSS + JS simples (ex.: botão que muda cor). Sandbox
    SEM `allow-same-origin` para isolar do app host; `allow-scripts` ok
    (é ferramenta pessoal, risco aceito por design).
  - **Acceptance criteria:**
    - [ ] HTML demo renderiza e o JS executa dentro do iframe
    - [ ] script do iframe não acessa o DOM do app host
    - [ ] build passa
  - **Verification:** manual no browser (interagir com o demo) + build.
  - **Dependencies:** Task 2
  - **Files likely touched:** `src/paineis/Html.tsx`
  - **Estimated scope:** S

### Checkpoint: Renderers (commit + push)
- [ ] Os 6 tipos de conteúdo renderizam corretamente
- [ ] Drag & drop continua funcionando com todos os tipos

### Phase 3 — Dinâmica de painéis

- [x] **Task 7: Criar/remover painéis em runtime**
  - **Description:** toolbar (dropdown "+ Adicionar painel") que chama
    `api.addPanel` com o tipo escolhido e conteúdo demo; remoção pelo
    fechar nativo do painel. Registry central
    `tipo → componente + params demo`.
  - **Acceptance criteria:**
    - [ ] é possível adicionar painéis de cada um dos 6 tipos em runtime
    - [ ] é possível remover qualquer painel pelo X nativo
    - [ ] na mesma sessão: arrastar painéis não perde conteúdo
    - [ ] build passa
  - **Verification:** manual no browser — adicionar vários painéis de
    tipos misturados, arrastar, fechar, repetir.
  - **Dependencies:** Tasks 3, 4, 5, 6
  - **Files likely touched:** `src/App.tsx` (toolbar + registry),
    `src/paineis/registry.ts`
  - **Estimated scope:** M

### Checkpoint: Spike 1 completo (commit + push)
- [x] Fluxo completo: adicionar painéis de qualquer tipo, misturar,
      arrastar, fechar
- [x] Humano avalia o resultado e decide: aprovar, ajustar ou tentar
      abordagem diferente (processo iterativo, D5)
      → VALIDADO EM 2026-09-11: revisor aprovou sem achados; humano
      aprovou visualmente ("ficou tudo muito bom").
      Repo: https://github.com/vitormcruz/painel-dinamico-lab

### Phase 4 — Spike 2: persistência de layout

- [x] **Task 8: Persistir e restaurar layout**
  - **Description:** serializar o layout (`api.toJSON`) no localStorage a
    cada mudança (`onDidLayoutChange`, com debounce leve); no boot, se
    houver layout salvo, aplicar via `fromJSON`; senão, layout default.
    Botão "Restaurar padrão" que limpa o storage e aplica o default.
    Fallback: se `fromJSON` falhar (schema mudou / JSON corrompido),
    cair no default sem quebrar o app.
  - **Acceptance criteria:**
    - [ ] layout (posição/tamanho/tabs) sobrevive ao reload do browser
    - [ ] conteúdo dos painéis recriado correto após reload (params
          preservados no JSON serializado)
    - [ ] "Restaurar padrão" volta ao layout inicial
    - [ ] JSON corrompido/incompatível não quebra o app (fallback)
    - [ ] `npm run build` passa
  - **Verification:** reload do browser recria o layout; build.
  - **Dependencies:** Task 7
  - **Files likely touched:** `src/App.tsx` (ou hook de persistência),
    `src/paineis/registry.ts`
  - **Estimated scope:** M

### Checkpoint: Spike 2 (commit + push)
- [x] Persistência validada; commits atômicos; push (D10)
      → VALIDADO EM 2026-09-11: reload do browser e restart do dev
      server preservam o layout (humano confirmou).

### Phase 5 — Spike 3: backend dinâmico real (FastAPI)

- [x] **Task 9: Backend FastAPI com dados reais do contexto opencode**
  - **Description:** criar `backend/` no repo do lab com FastAPI +
    uvicorn. Endpoints: `GET /api/estado` (contagens REAIS lidas em
    runtime do repo `opencode-global-config`: skills, agents, commands,
    testes — leitura de diretórios, nada hardcoded), `GET /api/markdown`
    (serve um .md real do repo de configs, ex.: README, como texto) e
    `GET /api/stream` (SSE empurrando payload com timestamp + resumo do
    estado a cada 2s). Acesso do frontend via proxy do Vite
    (`server.proxy` `/api` → `localhost:8000`), sem hack de CORS.
    Dependências pinadas em `backend/requirements.txt`.
  - **Acceptance criteria:**
    - [ ] uvicorn sobe na porta 8000 e os 3 endpoints respondem
    - [ ] `/api/estado` retorna contagens reais do repo de configs
    - [ ] `/api/stream` mantém conexão SSE e emite eventos periódicos
    - [ ] proxy do Vite encaminha `/api` sem CORS manual
    - [ ] `npm run build` passa
  - **Verification:** `curl` nos endpoints com uvicorn no ar (SSE com
    timeout curto); build.
  - **Dependencies:** Task 8
  - **Files likely touched:** `backend/main.py`, `backend/requirements.txt`,
    `vite.config.ts`
  - **Estimated scope:** M

- [x] **Task 10: Painéis dinâmicos consumindo o backend**
  - **Description:** 3 novos tipos no registry: `PainelEstado` (fetch
    `/api/estado`, render em tabela/JSON, botão atualizar), `PainelDoc`
    (fetch `/api/markdown`, render via react-markdown) e `PainelLive`
    (EventSource `/api/stream`, atualização em tempo real do último
    evento). Todos entram na toolbar de adicionar (total: 9 tipos).
    Erros de rede (backend fora do ar) com estado de erro amigável.
  - **Acceptance criteria:**
    - [ ] painel estado mostra contagens reais e atualiza sob demanda
    - [ ] painel doc renderiza o MD servido pelo backend
    - [ ] painel live atualiza em tempo real sem refresh manual (SSE)
    - [ ] backend fora do ar → estado de erro amigável nos painéis
    - [ ] 3 novos tipos na toolbar; `npm run build` passa
  - **Verification:** uvicorn + dev server no ar; validação manual no
    browser + build.
  - **Dependencies:** Task 9
  - **Files likely touched:** `src/paineis/Estado.tsx`, `src/paineis/Doc.tsx`,
    `src/paineis/Live.tsx`, `src/paineis/registry.ts`, `src/App.tsx`
  - **Estimated scope:** M

### Checkpoint: Spikes 2+3 completos (commit + push)
- [x] Reload preserva layout; painéis consomem backend real
- [x] Revisão única do revisor (ritmo escolhido pelo humano: uma tacada)
      → APROVADO sem achados bloqueantes (2026-09-11)
- [x] Humano avalia no browser
      → VALIDADO EM 2026-09-11: "funcionou, perfeito". Painéis Estado,
      Doc e Live operando com backend FastAPI real; persistência
      confirmada após restart do dev server.

### Spikes futuros (backlog)
- Spike 4 (condicional): challenger (FlexLayout ou novatas) se algo
  incomodar no Dockview

## Execução

- **Executor:** agente `worker` (nativo do OpenCode) com modelo
  `gpt-5.6-luna`, variante `max` (esforço MAX — não `high`, não `xhigh`).
  Referência no frontmatter: `opencode/gpt-5.6-luna#max` (provider Zen;
  alternativa `opencode-go` pendente de confirmação do humano).
- **Revisor:** agente `revisor` (nativo do OpenCode), modelo mantido:
  `zai-coding-plan/glm-5.3`, temperature 0.1, sem permissão de edição.
- A tool `task` não aceita modelo no spawn: os modelos vêm dos frontmatters.
  Para trocar, editar o frontmatter e reiniciar o OpenCode.
- Reutilizar estas escolhas em novas instâncias até o humano alterá-las.
- **LLM no lab (condicional):** se qualquer parte do lab precisar chamar
  um modelo (não há necessidade no escopo dos spikes 2-3), usar
  `opencode-go/deepseek-v4-flash` (provider `opencode-go`, escolha e
  confirmação do humano).

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Mermaid render async + React StrictMode duplica SVG | Médio | useEffect com cleanup e id único por render; testar c/ StrictMode on |
| Exemplos antigos do Dockview (v2–v5) não baterem com v8 | Médio | Usar só docs atuais de dockview.dev; API `onReady` + `api.addPanel` |
| iframe sandbox vazar para o app host | Baixo | sandbox sem `allow-same-origin`; conteúdo pessoal, risco aceito |
| Popout windows bloqueadas por popup blocker | Baixo | Popout fora do escopo do spike 1 |
| Dependência de rede para assets demo | Baixo | Assets locais (`src/assets/`) |
| Repo público com conteúdo irrelevante/ruim | Baixo | README claro; é um lab público proposital |

## Open Questions

- Critérios formais de avaliação comparativa entre libs (só relevantes se
  o spike 4 challenger acontecer).
- Backend do spike 3: qual servidor e formato (mock local vs endpoints reais
  do contexto opencode).
