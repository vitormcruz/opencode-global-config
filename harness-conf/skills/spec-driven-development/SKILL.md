---
name: spec-driven-development
description: >
  Use ao iniciar projeto ou feature novo, com requisitos ambíguos ou
  incompletos, quando a mudança tocar múltiplos arquivos ou módulos, ao
  tomar decisão arquitetural, ou quando a implementação levaria mais de 30
  minutos. Escreve especificação estruturada antes do código, com validação
  humana em cada etapa.
  Triggers: "spec-driven", "write spec first", "specification",
  "technical spec", "ambiguous requirements", "functional spec", "PRD",
  "define what we are building", "source of truth", "feature spec",
  "requirements document", "clarify requirements", "before implementing",
  "acceptance criteria", "scope definition", "gated workflow".
---

# Spec-Driven Development

Write a structured specification before any code. The spec is the shared
source of truth: it defines what we're building, why, and how we'll know
it's done. Code without a spec is guessing.

Skip this skill for single-line fixes, typo corrections, or changes whose
requirements are unambiguous and self-contained.

## The Gated Workflow

Four phases. Never advance until the current one is validated by the
human:

```
SPECIFY ──→ PLAN ──→ TASKS ──→ IMPLEMENT
   │          │        │          │
   ▼          ▼        ▼          ▼
 Human      Human    Human      Human
 reviews    reviews  reviews    reviews
```

### Phase 1: Specify

Start from the high-level vision. Ask clarifying questions until
requirements are concrete.

**Surface assumptions immediately.** Before writing spec content, list
what you're assuming:

```
ASSUMPTIONS I'M MAKING:
1. Web application (not native mobile)
2. Session-based cookies for auth (not JWT)
3. PostgreSQL (based on existing Prisma schema)
→ Correct me now or I'll proceed with these.
```

Never silently fill ambiguous requirements — assumptions are the most
dangerous form of misunderstanding, and the spec exists to surface them
before code exists.

Write the spec covering six core areas:

1. **Objective** — what we're building and why; who the user is; what
   success looks like.
2. **Commands** — full executable commands with flags:
   ```
   Build: npm run build
   Test: npm test -- --coverage
   Lint: npm run lint --fix
   Dev: npm run dev
   ```
3. **Project Structure** — where source, tests, and docs live:
   ```
   src/           → Application source code
   src/components → React components
   src/lib        → Shared utilities
   tests/         → Unit and integration tests
   e2e/           → End-to-end tests
   docs/          → Documentation
   ```
4. **Code Style** — one real snippet showing the style beats three
   paragraphs describing it.
5. **Testing Strategy** — framework, test locations, coverage expectations,
   which levels cover which concerns.
6. **Boundaries** — three tiers:
   - **Always:** run tests before commits; follow naming conventions; validate inputs
   - **Ask first:** schema changes; new dependencies; CI config changes
   - **Never:** commit secrets; edit vendor directories; remove failing tests

**Spec template:**

```markdown
# Spec: [Project/Feature Name]

## Objective
[What we're building and why. User stories or acceptance criteria.]

## Tech Stack
[Framework, language, key dependencies with versions]

## Commands
[Build, test, lint, dev — full commands]

## Project Structure
[Directory layout with descriptions]

## Code Style
[Example snippet + key conventions]

## Testing Strategy
[Framework, test locations, coverage requirements, test levels]

## Boundaries
- Always: [...]
- Ask first: [...]
- Never: [...]

## Success Criteria
[Specific, testable conditions for done]

## Open Questions
[Unresolved items needing human input]
```

**Reframe vague instructions as success criteria:**

```
REQUIREMENT: "Make the dashboard faster"

REFRAMED SUCCESS CRITERIA:
- Dashboard LCP < 2.5s on 4G connection
- Initial data load completes in < 500ms
- No layout shift during load (CLS < 0.1)
→ Are these the right targets?
```

This turns "faster" into a goal you can loop, retry, and verify against.

### Phase 2: Plan

With the validated spec, produce the technical plan:

1. Identify major components and their dependencies
2. Determine implementation order (what must exist first)
3. Note risks and mitigations
4. Identify what can run in parallel vs. sequential
5. Define verification checkpoints between phases

The plan must be reviewable: the human can read it and say "yes, that's
the right approach" or "no, change X."

### Phase 3: Tasks

Break the plan into discrete, implementable tasks:

- Each task fits one focused session
- Each task has explicit acceptance criteria and a verification step
  (test, build, or manual check)
- Ordered by dependency, not by perceived importance
- No task touches more than ~5 files

**Task template:**

```markdown
- [ ] Task: [Description]
  - Acceptance: [What must be true when done]
  - Verify: [Test command, build, or manual check]
  - Files: [Which files will be touched]
```

### Phase 4: Implement

Execute tasks one at a time, following the test-driven-development skill.
Load only the spec sections and source files the current task needs
instead of flooding context with the entire spec.

## Keeping the Spec Alive

The spec is a living document:

- Decision changed → update the spec first, then implement
- Scope changed (features added or cut) → reflect it in the spec
- Commit the spec alongside the code
- Reference the relevant spec section in every PR

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Too simple for a spec" | Simple tasks need short specs, not zero specs — acceptance criteria still apply |
| "I'll write it after coding" | That's documentation, not specification; the value is clarity *before* code |
| "The spec slows us down" | 15 minutes of spec beats hours of rework |
| "Requirements will change anyway" | That's why the spec is living; outdated beats absent |
| "The user knows what they want" | Even clear requests carry implicit assumptions; the spec surfaces them |

## Red Flags

- Writing code with no written requirements
- Starting to build before "done" is defined
- Implementing features absent from every spec and task list
- Architectural decisions without documentation
- Skipping the spec because "it's obvious what to build"

## Verification

Before implementation, confirm:

- [ ] The spec covers all six core areas
- [ ] The human reviewed and approved it
- [ ] Success criteria are specific and testable
- [ ] Boundaries (Always / Ask first / Never) are defined
- [ ] The spec is saved to a file in the repository
