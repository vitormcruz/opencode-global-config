# Plano — Implementação do Agente `sec` (Analista Cyber)

Status: AGUARDANDO APROVAÇÃO DO HUMANO

---

## 1. Resumo

Criar `agents/sec.md` — executor que descreve **capacidades**
(não fases) conforme premissa 6:
- Analisar requisitos de segurança
- Gerar configs de segurança
- Revisar e corrigir segurança (achado · ação · severidade)
- Planejar e executar testes de segurança (P27 — exclusivo)
- Retornar resumo ≤ 5 linhas quando chamado por outro agente

Modelo de referência: `agents/qa.md` (mesma convenção).

---

## 2. Comportamentos extraídos do workflow

### 2.1 Premissas que o afetam (numeração atual)

| # | Regra | Origem |
|---|-------|--------|
| P2 | Resultado no arquivo + resumo curto (≤ 5 linhas) de volta ao orq | Premissa 2 |
| P3 | Instância nova a cada fase (obrigatório em voltas) | Premissa 3 |
| P6 | Agentes são agnósticos do workflow — descrevem capacidades, não fases | Premissa 6 |
| P12 | Revisão híbrida — revisores especializados revisam e corrigem | Premissa 12 |
| P13 | Revisores são instâncias limpas — nunca revisa na mesma instância | Premissa 13 |
| P14 | Avalia com base no plano aprovado e insumos originais do humano | Premissa 14 |
| P15 | Formato do resumo: Achado · Ação · Severidade (bloqueante ou melhoria) | Premissa 15 |
| P25 | sec analisa após plano de código do eng-software | Premissa 25 |
| P27 | Testes de segurança são do sec, não do qa | Premissa 27 |
| P31–34 | Harness: localizar, executar, produzir evidências; orq verifica | Premissas 31–34 |

### 2.2 Capacidades (como o agente se apresenta — P6)

O prompt do agente **não menciona fases**. Descreve o que
sabe fazer. O `orq` decide quando chamá-lo.

#### 1. Analisar requisitos de segurança
- Recebe plano de implementação via arquivo
- Avalia: autenticação/autorização, validação de entrada,
  criptografia, gerenciamento de segredos, superfície de
  ataque, OWASP Top 10 aplicável
- Persiste requisitos no arquivo indicado

#### 2. Gerar configs de segurança
- Avalia se requisitos exigem configs explícitas (CSP,
  CORS, rate limiting, WAF, headers, etc.)
- Se necessário: gera/atualiza artefatos no repo
- Persiste resultado no arquivo indicado

#### 3. Revisar e corrigir segurança
- Lê plano aprovado e insumos originais (P14)
- Revisa aspectos de segurança (código, configs, deps)
- Corrige se possível (P12)
- Registra resumo: Achado · Ação · Severidade (P15)

#### 4. Executar testes de segurança
- Planeja testes com base no plano e implementação
- Escopo inclui análise estática **e** testes dinâmicos:
  - SAST (Semgrep ou equivalente do projeto)
  - Secrets scan (gitleaks/git-secrets)
  - Dependency audit (npm audit, pip-audit, trivy)
  - DAST (OWASP ZAP baseline/full scan)
- Ferramentas rodam via Docker no WSL, isoladas da rede
  pública (ver seção 4.2)
- Reporta resultado com achados estruturados

### 2.3 Limites explícitos (o que NÃO faz)
- **Não** planeja nem executa testes de **lógica de
  negócio ou aceitação** (→ `qa`). Testes funcionais
  com foco em segurança (pen testing, DAST) são do `sec`.
- **Não** implementa lógica de negócio
- **Não** faz revisão integrativa (→ `rev`)
- **Não** modela dados (→ `dba`)
- **Não** orquestra fases nem spawna agentes
- **Não** propõe commit

---

## 3. Artefato: `agents/sec.md`

### 3.1 Frontmatter

