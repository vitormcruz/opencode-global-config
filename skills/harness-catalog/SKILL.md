---
name: harness-catalog
description: >
  Catálogo de referência com sugestões de harness por agente
  (eng-software, dba, sec, qa, rev, front, curador-produto).
  Use quando: criando ou atualizando harness de agentes,
  definindo regras de contenção para o /doc/README.md,
  configurando ferramentas determinísticas para script
  único por agente. Triggers: "harness", "catálogo de
  harness", "sugestões de harness", "regras de contenção",
  "ferramentas de harness", "harness catalog",
  "criar harness", "definir harness".
---

# Catálogo de Referência — Sugestões de Harness

> **Nota importante:** as regras abaixo são referência de
> domínio para orientar o humano na criação de harness.
> **Não são regras obrigatórias.** O harness efetivo de
> cada agente é definido no `AGENTS.md` de cada
> projeto.

## Interface Padronizada

Cada agente possui um **script único** (sem argumentos,
idempotente) que retorna JSON:

```json
{
  "status": "pass | fail",
  "findings": [
    {
      "severity": "bloqueante | melhoria",
      "tool": "nome-da-ferramenta",
      "message": "descrição do problema"
    }
  ],
  "prompt": "instrução adicional (opcional)"
}
```

Exit code: 0 = pass, 1 = fail.

### Regras de segurança da interface

- Forçar UTF-8 em stdout/stderr e emitir progresso em stderr,
  sem ecoar a linha JSON final.
- Em falha transitória de rede, fazer retry até 3 vezes;
  esgotado, retornar finding bloqueante com instrução para
  resolver a rede.
- Não bypassar verificações, usar `failOnViolation=false`,
  excluir teste do scan, usar fail-open em audit ou cache sem
  fallback.

## eng-software

- **Instalação de deps de harness** `tool` `build · val`
  Executar script de instalação de harness do projeto
  quando ferramenta ausente.

- **Smoke tests pós-construção** `prompt` `build`
  Executar todos os testes ao final da construção.

- **Testes existentes são intocáveis** `prompt` `build`
  Teste não previsto para alteração falhou → registrar
  e perguntar ao humano.

- **Regressão incremental** `prompt` `build`
  Após cada modificação, executar testes existentes.

- **Análise estática** `tool` `build · val`
  ESLint, ruff, mypy, pyright, shellcheck, hadolint, etc.

## dba

- **Validação de SQL** `tool` `build · val`
  SQLFluff ou linter SQL do projeto. Error = bloqueante.

- **Schema diff** `tool` `build`
  Comparar schema resultante com modelo "as code".

- **IaC lint** `tool` `build · val`
  checkov/tflint se houver infra de BD.

- **Nomenclatura determinística** `prompt` `build · val`
  Verificar convenção de naming do projeto.

## sec

> Ferramentas efetivas: as do `AGENTS.md`. Abaixo
> é catálogo de referência.

- **SAST obrigatório** `tool` `build · val`
  Semgrep ou SAST do projeto. high/critical = bloqueante.

- **Secrets scan** `tool` `build`
  gitleaks/git-secrets no diff. Segredo = bloqueante.

- **Dependency check** `tool` `val`
  Snyk/npm audit/pip-audit. Críticas = bloqueante.

- **OWASP Top 10 checklist** `prompt` `val`
  Verificar riscos OWASP aplicáveis.

- **DAST** `tool` `val`
  OWASP ZAP ou equivalente. high/critical = bloqueante.

## qa

- **Cobertura mínima** `tool` `val`
  Cobertura não pode cair abaixo do baseline.

- **Testes de aceitação** `tool` `val`
  BDD/Playwright/Cypress. Falhas = bloqueante.

- **Relatório estruturado** `prompt` `val`
  Total executados, passaram, falharam, skipped, delta.

- **Acessibilidade** `tool` `val`
  axe-core ou equivalente (frontend). Critical = bloqueante.

## rev

- **Markdown lint** `tool` `val`
  markdownlint em docs produzidas.

- **Link check** `tool` `val`
  markdown-link-check. Links quebrados = reportar.

- **Consistência cross-artefato** `prompt` `val`
  Nomes, convenções e referências consistentes.

- **Aderência ao plano** `prompt` `val`
  Desvios não autorizados = bloqueante.

## front

- **Validação do humano (gate visual)** `prompt` `build`
  Após gerar protótipos, apresentar ao humano para
  aprovação. Sem aprovação, a construção não avança.

- **Lint CSS/HTML** `tool` `build · val`
  stylelint, htmlhint ou equivalente.

- **Acessibilidade** `tool` `build · val`
  axe-core, pa11y ou equivalente. Critical = bloqueante.

- **Snapshot visual** `tool` `val`
  Playwright/Cypress snapshot visual (se aplicável).

- **Aderência à identidade visual** `prompt` `val`
  Comparar implementação contra protótipos aprovados.
  Desvios não autorizados = bloqueante.

## curador-produto

- **Checklist do AGENTS.md** `prompt` `val`
  Verificar se faltou atualizar documentação.
- **Atualiza AGENTS.md diretamente** `prompt` `val`
  Alterou estrutura/convenções → atualizar AGENTS.md.

- **Valida existência de harness** `prompt` `val`
  Todos os agentes devem ter harness registrado.

- **Delega outros domínios** `prompt` `val`
  Problemas em código/BD/segurança → instruir delegação.
