---
name: testes-produto-catalog
description: >
  Use ao criar ou atualizar suítes, definir a seção "Testes por
  Especialidade" no docs/README.md ou configurar ferramentas
  determinísticas. Catálogo de sugestões de ferramentas por especialidade
  (backend, dados, segurança, frontend) e do agregador testes-produto.
  Triggers:
  "testes-produto", "catálogo de testes-produto",
  "sugestões de suíte", "regras de contenção",
  "ferramentas de testes-produto", "criar suítes",
  "definir suítes", "testes por especialidade",
   "agregador".
---

# Catálogo de Referência — Suítes por Especialidade

Referência de domínio, não regra obrigatória. O spec efetivo é a seção
"Testes por Especialidade" do `docs/README.md`.

## Interface Padronizada

Cada suíte e o agregador `testes-produto` são scripts sem argumentos,
idempotentes, com JSON:

```json
{
  "status": "pass | fail",
  "findings": [
    {
      "severity": "bloqueante | melhoria",
      "tool": "nome-da-ferramenta",
      "message": "descrição do problema"
    }
  ]
}
```

Exit code: 0 = pass, 1 = fail. O agregador `testes-produto` chama as
quatro suítes e consolida `findings`; falha se qualquer suíte falhar.
Executado pelo agente `qa` na fase Testes do workflow; a evidência é
validada pelo `curador-produto`.

### Regras de segurança da interface

- Forçar UTF-8 em stdout/stderr e emitir progresso em stderr, sem ecoar a
  linha JSON final.
- Falha transitória de rede: retry até 3 vezes; esgotado, finding
  bloqueante com instrução de rede.
- Não bypassar verificações, usar `failOnViolation=false`, excluir teste do
  scan, usar fail-open em audit ou cache sem fallback.

## backend

- **Análise estática** `tool`: ESLint, ruff, mypy, pyright, shellcheck,
  hadolint, etc.
- **Cobertura mínima** `tool`: cobertura não pode cair abaixo do baseline.
- **Testes de aceitação** `tool`: BDD/Playwright/Cypress quando o fluxo for
  backend. Falhas = bloqueante.

## dados

- **Validação de SQL** `tool`: SQLFluff ou linter SQL do projeto.
  Error = bloqueante.
- **Schema diff** `tool`: comparar schema resultante com modelo "as code".
- **IaC lint** `tool`: checkov/tflint se houver infra de BD.

## segurança

- **SAST obrigatório** `tool`: Semgrep ou SAST do projeto.
  high/critical = bloqueante.
- **Secrets scan** `tool`: gitleaks/git-secrets no diff. Segredo =
  bloqueante.
- **Dependency check** `tool`: Snyk/npm audit/pip-audit. Críticas =
  bloqueante.
- **DAST** `tool`: OWASP ZAP ou equivalente. high/critical = bloqueante.

## frontend

- **Lint CSS/HTML** `tool`: stylelint, htmlhint ou equivalente.
- **Acessibilidade** `tool`: pa11y, axe-core ou ambos; a entrevista decide.
  Critical = bloqueante.
- **Snapshot visual** `tool`: Playwright/Cypress snapshot visual (se
  aplicável).
- **Cobertura da suíte de UI** `tool`: se houver suíte de UI, a cobertura
  entra aqui.

## Instruções

Itens abaixo não são suíte; vivem em `## Instruções por Agente` se o
humano aprovar.

- Smoke tests e regressão incremental (construção).
- Testes existentes são intocáveis.
- Gate visual e aderência à identidade.
- Checklist OWASP manual (roteiro do `sec`).
- Consistência cross-artefato e aderência ao plano.