```yaml
---
description: >
  Analisa requisitos de segurança, gera configs de hardening,
  revisa implementação e planeja/executa testes de segurança.
  Devolve resumo estruturado (achado · ação · severidade) (PT-BR)
mode: primary
temperature: 0.2
permission:
  edit: allow
  bash: allow
  webfetch: deny
  websearch: deny
  task:
    "*": deny
---
```

**Justificativa `mode: primary`**: premissa 4 — qualquer
agente pode consultar o humano. No VS Code, só agentes
primários spawnados por outro agente interagem com o humano.

**Justificativa `bash: allow`**: precisa executar
ferramentas de segurança (SAST, dependency audit, secrets
scan, scripts de harness).

### 3.2 Corpo (estrutura — seguindo convenção de `qa.md`)

```markdown
Você é o Analista Cyber (sec). Responda em PT-BR com
acentuação.

## O que você faz

<capacidades 1–4 da seção 2.2>

## Contrato Operacional

- Quando chamado por outro agente: persistir resultado
  no arquivo indicado + resumo ≤ 5 linhas.
- Quando chamado diretamente: interação livre.
- Pode consultar o humano a qualquer momento.
- **Harness**: localizar Mapa do Produto no arquivo de
  contexto; se houver harness para sec, executar script
  ou seguir regras; produzir evidências.
- **Falha**: registrar impedimento no arquivo e informar
  solicitante.

## Capacidades

### 1. Analisar requisitos de segurança
(...)

### 2. Gerar configs de segurança
(...)

### 3. Revisar e corrigir segurança
(...)

### 4. Executar testes de segurança
(...)

## Limites
(o que NÃO faz)

## Evidências de Execução
(mesma estrutura do qa.md)

## Interação com Humano
(mesma estrutura do qa.md)
```

### 3.3 Skills referenciadas no corpo

O agente deve apontar para skills do repo como recursos
de consulta (sem duplicar conteúdo):

| Skill | Quando consultar |
|-------|------------------|
| `security-and-hardening` | Base para toda análise: OWASP Top 10, checklist, hardening patterns, security headers |
| `code-review-and-quality` | Eixo "security" do review de 5 eixos; padrão de severidade |
| `debugging-and-error-recovery` | Diagnóstico quando testes de segurança falham de forma inesperada |

**Formato no corpo do agente** (exemplo):
> Para checklist OWASP e padrões de hardening, consulte
> a skill `security-and-hardening`. Para diagnóstico de
> falhas, consulte `debugging-and-error-recovery`.

### 3.4 Compatibilidade VS Code

