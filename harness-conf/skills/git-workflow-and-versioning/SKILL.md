---
name: git-workflow-and-versioning
description: >
  Use sempre: toda mudança de código passa por git. Guia de workflow e
  versionamento: commits atômicos, mensagens descritivas (Conventional
  Commits), trunk-based development, worktrees, save points, higiene de
  pre-commit. Triggers: "git workflow", "commit", "commit message",
  "branch", "merge", "rebase", "merge conflict", "trunk-based development",
  "feature branch", "conventional commits", "semver", "version tag",
  "cherry-pick", "git bisect", "stash", "squash", "pull request workflow",
  "gitflow", "git history", "stage changes", "git log", "rollback".
---

# Git Workflow and Versioning

Git é a rede de segurança: commit é save point, branch é sandbox, histórico
é documentação. Com agentes gerando código em alta velocidade, versionamento
disciplinado é o que mantém a mudança revisável e reversível.

Vale sempre: toda mudança de código passa por git.

## Trunk-based development (recomendado)

Mantenha `main` sempre deployable. Trabalhe em branches curtos, com merge
em 1-3 dias. Branch de dev longa é custo escondido: diverge, gera conflito
e atrasa integração. Pesquisa DORA correlaciona trunk-based com times de
alta performance.

- **Branch de dev é custo.** Cada dia de vida acumula risco de merge.
- **Release branch é aceitável** para estabilizar release enquanto
  `main` avança.
- **Feature flag > branch longa.** Prefira deployar trabalho incompleto
  atrás de flag a manter branch por semanas.

Time com gitflow ou branches longas? Adapte os princípios (commits
atômicos, mudanças pequenas, mensagens descritivas): a disciplina de
commit importa mais que a estratégia de branching.

## Commits

**1. Commit cedo, commit sempre.** Cada incremento bem-sucedido vira um
commit: implementar → testar → verificar → commit → próximo slice.
Commit é save point: a próxima mudança quebrou? Reverta ao último estado
conhecido-bom na hora.

**2. Commit atômico.** Um commit faz uma coisa lógica:

```
# Bom: cada commit é autocontido
a1b2c3d Add task creation endpoint with validation
d4e5f6g Add task creation form component
h7i8j9k Connect form to API and add loading state
m1n2o3p Add task creation tests (unit + integration)

# Ruim: tudo misturado
x1y2z3a Add task feature, fix sidebar, update deps, refactor utils
```

**3. Mensagem descritiva.** Explica o porquê, não só o quê:

```
feat: add email validation to registration endpoint

Prevents invalid email formats from reaching the database.
Uses Zod schema validation at the route handler level,
consistent with existing validation patterns in auth.ts.
```

Formato: `<type>: <descrição curta>` + corpo opcional explicando o
porquê. Tipos: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`.

**4. Separe as preocupações.** Não misture formatação com mudança de
comportamento, nem refactor com feature: cada tipo em commit separado
(idealmente PR separado). Pequena limpeza (renomear variável) pode
entrar no commit de feature, a critério do revisor.

**5. Dimensione a mudança.** Alvo ~100 linhas por commit/PR; ~300 é
aceitável para uma mudança lógica; acima de ~1000, divida. Estratégias
de divisão: ver `code-review-and-quality`.

## Branches

```
main (always deployable)
  ├── feature/task-creation    ← uma feature por branch
  ├── feature/user-settings    ← trabalho paralelo
  └── fix/duplicate-tasks      ← correções
