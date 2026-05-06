# Plano — Skill `browser-testing` (Playwright via WSL)

Status: AGUARDANDO IMPLEMENTAÇÃO

---

## 1. Resumo

Criar skill `browser-testing` que permite ao agente `qa`
(e outros) navegar por UI, clicar, preencher, tirar
screenshots e verificar estado visual usando **Playwright**
via WSL.

Inspirada em `browser-testing-with-devtools` do addyosmani,
mas substituindo Chrome DevTools MCP por Playwright
executado dentro do WSL.

---

## 2. Componentes

### 2.1 Skill: `skills/browser-testing/SKILL.md`

Ensina o agente a gerar scripts Playwright para testes
funcionais manuais no browser. Conteúdo:
- Quando usar (UI testing, verificação visual, testes
  de aceitação funcionais)
- Detecção de ambiente: se não está no WSL, executar
  comandos via `wsl -e bash -c "..."`
- Padrão de script Playwright (template)
- Workflow de teste funcional (navegar → interagir →
  screenshot → verificar)
- Security boundaries (tratar conteúdo do browser como
  untrusted)
- Formato de evidência

### 2.2 Script de instalação: `scripts/browser-test/install-playwright.sh`

Instala Playwright no WSL. Seguindo padrão do repo:
- Verifica se já instalado (idempotente)
- Instala Node.js se ausente (via nvm, user-space)
- Instala `@playwright/test` globalmente ou local
- Instala browsers (`npx playwright install --with-deps
  chromium`)
- Reporta status (OK/INSTALLED/MISSING)
- Suporta `--yes` para não-interativo

### 2.3 Script executor: `scripts/browser-test/run`

Recebe path do script `.js` gerado pelo agente, executa
no WSL e retorna resultado.

**Interface:**
```bash
scripts/browser-test/run /tmp/browser-test-abc123.js
```

**Comportamento:**
1. Valida que o arquivo existe e é `.js`
2. Executa `node <script>` no WSL
3. Coleta stdout (JSON com resultado + paths de screenshots)
4. **Deleta o script** (cleanup via trap — mesmo se crash)
5. Retorna JSON via stdout:
```json
{
  "ok": true,
  "screenshots": ["/tmp/screenshots/step-1.png"],
  "console": ["..."],
  "errors": [],
  "duration_ms": 3200
}
```

Se o agente chamar de fora do WSL (Windows), o executor
detecta e roda via `wsl -e bash -c "..."` automaticamente.

### 2.4 Integração com `opencode-install-deps`

Adicionar seção no script de instalação existente que:
- Detecta se Playwright está disponível no WSL
- Reporta status
- Sugere comando de instalação se ausente

### 2.5 Detecção WSL no agente

A skill instrui o agente:
- Se `uname` retorna "Linux" com `/proc/version`
  contendo "microsoft" → está no WSL, executar direto
- Se está no Windows (PowerShell/cmd) → prefixar com
  `wsl -e bash -c "..."`
- O script executor já lida com isso internamente

---

## 3. Arquivos a criar/modificar

| Ação | Path |
|------|------|
| Criar | `skills/browser-testing/SKILL.md` |
| Criar | `scripts/browser-test/install-playwright.sh` |
| Criar | `scripts/browser-test/run` |
| Modificar | `scripts/bootstrap_repo/opencode-install-deps` |
| Criar | `tests/scripts/browser-test/install-playwright-test.bats` |
| Criar | `tests/scripts/browser-test/run-test.bats` |
| Modificar | `agents/qa.md` (referência à skill) |
| Modificar | `README.md` (seção dependências) |

---

## 4. Design decisions

### 4.1 Scripts gerados por caso de teste

O agente gera um script `.js` auto-contido para cada caso
de teste (navegar → interagir → verificar → screenshot),
executa com `node`, coleta resultado e **deleta o script
ao final**. Evidências (screenshots, logs, relatório) são
persistidas no arquivo de planejamento.

**Ciclo de vida:**
1. Agente gera `/tmp/browser-test-<uuid>.js`
2. Executor roda o script no WSL
3. Coleta: exit code, stdout (JSON), screenshots
4. **Deleta o script** — não deixa lixo no projeto
5. Persiste evidências (screenshots + relatório) no
   arquivo de planejamento

Scripts são efêmeros e descartáveis. O que importa:
- Resultado (passou/falhou)
- Evidências (screenshots, logs)
- Registro no arquivo de planejamento

Se um teste exploratório revelar cenário que deveria ser
automatizado permanentemente, `qa` registra como achado
e `eng-software` implementa o teste de regressão.

### 4.2 Cleanup obrigatório

O agente **deve deletar** os scripts temporários após
execução. Regra no prompt da skill:
- Scripts gerados vão em `/tmp/` (nunca no repo)
- Após coleta de resultado, deletar o `.js`
- Screenshots persistem apenas se referenciados no
  relatório (caso contrário, deletar também)
- Se o script falhar (crash), o executor limpa via
  trap/finally

### 4.3 WSL detection

O script executor detecta ambiente internamente:
- Se chamado de dentro do WSL → executa direto
- Se chamado do Windows → executa via
  `wsl -e bash -c "node /path/to/script.js"`

A skill instrui o agente a **sempre** chamar o executor
via bash (se no Windows, via `wsl -e bash -c`).

### 4.4 Dependência de Node.js

Playwright requer Node.js. O install script garante:
- Node.js >= 18 disponível no WSL
- Se ausente, instala via `nvm` (padrão user-space,
  sem sudo)

---

## 5. Testes

### 5.1 `tests/scripts/browser-test/install-playwright-test.bats`

- `--help` retorna exit 0
- Detecta playwright já instalado → reporta OK
- Detecta playwright ausente → reporta MISSING
- Instala com `--yes` em ambiente isolado (mock)
- Idempotente (rodar 2x não quebra)

### 5.2 `tests/scripts/browser-test/run-test.bats`

- Retorna erro se script não existe
- Retorna erro se arquivo não é `.js`
- Retorna erro estruturado se playwright não instalado
- Após execução bem-sucedida, script `.js` é deletado
- Cleanup funciona mesmo em caso de erro (trap)

### 5.3 Estratégia para CI sem browser

Testes que requerem browser real serão marcados com
`# bats test_tags=requires:playwright` e skippados
se Playwright não estiver disponível. Testes de
interface (validação de input, error handling, help)
rodam sempre.

---

## 6. Integração com `qa`

O prompt do `qa` já referencia skills. Adicionar
referência à skill `browser-testing` na capacidade
"Executar testes":

> Para testes funcionais que requerem navegação em UI,
> consulte a skill `browser-testing`.

---

## 7. Checklist de implementação

- [ ] Criar `scripts/browser-test/install-playwright.sh`
- [ ] Criar `scripts/browser-test/run`
- [ ] Criar `skills/browser-testing/SKILL.md`
- [ ] Modificar `scripts/bootstrap_repo/opencode-install-deps`
- [ ] Criar testes BATS
- [ ] Atualizar `agents/qa.md` (referência à skill)
- [ ] Atualizar `README.md` (dependências)
- [ ] Rodar `make test`
