# Plano: Skill WSL + Split de Ambiente nos Testes

## TL;DR

Criar uma skill genérica que ensine o VS Code Copilot a executar
corretamente comandos Bash/shell via WSL (`wsl -- bash -ic`), e
modificar o Makefile para condicionar a execução dos testes ao
ambiente declarado via variável explícita `ENV=`. Testes de
integração OpenCode só rodam com `ENV=opencode`; testes de
integração VS Code ficam como item futuro.

---

## Fase 1 — Skill `wsl-execution` para VS Code

**Objetivo**: Skill que orienta o Copilot a prefixar qualquer
comando Bash/BATS/shell com `wsl -- bash -ic "..."` quando
executando no Windows.

**Arquivos a criar**:
- `skills/wsl-execution/SKILL.md`

**Conteúdo da skill**:
- Frontmatter YAML com `name`, `description` (com triggers)
- Triggers de ativação na description:
  - "executar no wsl", "rodar no wsl", "wsl", "bash",
    "terminal linux", "make test", "bats", "shell command",
    "run in wsl", "execute in wsl"
- Regras:
  1. Sempre usar `wsl -- bash -ic "COMANDO"` (nunca `wsl -e
     bash -c` — não carrega ~/.bashrc)
  2. Para caminhos Windows → converter para `/mnt/c/...`
  3. Para scripts do repo → `cd /mnt/c/.../opencode-config &&`
  4. Exemplos canônicos para make targets:
     `wsl -- bash -ic "cd /mnt/c/Users/<usr>/Projetos/opencode-config && make test-unit"`
  5. Quando o terminal já for WSL/Linux → executar direto sem
     prefixo `wsl`
  6. Detecção de contexto: se o terminal ativo é PowerShell/cmd
     → prefixar; se já é bash/zsh → executar direto
- Referência ao padrão existente em AGENTS.md (linhas 103-114)
- Não ter script associado — é só instrução para o LLM

**Sync para VS Code**:
- `vscode-sync.ps1` já copia `skills/*/SKILL.md` para
  `~/.copilot/skills/` automaticamente
- Não precisa de alteração no sync

**Testes**:
- Criar `tests/scripts/skills/wsl-execution-test.bats`:
  - Verifica que SKILL.md existe
  - Verifica que tem frontmatter YAML válido
  - Verifica que description contém triggers obrigatórios
  - Verifica que contém a regra `wsl -- bash -ic` (não
    `wsl -e bash -c`)
- Padrão: espelha `tests/scripts/skills/` existente

---

## Fase 2 — Split de ambiente no Makefile

**Objetivo**: Variável explícita `ENV` controla quais suítes de
teste rodam no target `test`. Sem `ENV` definido → roda unit +
tools (safe default). Com `ENV=opencode` → roda tudo incluindo
integração OpenCode.

**Arquivo a modificar**:
- `Makefile`

**Estratégia técnica**:

```makefile
ENV ?=

.PHONY: test test-unit test-tools test-opencode-integration

## Todos os testes válidos para o ambiente atual
test: test-unit test-tools
	@if [ "$(ENV)" = "opencode" ]; then \
	  $(MAKE) test-opencode-integration; \
	fi

## Testes unitários puros
test-unit:
	$(BATS) ...

## Testes que requerem ferramentas WSL
test-tools:
	$(BATS) ...

## OpenCode via Docker
test-opencode-integration:
	@bash -c 'set -e; ...'
```

**Decisões**:
- `ENV` só tem efeito no target `test` — decide se inclui
  integração OpenCode ou não
- `make test` sem ENV → roda unit + tools (seguro)
- `make test ENV=opencode` → roda unit + tools + integração
- `make test-unit`, `make test-tools`,
  `make test-opencode-integration` → sempre rodam quando
  chamados diretamente, sem checar ENV

**Testes**:
- Atualizar `tests/scripts/bootstrap_repo/repo-structure-test.bats`
  se houver validação do Makefile

---

## Fase 3 — Atualização de documentação

**Arquivos a modificar**:
- `AGENTS.md`: adicionar referência à skill `wsl-execution` e
  à variável `ENV` do Makefile
- `README.md`: atualizar seção de testes com a nova variável ENV
  e exemplos de uso

---

## Fora de escopo (decisão explícita)

- **Testes de integração VS Code**: adiados. Não há API HTTP nem
  CLI do Copilot para consultar skills/agents. Quando/se surgir
  uma forma viável, criar issue separada.
- **Detecção automática de ambiente**: descartada. O usuário
  preferiu variável explícita `ENV=`.
- **code-server em Docker**: complexidade alta, baixo retorno.

---

## Ordem de implementação

1. **Fase 1** — Skill `wsl-execution` + teste (independente)
2. **Fase 2** — Makefile ENV split (*paralelo com 1*)
3. **Fase 3** — Docs (*depende de 1 e 2*)

---

## Arquivos relevantes

- `skills/wsl-execution/SKILL.md` — criar (novo)
- `Makefile` — modificar targets `test` e
  `test-opencode-integration`
- `AGENTS.md` — adicionar regra sobre ENV e referência à skill
- `README.md` — atualizar seção de testes
- `tests/scripts/skills/wsl-execution-test.bats` — criar (novo)
- `skills/browser-testing/SKILL.md` — referência (já tem
  detecção WSL)
- `scripts/bootstrap_repo/opencode-install-deps` — referência
  (`detect_os()`)

## Verificação

1. `make test-unit` passa (inclui novo teste da skill)
2. `make test` sem ENV → roda unit + tools, **não** roda
   integração OpenCode
3. `make test ENV=opencode` → roda tudo incluindo integração
4. `make test-opencode-integration` direto → roda normalmente
5. Skill `wsl-execution` copiada pelo `vscode-sync.ps1` sem erro
6. BATS valida estrutura da SKILL.md (frontmatter, triggers,
   regra canônica)

## Decisões registradas

- Ambiente controlado **somente** por variável explícita ENV
- Default sem ENV = unit + tools (seguro)
- Testes de integração VS Code **adiados**
- Skill é **instrucional** (sem script) — só orienta o LLM
