# MCP do codebase-memory: decisão postergada

Este artefato registra por que a adoção do modo MCP do codebase-memory-mcp
foi adiada e o que deve ser reavaliado quando os gatilhos abaixo ocorrerem.
Fonte: ciclo de planejamento concluído em 13/09/2026 (plano de atualização de
libs do bootstrap, removido após conclusão).

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