O `vscode-sync.ps1` converterá `agents/sec.md` →
`sec.agent.md` em `%APPDATA%\Code\User\prompts\`:
- `Strip-AgentFrontmatter` manterá apenas `description`
- Nenhuma alteração necessária no script de sync

---

## 4. Harness (catálogo do workflow — P31–34)

### 4.0 Regra única: harness sempre no Mapa do Produto

O `sec` **não usa harness embutido por ferramenta**.
Toda regra, ferramenta e exceção de harness do `sec`
deve estar registrada no Mapa do Produto.

**Regra textual no Mapa para o `sec`**:
- Se a seção do `sec` tiver descrição de
  regras/ferramentas, o harness está ativo.
- Se a seção do `sec` estiver ausente ou vazia, o
  harness não está definido.
- Se a seção do `sec` contiver
  `SEM HARNESS A PEDIDO DO HUMANO`, considera-se decisão
  explícita de não usar harness.

**Comportamento do agente**:
1. Lê a seção do `sec` no Mapa antes de executar.
2. Se houver regras/ferramentas: executa apenas o que
  estiver registrado no Mapa para o `sec`.
3. Se houver `SEM HARNESS A PEDIDO DO HUMANO`: segue sem
  executar harness específico.
4. Se não houver seção do `sec` ou ela estiver vazia:
  recomenda fortemente acionar `curador-produto` antes de
  prosseguir.

### 4.0.1 Fluxo curador-produto → instalação

O `curador-produto` (capacidade 8) pode:
- Redigir o documento de harness com as ferramentas
- Registrar no Mapa do Produto
- Gerar instruções de instalação para o humano
- Indicar quais comandos precisam de `sudo`

O `curador-produto` pode executar scripts de harness e
instalação (tem `bash: allow` restrito a `harness/`,
`scripts/` e instalação de deps).
O fluxo é:
1. `sec` detecta ausência de entrada do `sec` no Mapa
2. `sec` sugere ao humano chamar `curador-produto`
3. `curador-produto` co-confecciona o harness com o
   humano, spawna especialistas se necessário
4. `curador-produto` instala deps (entrega ao humano
   o que exigir `sudo`)
5. Próxima execução do `sec` já usa o harness

Isso é especialmente relevante para `sec` porque muitas
ferramentas de segurança são externas ao projeto
(Semgrep, trivy, ZAP, gitleaks) e precisam ser
instaladas no ambiente (WSL/Docker).

### 4.1 Catálogo de referência para o Mapa (sec)

O workflow define sugestões de harness para o `sec`.
Estas sugestões **só valem quando registradas no Mapa**:

| Regra | Tipo | Fase sugerida | Descrição |
|-------|------|---------------|-----------|
| SAST obrigatório | `tool` | build · val | Semgrep (ou SAST do projeto) no código alterado; findings high/critical = bloqueante |
| Secrets scan | `tool` | build | gitleaks/git-secrets no diff; qualquer segredo = bloqueante |
| Dependency check | `tool` | val | Snyk/npm audit/pip-audit; vulns críticas = bloqueante |
| OWASP Top 10 checklist | `prompt` | val | Na revisão, verificar riscos OWASP aplicáveis; registrar quais foram verificados |
| DAST | `tool` | val | OWASP ZAP baseline/full scan (ou ferramenta equivalente definida no Mapa) quando app disponível; findings high/critical = bloqueante |

### 4.2 Exemplos de ferramentas por stack (para sugestão)

Exemplos que o `sec` pode sugerir ao `curador-produto`
conforme o stack:

| Stack | Ferramenta | Tipo | Uso |
|-------|------------|------|-----|
| Node.js | Snyk | dep check | Registry privado, licenças |
| Node.js | eslint-plugin-security | SAST | Complementa Semgrep |
| Python | bandit | SAST | Padrões Python-específicos |
| Python | safety/pip-audit | dep check | Vulns em deps |
| Docker | trivy | image scan | Vulns em base images |
| Java/.NET | SonarQube | SAST | Regras enterprise |
| IaC | checkov/tflint | config scan | Terraform/CloudFormation |
| Go | gosec | SAST | Padrões Go-específicos |

**Nota**: o agente não hardcoda estas como obrigatórias.
O `sec` executa apenas o que estiver registrado no Mapa.

### 4.3 Ferramentas de DAST

| Ferramenta | Tipo | Custo | Uso |
|------------|------|-------|-----|
| OWASP ZAP | DAST black-box | Zero | Scan rápido: headers, configs, vulns comuns |

**ZAP via Docker (isolado)**:
```bash
docker run --rm --network sec-pentest-net \
  ghcr.io/zaproxy/zaproxy zap-baseline.py \
  -t http://<target>:<port>
