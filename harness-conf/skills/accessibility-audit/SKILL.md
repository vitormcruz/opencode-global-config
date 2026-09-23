---
name: accessibility-audit
description: >
  Use ao auditar web ou mobile para conformidade WCAG, identificar barreiras
  de acessibilidade e priorizar correções, estabelecer prática contínua de
  testes de acessibilidade ou preparar evidências de conformidade para
  stakeholders, com testes automatizados e verificação manual.
  Triggers: "accessibility", "accessibility audit", "WCAG", "a11y", "ARIA",
  "axe-core", "screen reader", "color contrast", "keyboard focus",
  "keyboard navigation", "digital inclusion", "accessibility compliance",
  "WCAG 2.1", "WCAG 2.2", "ADA", "Section 508", "tab order",
  "focus management", "alt text", "semantic HTML", "skip link",
  "inclusive design", "assistive technology".
risk: safe
source: community
---

# Accessibility Audit

Auditoria de acessibilidade: conformidade WCAG, identificação de barreiras e
priorização de correção em web e mobile, com varredura automatizada e
verificação manual.

## Não use quando

- O pedido é review de UI sem escopo de acessibilidade.
- Não há acesso à UI, aos artefatos de design ou ao conteúdo.

## Entrada

$ARGUMENTS

## Instruções

- Confirme o escopo: plataformas, nível WCAG, páginas-alvo e jornadas críticas.
- Rode a varredura automatizada para obter o baseline de violações e lacunas de cobertura.
- Faça a verificação manual: teclado, screen reader, ordem de foco e contraste.
- Mapeie cada achado a critério WCAG, severidade e impacto no usuário.
- Forneça a correção, re-teste após o fix e registre evidências.
- Procedimento detalhado (passos, ferramentas, exemplos de remediação) vive em
  `resources/implementation-playbook.md`.
