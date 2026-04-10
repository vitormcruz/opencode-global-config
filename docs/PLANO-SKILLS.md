# PLANO-SKILLS — Incorporação de Skills de Engenharia

## Objetivo

Incorporar 14 skills externas ao `opencode-config` para cobrir as práticas
do `DEVELOPING.md`: TDD, code review, segurança, ADRs, debugging, performance,
acessibilidade e pentest.

## Fontes

| Fonte | Skills | URL |
|---|---|---|
| addyosmani/agent-skills | 12 | github.com/addyosmani/agent-skills |
| vichhka-git/opencode-shannon-plugin | 1 (pentest) | github.com/vichhka-git/opencode-shannon-plugin |
| sickn33/antigravity-awesome-skills | 1 (acessibilidade) | github.com/sickn33/antigravity-awesome-skills |

## Decisões Tomadas

- **ADR path:** `docs/adr/` (já definido no DEVELOPING.md)
- **References:** pasta `references/` na raiz do repo (compartilhada, sem duplicação)
- **Shannon:** skill completa com UPSTREAM.md; `deny` por padrão no `opencode.json`
- **Adaptação de descriptions:** cada SKILL.md adaptado terá description rica
  (max 1024 chars) com triggers de ativação; original preservado como
  `SKILL.upstream.md`
- **Idioma:** corpo do SKILL.md em PT-BR; exemplos de código em inglês

## Etapas

### Etapa 1 — Infraestrutura de sync (addyosmani)

**Complexidade:** Média | **Contexto:** Baixo

- Criar `scripts/addyosmani/sync` seguindo o padrão de `scripts/prompt-improver/sync`
- Diferença: um único repo fonte → múltiplas skills (12)
- O script deve:
  - Clonar/atualizar `addyosmani/agent-skills` em `/tmp`
  - Para cada skill listada, copiar `SKILL.md` → `skills/<nome>/SKILL.upstream.md`
  - Copiar `references/` → `references/` na raiz
  - Registrar commit SHA e data no UPSTREAM.md de cada skill
  - Suportar `--check-only` e `--yes`
- Criar UPSTREAM.md para cada uma das 12 skills (mesmo template)

### Etapa 2 — Primeira sincronização (addyosmani)

**Complexidade:** Baixa | **Contexto:** Baixo

- Executar `scripts/addyosmani/sync --yes`
- Validar que os 12 `SKILL.upstream.md` e 4 arquivos de `references/` existem
- Commit intermediário

### Etapa 3 — Adaptação dos SKILL.md (12 skills)

**Complexidade:** Alta | **Contexto:** Alto (fazer em lotes de 3-4)

Para cada skill:
1. Ler `SKILL.upstream.md`
2. Criar `SKILL.md` adaptado:
   - Frontmatter com `description` rica (max 1024 chars, PT-BR, triggers de ativação)
   - Corpo traduzido para PT-BR
   - Referências apontando para `references/` na raiz
   - ADR paths ajustados para `docs/adr/`
3. Manter `SKILL.upstream.md` intocado

**Lotes sugeridos:**
- Lote A: `test-driven-development`, `code-review-and-quality`,
  `code-simplification`
- Lote B: `security-and-hardening`, `documentation-and-adrs`,
  `debugging-and-error-recovery`
- Lote C: `git-workflow-and-versioning`, `spec-driven-development`,
  `planning-and-task-breakdown`
- Lote D: `api-and-interface-design`, `performance-optimization`,
  `frontend-ui-engineering`

### Etapa 4 — Shannon (pentest)

**Complexidade:** Média | **Contexto:** Médio

- Criar `skills/shannon-pentest/`
- SKILL.md com description incluindo: "pentest", "teste de penetração",
  "segurança ofensiva", "OWASP"
- SKILL.upstream.md com conteúdo original
- UPSTREAM.md com referência ao repo `vichhka-git/opencode-shannon-plugin`
- Script `scripts/shannon-pentest/sync`
- Adicionar ao `opencode.json`:
  ```json
  "permission": {
    "skill": {
      "aws-*": "deny",
      "shannon-*": "deny"
    }
  }
  ```
- Criar agent ou config que permite shannon quando necessário
  (padrão do `aws-analista`)

### Etapa 5 — Accessibility audit

**Complexidade:** Baixa | **Contexto:** Baixo

- Criar `skills/accessibility-audit/`
- SKILL.md adaptado do antigravity (PT-BR, description rica)
- SKILL.upstream.md com original
- UPSTREAM.md com referência ao repo sickn33
- Script `scripts/accessibility-audit/sync`

### Etapa 6 — Atualizar DEVELOPING.md

**Complexidade:** Média | **Contexto:** Médio

- Adicionar seção "Skills de Apoio" mapeando fases → skills:
  - **Planejamento:** `planning-and-task-breakdown`, `spec-driven-development`
  - **Execução:** `test-driven-development`, `code-simplification`,
    `api-and-interface-design`, `frontend-ui-engineering`,
    `performance-optimization`, `documentation-and-adrs`
  - **Revisão:** `code-review-and-quality`, `security-and-hardening`,
    `accessibility-audit`
  - **Testes:** `debugging-and-error-recovery`, `shannon-pentest`,
    `git-workflow-and-versioning`
- Adicionar diretiva: quando uma skill disponível cobrir a tarefa atual,
  prefira carregá-la via tool `skill` antes de agir
- Referenciar skills por nome nas seções existentes (TDD, ADR, Clean Code)

### Etapa 7 — Atualizar opencode.json

**Complexidade:** Baixa | **Contexto:** Baixo

- Permissão `shannon-*: deny` global
- Avaliar se algum agent existente deve ter permissão explícita para shannon

### Etapa 8 — Documentação de manutenção

**Complexidade:** Baixa | **Contexto:** Baixo

- Criar `docs/UPSTREAM-GUIDE.md` explicando:
  - Padrão de sync: `SKILL.upstream.md` = cópia intocada, `SKILL.md` = adaptada
  - Como fazer merge de atualizações upstream
  - Checklist de revisão pós-sync
- Atualizar README.md (seção de dependências se necessário)

### Etapa 9 — Testes

**Complexidade:** Média | **Contexto:** Médio

- `tests/structure/repo-structure.bats`: validar que todas as 14 skills têm
  `SKILL.md`, `SKILL.upstream.md`, `UPSTREAM.md`
- `tests/skills/`: testar scripts de sync (addyosmani, shannon, accessibility)
  com `--check-only`
- `tests/behavioral/skills-activation.bats`: validar que descriptions contêm
  triggers esperados
- Rodar `make test` e corrigir falhas

## Ordem de Execução

```
Etapa 1 → Etapa 2 → Etapa 3 (lotes A→D) → Etapa 4 → Etapa 5
    ↓
Etapa 6 + Etapa 7 + Etapa 8 (paralelas)
    ↓
Etapa 9
```

## Critérios de Aceite

- [ ] 14 skills com `SKILL.md` + `SKILL.upstream.md` + `UPSTREAM.md`
- [ ] `scripts/skills/list-updatable` lista todas as 14
- [ ] `references/` contém os 4 checklists
- [ ] Shannon com `deny` por padrão no `opencode.json`
- [ ] DEVELOPING.md com seção "Skills de Apoio"
- [ ] `docs/UPSTREAM-GUIDE.md` criado
- [ ] `make test` passa sem erros
