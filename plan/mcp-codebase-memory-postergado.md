# MCP do codebase-memory: decisão postergada

Este artefato registra por que a adoção do modo MCP do codebase-memory-mcp
foi adiada e o que deve ser reavaliado quando os gatilhos abaixo ocorrerem.
Fonte: ciclo de planejamento concluído em 13/09/2026 (plano de atualização de
libs do bootstrap, removido após conclusão).

O processo da seção "Como avaliar novas ferramentas via MCP" vale para
QUALQUER ferramenta, não só para o codebase-memory.

## Contexto

O repo usa o codebase-memory em CLI mode (`codebase-memory-mcp cli <tool>
'<json>'` via Bash), com instalação user-space via npm (pin 0.10.8). Uma
revisão arquitetural avaliou migrar para o modo MCP (tools nativas do
harness) nos dois harnesses (OpenCode e Copilot CLI).

## Decisões do ciclo

- Só o codebase-memory-mcp passaria nos gates para a camada MCP. Vereditos:
  playwright fica só CLI (a própria Microsoft endossa CLI+skills para coding
  agents; MCP para "specialized agentic loops" com custo de token maior);
  crawl4ai fica só CLI (MCP virou oficial, mas exige server Docker na porta
  11235); docling fica só CLI (MCP oficial existe; uso esporádico não
  justifica processo residente; reavaliar se doc-extract virar fluxo
  frequente); pandoc fica só CLI (sem MCP oficial); aws-cli fica só CLI
  (skills do repo giram em torno de SSO login interativo, que pertence ao
  CLI).
- Gates usados (mantidos para futuras reavaliações): G1 suporte oficial;
  G2 instalação user-space fácil (sem containers/sidecars); G3 uso tão bom
  quanto o CLI; G4 Windows e WSL/Linux nativos ou ponte simples.
- Adoção do MCP: ADIADA. Foco do momento: consistência do uso do CLI.

## Por que foi adiado (medições locais, 13/09/2026)

- OpenCode 1.x (versão em uso): tools MCP entram no contexto com schema
  completo. Custo fixo por sessão: ~6.100 tokens (15 tools) ou ~5.100
  (perfil analysis, 11 tools).
- Busca via CLI custa ~100-150 tokens (comando + saída JSON compacta; busca
  típica: comando de 122 bytes + saída de 276 bytes).
- Break-even do MCP: ~40 buscas na mesma sessão. Sessões típicas ficam muito
  abaixo; o custo fixo do MCP não se paga em tokens.
- Copilot CLI: tem deferral/tool-search (custo real baixo e quase fixo);
  OpenCode 2.x: Code Mode default (catálogo orçado + busca sob demanda).
  Nestes ambientes o MCP fica competitivo.

## Gatilhos de reativação

1. Migração para OpenCode 2.x com Code Mode (verificar `codemode: true` na
   doc/config da versão em uso).
2. Uso do codebase-memory em sessões intensivas de exploração (dezenas de
   buscas por sessão) onde o ganho de tempo do daemon (cold start de 1-3s por
   comando CLI) pese mais que o custo fixo.
3. Necessidade de descoberta de tools sem depender da skill carregada.

## Design já validado (se reativar)

- Fallback híbrido: adapter/bootstrap materializa a entrada MCP
  (`harness-conf/opencode.json` seção `mcp`; merge gerenciado em
  `~/.copilot/mcp-config.json` preservando servers manuais). O subcomando
  `install` nativo do CBM NÃO roda (fonte de verdade única do repo). A skill
  mantém o CLI como plano B permanente.
- Perfil recomendado na ocasião: analysis (11 tools; mantém tudo que a skill
  code-explorer-priority usa; corta as 4 de manutenção). Perfis medidos:
  completo 15 tools / ~6.100 tokens; analysis 11 / ~5.100; scout 7 / ~3.400
  (scout corta query_graph e search_code, que a skill usa).
- Se ativar no OpenCode 1.x: considerar restrição por glob (`tools` na config)
  ou por agente (`agent.<nome>.tools`).

## Como avaliar novas ferramentas via MCP (processo permanente)

Princípio aprovado no ciclo de 13/09/2026: o padrão-arquitetura é MCP com
fallback CLI garantido, mas TODA adição de ferramenta à camada MCP depende de
decisão humana explícita, após avaliação de prós e contras. Nenhuma adição é
automática. Passos obrigatórios:

1. **Gates G1-G4** (reprovado em qualquer um = fica só CLI):
   G1 suporte oficial (mantido pelo próprio projeto, não comunidade);
   G2 instalação user-space fácil (sem containers/sidecars);
   G3 uso pelo menos tão bom quanto o CLI atual;
   G4 Windows e WSL/Linux nativos, ou ponte simples.
2. **Medição local de custo/benefício** antes de decidir (modelo aplicado ao
   CBM em 13/09/2026, reutilizar): custo fixo de contexto por sessão com
   schemas (ou catálogo/deferral, conforme o harness), custo por uso via
   CLI, break-even em número de usos por sessão, ganhos de tempo
   (daemon/cold start) e de confiabilidade (schema validado).
3. **Veredito com fonte oficial** citada por ferramenta (repo/docs do
   projeto, não fontes secundárias).
4. **Se aprovada pelo humano**, aplicar o design já validado: fallback
   híbrido com o adapter/bootstrap como escritor único das entradas MCP
   (`harness-conf/opencode.json` seção `mcp`; merge gerenciado em
   `~/.copilot/mcp-config.json` preservando servers manuais); instalador
   nativo da ferramenta não roda; a skill da ferramenta mantém o CLI
   documentado como plano B permanente (hierarquia: MCP > cli > grep/glob).
5. **Registrar a decisão** (neste artefato ou em plano próprio) com
   veredito, medições, data e gatilhos de reavaliação.

## Insumos técnicos úteis

- Daemon de coordenação: com MCP, o CBM sobe o daemon na primeira sessão
  (watchers, indexação compartilhada, sem cold start). O modo cli é
  intencionalmente local (nunca conecta ao daemon), por design upstream.
- Perfis do servidor: `--tool-profile=analysis|scout` reduz a superfície
  reportada no `tools/list` (vale para qualquer cliente).
- Configs observadas na 0.10.8 (`config list`): `auto_index=true`,
  `auto_watch=true`, `auto_index_limit=50000`, `ui-lang=auto`,
  `ui_enabled=true`, `ui_port=9749`. Nota: `watcher_enabled`, documentado no
  README upstream, não existe nesta build.
