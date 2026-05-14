# Graph Report - opencode-config  (2026-05-14)

## Corpus Check
- 107 files · ~118,768 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 137 nodes · 168 edges · 22 communities (11 shown, 11 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 5 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3a66f3b0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]

## God Nodes (most connected - your core abstractions)
1. `Workflow de Agentes — Desenvolvimento` - 12 edges
2. `Agente: Orquestrador (orq)` - 11 edges
3. `Say()` - 8 edges
4. `Ensure-Dir()` - 8 edges
5. `Manutencao de Upstream — Padrao do Repo` - 7 edges
6. `evaluate_prompt()` - 7 edges
7. `Backup-IfExists()` - 6 edges
8. `Sync-Skills()` - 6 edges
9. `Sync-Agents()` - 6 edges
10. `Sync-Instructions()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `Skill: test-driven-development` --semantically_similar_to--> `Agente: Engenheiro de Software (eng-software)`  [INFERRED] [semantically similar]
  skills/test-driven-development/SKILL.md → agents/eng-software.md
- `Skill: security-and-hardening` --semantically_similar_to--> `Agente: Analista Cyber (sec)`  [INFERRED] [semantically similar]
  skills/security-and-hardening/SKILL.md → agents/sec.md
- `Plano: Teste Comparativo Graphify` --references--> `Workflow de Agentes — Desenvolvimento`  [EXTRACTED]
  plan/graphify-context-test.md → docs/workflow-agentes-dev.md
- `Skill: harness-catalog` --references--> `Agente: Curador de Produto (curador-produto)`  [INFERRED]
  skills/harness-catalog/SKILL.md → agents/curador-produto.md
- `Configuração OpenCode (opencode.json)` --references--> `Plugin Graphify (OpenCode)`  [EXTRACTED]
  opencode.json → .opencode/plugins/graphify.js

## Hyperedges (group relationships)
- **Time de Agentes do Workflow Dev** — agent_orq, agent_eng_software, agent_curador_produto, agent_dba, agent_sec, agent_qa, agent_front, agent_rev, agent_val_harness [EXTRACTED 1.00]
- **Contratos Formais do Workflow** — contrato_mapa_produto, contrato_harness, contrato_arquivo_planejamento, contrato_verificacao_harness [EXTRACTED 1.00]
- **Scripts de Bootstrap do Repo** — script_opencode_link, script_vscode_sync, script_opencode_install_deps, script_graphify_install [INFERRED 0.90]

## Communities (22 total, 11 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.18
Nodes (20): Agente: Curador de Produto (curador-produto), Agente: DBA (dba), Agente: Engenheiro de Software (eng-software), Agente: Engenheiro Frontend (front), Agente: Orquestrador (orq), Agente: Testador (qa), Agente: Revisor Integrativo (rev), Agente: Analista Cyber (sec) (+12 more)

### Community 1 - "Community 1"
Cohesion: 0.29
Nodes (16): Adapt-SkillForVSCode(), Backup-IfExists(), Confirm-Action(), ConvertTo-WslPath(), Ensure-Dir(), Filter-AgentsMd(), Rewrite-ScriptRefs(), Say() (+8 more)

### Community 2 - "Community 2"
Cohesion: 0.12
Nodes (16): Acao, Atalho: "configure este repo", code:bash (bash ./scripts/bootstrap_repo/opencode-link --yes), code:bash (mkdir -p ~/.config/opencode), COMMITS, Concisao, Configuracao Global via Links Simbolicos, Criação de Skills (+8 more)

### Community 3 - "Community 3"
Cohesion: 0.17
Nodes (15): evaluate_clarity(), evaluate_completeness(), evaluate_context(), evaluate_prompt(), evaluate_specificity(), evaluate_structure(), generate_improvement_suggestions(), Prompt Evaluator - Scores prompts across quality dimensions (+7 more)

### Community 4 - "Community 4"
Cohesion: 0.2
Nodes (11): apply(), clean_schema(), _patch_getdoc(), _patch_pydantic_schemas(), sanitize_mcp.py - Monkey-patch para sanitizar metadados MCP do Crawl4AI.  Proble, Patcha inspect.getdoc para retornar descriptions default quando a     funcao dec, Patcha model_json_schema das classes Pydantic usadas como input     dos endpoint, Aplica todos os monkey-patches. Chamado via sitecustomize.py. (+3 more)

### Community 5 - "Community 5"
Cohesion: 0.2
Nodes (10): Checklist pos-sync, code:block3 (skills/<nome>/), code:block4 (description_lang: en), Estrutura obrigatoria por skill externa, Lingua da description de skills externas, Manutencao de Upstream — Padrao do Repo, O que o UPSTREAM.md deve conter, Regra de ouro do sync (+2 more)

### Community 6 - "Community 6"
Cohesion: 0.29
Nodes (7): analyze_use_case(), detect_intent(), get_framework_questions(), Framework Analyzer - Recommends appropriate prompting frameworks Uses intent-bas, Detect the primary intent category from a prompt.     Returns intent category an, Analyze a prompt and recommend appropriate frameworks.     Uses intent-based sel, Get clarifying questions for a specific framework.      Args:         framework_

### Community 7 - "Community 7"
Cohesion: 0.25
Nodes (8): Agente: AWS Analista (aws-analista), MCP: crawl4ai (SSE), Compaction Config (auto=false), Plugin Graphify (OpenCode), Configuração OpenCode (opencode.json), Script: graphify/install, Script: opencode-install-deps, Skill: web-research-exa-crawl4ai

### Community 8 - "Community 8"
Cohesion: 0.29
Nodes (6): app, port, server, sessionId, sessions, transport

### Community 9 - "Community 9"
Cohesion: 0.33
Nodes (6): Artefato: graph.json, Artefato: GRAPH_REPORT.md, Make target: test-tools, Plano: Teste Comparativo Graphify, Skill: Graphify (Knowledge Graph), Teste: graphify-installed-test.bats

## Knowledge Gaps
- **60 isolated node(s):** `graphify — Gate Obrigatório`, `code:bash (bash ./scripts/bootstrap_repo/opencode-link --yes)`, `code:bash (mkdir -p ~/.config/opencode)`, `Concisao`, `Geração de arquivos MD` (+55 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Workflow de Agentes — Desenvolvimento` connect `Community 0` to `Community 9`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Why does `Upstream de Skills Externas` connect `Community 5` to `Community 2`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **What connects `graphify — Gate Obrigatório`, `code:bash (bash ./scripts/bootstrap_repo/opencode-link --yes)`, `code:bash (mkdir -p ~/.config/opencode)` to the rest of the system?**
  _60 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.12 - nodes in this community are weakly interconnected._