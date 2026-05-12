# Graph Report - .  (2026-05-12)

## Corpus Check
- 141 files · ~119,773 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 122 nodes · 159 edges · 18 communities (10 shown, 8 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 5 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Time de Agentes Dev|Time de Agentes Dev]]
- [[_COMMUNITY_VS Code Sync (PowerShell)|VS Code Sync (PowerShell)]]
- [[_COMMUNITY_Regras Globais e Convenções|Regras Globais e Convenções]]
- [[_COMMUNITY_Prompt Improver (Avaliação)|Prompt Improver (Avaliação)]]
- [[_COMMUNITY_Crawl4AI  MCP Sanitizer|Crawl4AI / MCP Sanitizer]]
- [[_COMMUNITY_Configuração OpenCode|Configuração OpenCode]]
- [[_COMMUNITY_Framework Analyzer|Framework Analyzer]]
- [[_COMMUNITY_Servidor MCP SSE|Servidor MCP SSE]]
- [[_COMMUNITY_Bootstrap e Links Simbólicos|Bootstrap e Links Simbólicos]]
- [[_COMMUNITY_Backlog e Revisão de Histórias|Backlog e Revisão de Histórias]]
- [[_COMMUNITY_Curadoria Premissas|Curadoria: Premissas]]
- [[_COMMUNITY_Teste Integração OpenCode|Teste: Integração OpenCode]]
- [[_COMMUNITY_Padrão Upstream Skills|Padrão Upstream Skills]]
- [[_COMMUNITY_Skill doc-extract|Skill: doc-extract]]
- [[_COMMUNITY_Skill prompt-improver|Skill: prompt-improver]]
- [[_COMMUNITY_Plano Orquestrador|Plano: Orquestrador]]
- [[_COMMUNITY_Plano WSL Split|Plano: WSL Split]]

## God Nodes (most connected - your core abstractions)
1. `Workflow de Agentes — Desenvolvimento` - 13 edges
2. `Agente: Orquestrador (orq)` - 11 edges
3. `Say()` - 8 edges
4. `Ensure-Dir()` - 8 edges
5. `evaluate_prompt()` - 7 edges
6. `Backup-IfExists()` - 6 edges
7. `Sync-Skills()` - 6 edges
8. `Sync-Agents()` - 6 edges
9. `Sync-Instructions()` - 6 edges
10. `Regras Globais (AGENTS.md)` - 6 edges

## Surprising Connections (you probably didn't know these)
- `Script: vscode-sync.ps1` --references--> `Regras Globais (AGENTS.md)`  [EXTRACTED]
  scripts/bootstrap_repo/vscode-sync.ps1 → AGENTS.md
- `Skill: test-driven-development` --semantically_similar_to--> `Agente: Engenheiro de Software (eng-software)`  [INFERRED] [semantically similar]
  skills/test-driven-development/SKILL.md → agents/eng-software.md
- `Skill: security-and-hardening` --semantically_similar_to--> `Agente: Analista Cyber (sec)`  [INFERRED] [semantically similar]
  skills/security-and-hardening/SKILL.md → agents/sec.md
- `Plano: Teste Comparativo Graphify` --references--> `Workflow de Agentes — Desenvolvimento`  [EXTRACTED]
  plan/graphify-context-test.md → docs/workflow-agentes-dev.md
- `Skill: harness-catalog` --references--> `Agente: Curador de Produto (curador-produto)`  [INFERRED]
  skills/harness-catalog/SKILL.md → agents/curador-produto.md

## Hyperedges (group relationships)
- **Time de Agentes do Workflow Dev** — agent_orq, agent_eng_software, agent_curador_produto, agent_dba, agent_sec, agent_qa, agent_front, agent_rev, agent_val_harness [EXTRACTED 1.00]
- **Contratos Formais do Workflow** — contrato_mapa_produto, contrato_harness, contrato_arquivo_planejamento, contrato_verificacao_harness [EXTRACTED 1.00]
- **Scripts de Bootstrap do Repo** — script_opencode_link, script_vscode_sync, script_opencode_install_deps, script_graphify_install [INFERRED 0.90]

## Communities (18 total, 8 thin omitted)