```

- Crie a partir de `main` (ou do default do time).
- Vida curta: merge em 1-3 dias; delete após o merge.
- Trabalho incompleto: feature flag em vez de branch longa.

Nomes: `feature/<descricao>`, `fix/<descricao>`, `chore/<descricao>`,
`refactor/<descricao>`.

## Worktrees

Para agentes em paralelo, um diretório por branch:

```bash
git worktree add ../project-feature-a feature/task-creation
git worktree add ../project-feature-b feature/user-settings
# cada diretório tem a própria branch; agentes trabalham sem trocar de branch
git worktree remove ../project-feature-a  # ao terminar: merge e cleanup
```

Experimento falhou? Delete o worktree: nada se perde. Mudanças ficam
isoladas até o merge explícito.

## Save point pattern

Fez uma mudança → testes passam? Commit e continue; falham? Reverta ao
último commit e investigue. Repita por incremento. Assim nunca se perde
mais que um incremento: `git reset --hard HEAD` volta ao último estado
bom.

## Resumo de mudanças

Após qualquer modificação, forneça resumo estruturado:

```
CHANGES MADE:
- src/routes/tasks.ts: Added validation middleware to POST endpoint
- src/lib/validation.ts: Added TaskCreateSchema using Zod

THINGS I DIDN'T TOUCH (intentionally):
- src/routes/auth.ts: Has similar validation gap but out of scope
- src/middleware/error.ts: Error format could be improved (separate task)

POTENTIAL CONCERNS:
- The Zod schema is strict — rejects extra fields. Confirm this is desired.
- Added zod as a dependency (72KB gzipped) — already in package.json
```

A seção "DIDN'T TOUCH" evidencia disciplina de escopo e evita reforma
não solicitada; "CONCERNS" antecipa suposição errada.

## Higiene de pre-commit

Antes de todo commit:

```bash
git diff --staged                                       # revise o que vai entrar
git diff --staged | grep -i "password\|secret\|api_key\|token"  # sem segredos
npm test                                                # testes
npm run lint                                            # lint
npx tsc --noEmit                                        # tipos
```

Automatize com hooks (lint-staged + husky):

```json
{
  "lint-staged": {
    "*.{ts,tsx}": ["eslint --fix", "prettier --write"],
    "*.{json,md}": ["prettier --write"]
  }
}
```

## Arquivos gerados

- Commit de arquivo gerado só se o projeto o espera (`package-lock.json`,
  migrations Prisma).
- Nunca commitar build output (`dist/`, `.next/`), `.env` nem IDE config
  não compartilhada (`.vscode/settings.json`).
- `.gitignore` cobrindo: `node_modules/`, `dist/`, `.env`, `.env.local`,
  `*.pem`.

## Git para debug

```bash
# Qual commit introduziu o bug (checkout nos midpoints; teste a cada passo)
git bisect start
git bisect bad HEAD
git bisect good <known-good-commit>

# O que mudou recentemente
git log --oneline -20
git diff HEAD~5..HEAD -- src/

# Quem mudou uma linha; procurar mensagem
git blame src/services/task.ts
git log --grep="validation" --oneline
```

## Anti-racionalizações

| Racionalização | Realidade |
|---|---|
| "Committarei quando a feature estiver pronta" | Commit gigante é impossível de revisar. Commite cada slice. |
| "A mensagem não importa" | Mensagem é documentação; você e os agentes futuros precisarão do porquê. |
| "Squasho tudo depois" | Squash destrói a narrativa de desenvolvimento; commits incrementais desde o início. |
| "Branch custa caro" | Branch curta é de graça; a longa é que diverge e colide. |
| "Divido essa mudança depois" | Divida antes de submeter, não depois. |
| "Não preciso de .gitignore" | Até o `.env` de produção ser commitado. Configure agora. |

## Red flags

Mudanças grandes acumuladas sem commit; mensagens tipo "fix", "update",
"misc"; formatação misturada com comportamento; projeto sem
`.gitignore`; `node_modules/`, `.env` ou build artifact commitado;
branch longa muito divergente de `main`; force-push em branch
compartilhada.

## Verificação (todo commit)

- [ ] Uma coisa lógica por commit
- [ ] Mensagem explica o porquê e segue o padrão de tipos
- [ ] Testes passam antes do commit
- [ ] Nenhum segredo no diff
- [ ] Nenhuma mudança só-de-formatação misturada
- [ ] `.gitignore` cobre as exclusões padrão
