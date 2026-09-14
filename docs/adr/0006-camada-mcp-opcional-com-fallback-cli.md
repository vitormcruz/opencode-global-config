# ADR-0006: Camada MCP opcional com fallback CLI garantido

- **Status:** Aceita
- **Data:** 2026-09-13
- **Escopo:** harnesses (OpenCode, Copilot CLI), bootstrap/adapter, skills

## Contexto

A ADR-0001 eliminou os MCPs locais e adotou CLIs nativos (AD-1). Em 13/09/2026,
revisão arquitetural avaliou readotar o modo MCP para ferramentas específicas.
Medições locais (codebase-memory 0.10.8) mostraram custo desfavorável no
OpenCode 1.x: ~5.100 tokens fixos por sessão (perfil analysis) contra
~100-150 tokens por busca via CLI (break-even ~40 buscas/sessão). A adoção
foi adiada, mas o processo de avaliação foi padronizado nesta ADR. Medições e
gatilhos de reavaliação: `plan/mcp-codebase-memory-postergado.md`.

## Decisão

O padrão permanece CLI-first. A camada MCP é opcional, por ferramenta, e
segue as decisões abaixo:

| ID | Decisão aceita |
|---|---|
| MD-1 | Toda adição de ferramenta à camada MCP exige decisão humana explícita, após avaliação de prós e contras. Nenhuma adição é automática. |
| MD-2 | Avaliação obrigatória pelos gates: G1 suporte oficial (mantido pelo próprio projeto); G2 instalação user-space fácil, sem containers/sidecars; G3 uso pelo menos tão bom quanto o CLI; G4 Windows e WSL/Linux nativos ou ponte simples. Reprovado em qualquer gate = fica só CLI. |
| MD-3 | A avaliação mede custo/benefício localmente (custo fixo de contexto por sessão vs custo por uso via CLI, break-even, ganhos de tempo e confiabilidade) e cita fonte oficial por ferramenta. |
| MD-4 | Se aprovada, o adapter/bootstrap é o escritor único das entradas MCP: seção `mcp` do `harness-conf/opencode.json` e merge gerenciado em `~/.copilot/mcp-config.json`, preservando servers definidos manualmente. O instalador nativo da ferramenta não roda. |
| MD-5 | Fallback garantido: toda ferramenta com modo MCP mantém o caminho CLI documentado na skill como plano B permanente (hierarquia: MCP > cli > grep/glob). |

## Consequências

- Nenhuma ferramenta em MCP hoje; vereditos de 13/09/2026 (playwright,
  crawl4ai, docling, pandoc, aws-cli ficam só CLI) no artefato de postergação.
- Reavaliação por gatilhos: migração para OpenCode 2.x com Code Mode, uso
  intensivo de codebase-memory por sessão, ou necessidade de descoberta de
  tools sem skill carregada.
- Skills não assumem tools MCP; mantêm invocação CLI como caminho primário
  até que uma adição específica seja aprovada.

## Alternativas rejeitadas

- Adotar MCP imediatamente nos dois harnesses: custo fixo de contexto não se
  paga no OpenCode 1.x conforme medição.
- Proibir MCP permanentemente: descarta a optionality em ambientes onde o
  custo é baixo (Copilot CLI com deferral; OpenCode 2.x com Code Mode).
- Deixar cada instalador nativo escrever as configs: conflito com a fonte de
  verdade única do repo (adapter), já rejeitado pela ADR-0004.

## Asserções executáveis

- Decisão de processo; sem testes novos obrigatórios.
- Verificação operacional em revisões: ausência de entradas MCP não aprovadas
  em `harness-conf/opencode.json` e `~/.copilot/mcp-config.json`.
