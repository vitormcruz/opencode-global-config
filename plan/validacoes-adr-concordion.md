# Plano (rascunho futuro): Ativar validações Concordion das ADRs

> Plano para execução futura. NÃO aprovado para execução imediata:
> passar pelo planejador (smart-planner) e decisões humanas antes de
> executar. Criado em 2026-10-14 a partir do achado sistêmico do ciclo
> de permissões task abertas (plano concluído, ver ADR 0012).

## Overview

As specs Concordion que acompanham as ADRs numeradas deste repo usam a
sintaxe `#execute=`/`#assertEquals=`, que o Concordion trata como âncora
comum: o relatório mostra `Successes: 0, Failures: 0` e o veredito `pass`
do gradle não exercita asserção nenhuma. Só as ADRs 0006 e 0008, escritas
com a sintaxe ativa (`[texto](- "metodo()")`), executam de verdade; a
suíte `tests/product_tests/test_concordion_spec_infra.py` sanciona esse
padrão ativo. Consequência concreta confirmada em revisão independente:
uma regressão na fixture `Adr0012Fixture.groovy` (ex.: reintroduzir o bug
`it.name` em `java.nio.file.Path`, corrigido no commit 689ce4f) não seria
capturada por suíte nenhuma; a política de task aberta segue protegida
executavelmente apenas pela guarda Python
(`tests/agents/test_task_spawnable_modes.py`).

Fatos confirmados por executor e revisor independentes (2026-10-14):

- Specs com sintaxe inativa avaliam zero asserções, incluindo a da ADR
  0012 e a `BackendFixture`.
- `Adr0012Fixture.groovy` tem lógica correta por inspeção, mas inativa.
- O runner JUnit usado no TDD da correção não foi versionado.
- Dois refinamentos pendentes na fixture: `entradasDoBlocoTask` casa
  `'  task:'` em qualquer posição do arquivo (não só no frontmatter) e o
  check global `!conteudo.contains('"*": deny')` olha o arquivo inteiro
  (falso positivo potencial com deny legítimo em outra seção).

## Architecture Decisions

(nenhuma aprovada ainda; ver Open Questions)

## Task List

(rascunho preliminar; validar com o humano na sessão de planejamento)

### Task 1: Inventariar specs ativas vs inativas
- Mapear todas as specs/ADRs com fixture (incluindo `BackendFixture`),
  classificar sintaxe ativa/inativa e cruzar com
  `tests/product_tests/test_concordion_spec_infra.py`.
- Entregável: lista no plano com veredito real de cada spec.

### Task 2: Decisão humana sobre estratégia
- Opções: converter todas as specs para a sintaxe ativa das ADRs
  0006/0008; ou substituir Concordion por guardas pytest equivalentes;
  ou híbrido. Requer decisão antes da execução.

### Task 3: Aplicar a estratégia escolhida com TDD
- Converter/escrever validações com veredito real (`Successes > 0`),
  começando pela ADR 0012; versionar runner de proteção se a estratégia
  mantiver Concordion.

### Task 4: Endurecer a fixture da ADR 0012 (se mantida)
- Delimitar `entradasDoBlocoTask` ao frontmatter e escopar o check
  global de deny à seção `task`.

### Task 5: Suíte completa
- `.venv/bin/pytest -m all` + gradle com veredito real; registro de
  evidências.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Converter specs exige conhecimento Concordion/Groovy | Médio | Seguir o padrão das ADRs 0006/0008, já sancionado pela suíte pytest de infra |
| Fixtures com lógica morta passam falsa segurança | Alto | Verificar `Successes > 0` no relatório como critério de aceite |

## Open Questions

- Estratégia alvo: sintaxe ativa em todas, migração para pytest, ou
  híbrido? (decisão humana)
- Escopo: todas as ADRs numeradas com fixture ou só as que afirmam
  validação executável na prosa?
- A suíte pytest de infra deve reprovar sintaxe inativa (guarda nova) ou
  apenas avisar?

## Status

- Fase: rascunho para execução futura; aguardando início pelo humano.
