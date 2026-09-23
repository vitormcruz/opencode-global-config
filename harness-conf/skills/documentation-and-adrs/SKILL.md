---
name: documentation-and-adrs
description: >
  Use ao tomar decisão arquitetural relevante, escolher entre abordagens
  concorrentes, adicionar ou alterar API pública, entregar feature que muda
  comportamento visível ao usuário, ou integrar novos membros e agentes ao
  time. Documenta o porquê das decisões, não só o quê (ADRs, CHANGELOG,
  docs técnicas).
  Triggers: "ADR", "architectural decision record", "decision record",
  "document this decision", "why did we", "trade-offs", "alternatives
  considered", "CHANGELOG", "technical docs", "onboarding docs", "README",
  "record decision", "context for future engineers", "decision log",
  "docs/adr/", "runbook", "system design doc".
---

# Documentação e ADRs

Documente decisões, não só código. Código mostra o que foi construído;
documentação captura o porquê: contexto, restrições e trade-offs que
levaram à decisão. É esse contexto que orienta humanos e agentes futuros
no codebase.

## Documentação inline

Comente o porquê, nunca o quê:

```typescript
// Ruim: repete o código
// Incrementa o contador em 1
counter += 1;

// Bom: explica intenção não óbvia
// Rate limit usa janela deslizante: reset na borda da janela,
// não em cronograma fixo, para impedir rajada nas bordas
if (now - windowStart > WINDOW_SIZE_MS) {
  counter = 0;
  windowStart = now;
}
```

- Não deixe TODO do que deve ser feito agora: faça agora.
- Não deixe código comentado: delete (o git guarda o histórico).
- Gotcha conhecido? Documente inline, onde importa:

```typescript
/**
 * Chamar antes do primeiro render; depois da hidratação causa flash
 * de conteúdo sem estilo (theme context indisponível no SSR).
 * Rationale completo: ADR-003.
 */
export function initializeTheme(theme: Theme): void {
  // ...
}
```

## ADRs

Escreva ADR para decisão técnica cara de reverter: escolha de framework
ou dependência relevante, modelagem de dados, estratégia de
autenticação, arquitetura de API (REST vs GraphQL vs tRPC), ferramentas
de build, hosting e infraestrutura.

Guarde em `docs/decisions/` com numeração sequencial:

```markdown
# ADR-001: PostgreSQL como banco primário

## Status
Accepted | Superseded by ADR-XXX | Deprecated

## Date
2026-01-15

## Context
Requisitos e restrições que motivam a decisão.

## Decision
A decisão tomada.

## Alternatives Considered
Para cada alternativa: prós, contras e motivo da rejeição.

## Consequences
Efeitos práticos da decisão.
```

Ciclo: `PROPOSED → ACCEPTED → (SUPERSEDED ou DEPRECATED)`.

- Nunca delete ADR antigo: ele é o contexto histórico.
- A decisão mudou? Escreva um novo ADR que cita e substitui o anterior.

## APIs públicas

- TypeScript: documentação inline junto dos tipos (`@param`, `@returns`,
  `@throws`, `@example`).
- REST: spec OpenAPI/Swagger como fonte única do contrato.

## README

Todo projeto cobre, nesta ordem: descrição de um parágrafo; Quick Start
(clone, install, env, run); tabela de comandos; arquitetura com links
para os ADRs; contribuição (padrões de código, fluxo de PR).

## CHANGELOG

Para features entregues, formato Keep a Changelog, com data de release e
referência do issue:

```markdown
## [1.2.0] - 2026-01-20
### Added
- Task sharing entre membros do time (#123)
### Fixed
- Tasks duplicadas ao clicar rápido em criar (#125)
```

## Documentação para agentes

- **CLAUDE.md / rules files**: convenções do projeto que o agente segue.
- **Specs**: mantenha atualizadas para o agente construir o certo.
- **ADRs**: evitam re-decidir o que já foi decidido.
- **Gotchas inline**: impedem o agente de cair em armadilha conhecida.

## Anti-racionalizações

| Racionalização | Realidade |
|---|---|
| "O código é autodocumentado" | Código mostra o quê; não o porquê, as alternativas rejeitadas nem as restrições. |
| "Escrevo docs quando a API estabilizar" | API estabiliza mais rápido com docs; o doc é o primeiro teste do design. |
| "Ninguém lê docs" | Agentes leem. Engenheiros futuros leem. |
| "Comentário fica desatualizado" | Comentário de porquê é estável; de quê, não. Escreva só o primeiro. |

## Red flags

- Decisão arquitetural sem rationale escrito.
- API pública sem doc nem tipos.
- README que não explica como rodar o projeto.
- Código comentado em vez de deletado.
- TODO com semanas de idade.
- Zero ADRs em projeto com escolhas arquiteturais.

## Verificação

- [ ] ADR para toda decisão arquitetural significante
- [ ] README com Quick Start, comandos e arquitetura
- [ ] APIs com parâmetros e retornos documentados
- [ ] Gotchas conhecidos documentados inline
- [ ] Nenhum código comentado
- [ ] Rules files (CLAUDE.md etc.) atualizados
