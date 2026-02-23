# Plano: Workflow "Elaborar Backlog" no OpenCode

## Objetivo
Criar um conjunto de agentes no OpenCode para auxiliar na elaboracao e manutencao de backlogs de produto, com historias leves e priorizacao simples.

---

## Decisoes tomadas

### Estrutura do repo
- **Local:** `/mnt/c/Users/ur5y/Projetos/opencode-config/`
- **Symlinks parciais** em `~/.config/opencode/`:
  - `opencode.json` -> repo
  - `AGENTS.md` -> repo
  - `agents/` -> repo
- Arquivos locais mantidos em `~/.config/opencode/`: `package.json`, `bun.lock`, `node_modules/`

### Permissoes globais (`opencode.json`)
- `edit: ask`
- `bash: ask`
- `webfetch: deny`
- `share: manual`

### Regras globais (`AGENTS.md`)
- Idioma: PT-BR (ASCII ok)
- Concisao: respostas curtas por padrao; detalhar apenas quando solicitado
- Acao: nao executar mudancas sem confirmacao explicita

### Formato de historia (sem ID)
```
Eu como <perfil>
Desejo <funcionalidade>
para que <objetivo de negocio>

Requisitos Funcionais:
- ...

Requisitos Nao Funcionais:
- ...

Prioridade: <numero>

Notas:
- ... (opcional)
```

### Prioridade
- Numerica, quanto menor mais prioritario
- Usar espacamento: 10, 20, 30...
- Insercoes intermediarias: 15, 17, 25...

---

## Agentes planejados

| Agente | Tipo | Papel |
|--------|------|-------|
| `elaborar-backlog` | primary | Coordena o workflow, identifica intencao do humano, roteia para subagentes, consolida saida, pede confirmacao antes de editar |
| `analista` | subagent (read-only) | Faz perguntas para identificar lacunas de contexto (personas, objetivos, restricoes, NFRs) |
| `gerador-historias` | subagent (read-only) | Gera historias no formato padrao com RF/RNF e prioridade numerica |
| `priorizador` | subagent (read-only) | Sugere reordenacao e ajuste de prioridade numerica |
| `detalhador` | subagent (read-only) | Sugere quebra de historias grandes em incrementos e identifica spikes |
| `revisor` | subagent (read-only) | Revisa clareza, consistencia e nivel de detalhe |

### Permissoes dos subagentes
Todos os subagentes:
- `edit: deny`
- `bash: deny`
- `webfetch: deny`

### Permissoes do `elaborar-backlog`
- Herda globais (`edit: ask`, `bash: ask`, `webfetch: deny`)
- `task`: permite apenas os 5 subagentes do workflow

---

## Etapas do plano

### Concluidas

- [x] **Etapa 1:** Criar repo base (pasta, git init, agents/, .gitignore)
- [x] **Etapa 2:** Criar `opencode.json` e `AGENTS.md` globais
- [x] **Etapa 3:** Criar symlinks parciais em `~/.config/opencode/`
- [x] **Etapa 4:** Criar `agents/elaborar-backlog.md`
- [x] **Etapa 5:** Criar `agents/analista.md`

### Pendentes

- [x] **Etapa 6:** Discutir e criar `agents/gerador-historias.md`
- [ ] **Etapa 7:** Discutir e criar `agents/priorizador.md`
- [ ] **Etapa 8:** Discutir e criar `agents/detalhador.md`
- [ ] **Etapa 9:** Discutir e criar `agents/revisor.md`
- [ ] **Etapa 10:** Smoke test manual

---

## Arquivos ja criados no repo

```
/mnt/c/Users/ur5y/Projetos/opencode-config/
├── .git/
├── .gitignore
├── AGENTS.md
├── opencode.json
└── agents/
    ├── elaborar-backlog.md
    ├── analista.md
    └── gerador-historias.md
```

---

## Proxima etapa: `gerador-historias`

**Proposta para revisao:**

```markdown
---
description: Gera historias leves no formato padrao (Eu como/Desejo/para que)
mode: subagent
temperature: 0.3
permission:
  edit: deny
  bash: deny
  webfetch: deny
---
Voce e um gerador de historias de backlog.

## Formato obrigatorio
Cada historia deve seguir exatamente este formato:

Eu como <perfil>
Desejo <funcionalidade>
para que <objetivo de negocio>

Requisitos Funcionais:
- ...

Requisitos Nao Funcionais:
- ...

Prioridade: <numero>

Notas:
- ... (opcional)

## Regras de prioridade
- Usar numeros com espaco: 10, 20, 30...
- Menor numero = mais prioritario.
- Para inserir entre existentes, usar intermediarios (15, 17, 25...).
- Justifique a prioridade sugerida em 1 linha.

## Restricoes
- Historias leves; nao detalhar alem do necessario.
- Nao edite arquivos.
- Nao repriorize historias existentes (isso e papel do @priorizador).
```

---

## Agentes restantes (rascunhos)

### `priorizador`
- Sugere reordenacao e ajuste de prioridade numerica
- Considera dependencias, risco e valor percebido
- Nao reescreve texto das historias

### `detalhador`
- Sugere quebra de historias grandes em 2-5 incrementos
- Identifica spikes quando houver incerteza tecnica
- Nao produz especificacao detalhada

### `revisor`
- Revisa clareza, ambiguidade, duplicidade
- Verifica consistencia do formato
- Mantem nivel de detalhe baixo

---

## Como continuar

1. Abra um novo contexto do OpenCode na pasta `/mnt/c/Users/ur5y/Projetos/opencode-config/`
2. Leia este arquivo (`PlanAgents.md`)
3. Continue a partir da **Etapa 6** (criar `agents/gerador-historias.md`)
4. Lembre-se: discutir cada agente antes de criar, um por vez