```

> **Futuro**: pen testing automatizado com Shannon CLI
> será agregado em iteração posterior
> (ver `plan/sec-shannon-integration.md`).

### 4.4 Contexto WSL + Isolamento de Rede

**Ambiente**: o projeto roda em WSL. Ferramentas de
segurança ficam instaladas no WSL. A app alvo pode
rodar em Docker ou diretamente no WSL — varia por
projeto.

**Detecção de ambiente pelo agente**: ao iniciar testes
dinâmicos, verificar se está em Windows (VS Code via
Windows). Se sim, invocar via `wsl -- bash -ic "..."`.

**Isolamento de rede** (para pen testing):

```bash
# Criar rede Docker sem gateway externo
docker network create --internal sec-pentest-net
```

- Se app roda em Docker: conectar à mesma rede isolada
  (`docker network connect sec-pentest-net <app>`)
- Se app roda direto no WSL: usar iptables para
  restringir saída apenas a ranges privados
  (10.x, 172.16.x, 192.168.x, 127.x)

Isso garante que ferramentas de pen test não acessem
a rede pública — apenas alvos locais/staging.

**Bootstrap**: script `scripts/bootstrap_repo/harness-install.sh`
instala no WSL:
- Docker (se não disponível)
- gitleaks, semgrep (via pip/brew)
- Cria a rede `sec-pentest-net`

---

## 5. Modificações em testes

### 5.1 Teste existente: `tests/opencode-int-test/agents-test.bats`

Adicionar:

```bats
@test "behavioral: GET /agent lista o agente sec" {
  run curl -sf "${OPENCODE_BASE_URL}/agent"
  assert_success
  assert_output --partial "sec"
}
```

### 5.2 Nenhum outro teste existente é afetado

---

## 6. Checklist de entrega

- [ ] Criar `agents/sec.md` com frontmatter + corpo
- [ ] Adicionar teste em `agents-test.bats`
- [ ] Criar `scripts/bootstrap_repo/harness-install.sh`
- [ ] Criar `tests/scripts/bootstrap_repo/harness-install-test.bats`
- [ ] Atualizar `README.md` (seção dependências)
- [ ] Atualizar `docs/workflow-agentes-dev.md` (P27)
- [ ] Atualizar `docs/workflow-curadoria.md` (catálogo harness sec: DAST)
- [ ] Atualizar `agents/curador-produto.md` (catálogo condensado sec: DAST)
- [ ] Rodar `make test` — validar tudo
- [ ] Verificar que `vscode-sync.ps1` gera `sec.agent.md`
- [ ] Confirmar que `AGENTS.md` já lista `sec` (ou atualizar)

---

## 7. Decisões resolvidas

| # | Decisão | Resposta |
|---|---------|----------|
| 1 | Skills referenciadas | `security-and-hardening`, `code-review-and-quality`, `debugging-and-error-recovery` — suficiente |
| 2 | Nível de detalhe | Detalhado (mesma granularidade do `qa.md`) |
| 3 | Harness | Genérico (ferramentas do projeto, sem comandos hardcoded) |
| 4 | Pen testing no escopo | Sim — testes funcionais de segurança são do `sec` |
| 5 | DAST | OWASP ZAP via Docker no WSL |
| 6 | Pen testing (Shannon) | Segregado para iteração futura (`plan/sec-shannon-integration.md`) |
| 7 | Ambiente | WSL; detectar Windows e invocar via `wsl -- bash -ic` |
| 8 | Isolamento de rede | Docker `--internal` network; app pode estar em Docker ou WSL |

---

## 8. Mudanças necessárias nos workflows

### 8.1 `docs/workflow-agentes-dev.md`

**P27** — reformular de:
> Testes de segurança são do `sec`, não do `qa`.

Para:
> Testes de segurança são do `sec`, não do `qa`. Isso
> inclui testes dinâmicos (DAST, pen testing
> automatizado) — são testes funcionais especializados
> em segurança, não testes de lógica de negócio.

### 8.2 `docs/workflow-curadoria.md` (catálogo de harness)

Adicionar item DAST na seção `### sec`:
> - **DAST** `tool` `val`
>   OWASP ZAP baseline quando app disponível.
>   Findings de severidade high/critical são bloqueantes.

### 8.3 `agents/curador-produto.md` (catálogo condensado)

Adicionar na seção `### sec` do catálogo de referência:
> - **DAST** `tool` `val`
>   OWASP ZAP ou equivalente. high/critical = bloqueante.