### Community 0 - "Time de Agentes Dev"
Cohesion: 0.18
Nodes (20): Agente: Curador de Produto (curador-produto), Agente: DBA (dba), Agente: Engenheiro de Software (eng-software), Agente: Engenheiro Frontend (front), Agente: Orquestrador (orq), Agente: Testador (qa), Agente: Revisor Integrativo (rev), Agente: Analista Cyber (sec) (+12 more)

### Community 1 - "VS Code Sync (PowerShell)"
Cohesion: 0.29
Nodes (16): Adapt-SkillForVSCode(), Backup-IfExists(), Confirm-Action(), ConvertTo-WslPath(), Ensure-Dir(), Filter-AgentsMd(), Rewrite-ScriptRefs(), Say() (+8 more)

### Community 2 - "Regras Globais e Convenções"
Cohesion: 0.12
Nodes (17): Regras de Commit, Regras Globais (AGENTS.md), Seção Graphify (AGENTS.md), Regras Obrigatórias de Testes, Padrão Upstream Skills Externas, Regra Sincronização Workflow↔Agentes, Command: sync-upstream-skills, Artefato: graph.json (+9 more)

### Community 3 - "Prompt Improver (Avaliação)"
Cohesion: 0.17
Nodes (15): evaluate_clarity(), evaluate_completeness(), evaluate_context(), evaluate_prompt(), evaluate_specificity(), evaluate_structure(), generate_improvement_suggestions(), Prompt Evaluator - Scores prompts across quality dimensions (+7 more)

### Community 4 - "Crawl4AI / MCP Sanitizer"
Cohesion: 0.2
Nodes (11): apply(), clean_schema(), _patch_getdoc(), _patch_pydantic_schemas(), sanitize_mcp.py - Monkey-patch para sanitizar metadados MCP do Crawl4AI.  Proble, Patcha inspect.getdoc para retornar descriptions default quando a     funcao dec, Patcha model_json_schema das classes Pydantic usadas como input     dos endpoint, Aplica todos os monkey-patches. Chamado via sitecustomize.py. (+3 more)

### Community 5 - "Configuração OpenCode"
Cohesion: 0.18
Nodes (11): Agente: AWS Analista (aws-analista), Make target: test-unit, MCP: crawl4ai (SSE), Compaction Config (auto=false), Plugin Graphify (OpenCode), Configuração OpenCode (opencode.json), Script: graphify/install, Script: opencode-install-deps (+3 more)

### Community 6 - "Framework Analyzer"
Cohesion: 0.29
Nodes (7): analyze_use_case(), detect_intent(), get_framework_questions(), Framework Analyzer - Recommends appropriate prompting frameworks Uses intent-bas, Detect the primary intent category from a prompt.     Returns intent category an, Analyze a prompt and recommend appropriate frameworks.     Uses intent-based sel, Get clarifying questions for a specific framework.      Args:         framework_

### Community 7 - "Servidor MCP SSE"
Cohesion: 0.29
Nodes (6): app, port, server, sessionId, sessions, transport

### Community 8 - "Bootstrap e Links Simbólicos"
Cohesion: 1.0
Nodes (3): Repo: opencode-config (fonte da verdade), Script: opencode-link (bootstrap), Symlinks ~/.config/opencode/

## Knowledge Gaps
- **45 isolated node(s):** `sanitize_mcp.py - Monkey-patch para sanitizar metadados MCP do Crawl4AI.  Proble`, `Resolve todas as ocorrencias de $ref apontando para #/$defs/...     substituindo`, `Remove title de nivel raiz e de properties (nao padrao MCP).`, `Patcha inspect.getdoc para retornar descriptions default quando a     funcao dec`, `Patcha model_json_schema das classes Pydantic usadas como input     dos endpoint` (+40 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Workflow de Agentes — Desenvolvimento` connect `Time de Agentes Dev` to `Regras Globais e Convenções`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Why does `Regra Sincronização Workflow↔Agentes` connect `Regras Globais e Convenções` to `Time de Agentes Dev`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **What connects `sanitize_mcp.py - Monkey-patch para sanitizar metadados MCP do Crawl4AI.  Proble`, `Resolve todas as ocorrencias de $ref apontando para #/$defs/...     substituindo`, `Remove title de nivel raiz e de properties (nao padrao MCP).` to the rest of the system?**
  _45 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Regras Globais e Convenções` be split into smaller, more focused modules?**
  _Cohesion score 0.12 - nodes in this community are weakly interconnected._