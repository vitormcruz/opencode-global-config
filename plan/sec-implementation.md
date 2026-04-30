# Plano — Implementação do Agente `sec` (Analista Cyber)

Status: AGUARDANDO APROVAÇÃO DO HUMANO

---

## 1. Resumo

Criar `agents/sec.md` — executor com modos plan · build · val que:
- Analisa requisitos de segurança após plano de código (P24)
- Gera configs de segurança quando necessário
- Revisa e corrige segurança (achado · ação · severidade)
- Planeja e executa testes de segurança (P26 — exclusivo do sec)
- Retorna resumo ≤ 5 linhas ao orq

---

## 2. Comportamentos extraídos do workflow

### 2.1 Premissas que o afetam

| # | Regra | Origem |
|---|-------|--------|
| P2 | Resultado no arquivo + resumo curto (≤ 5 linhas) de volta ao orq | Premissa 2 |
| P3 | Instância nova a cada fase (obrigatório em voltas) | Premissa 3 |
| P11 | Revisão híbrida — revisores especializados revisam e corrigem | Premissa 11 |
| P12 | Revisores são instâncias limpas — nunca revisa na mesma instância que planejou/construiu | Premissa 12 |
| P13 | Avalia com base no plano aprovado e insumos originais do humano | Premissa 13 |
| P14 | Formato do resumo: Achado · Ação · Severidade (bloqueante ou melhoria) | Premissa 14 |
| P24 | sec analisa após plano de código do eng-software | Premissa 24 |
| P26 | Testes de segurança são do sec, não do qa | Premissa 26 |

### 2.2 Ações por fase do workflow

#### PLANEJAMENTO (spawnado por `orq`)
1. Recebe plano de implementação (já feito por `eng-software`) via
   arquivo de planejamento
2. Analisa requisitos de segurança decorrentes do plano:
   - Autenticação/autorização
   - Validação de entrada / sanitização
   - Criptografia em trânsito e em repouso
   - Gerenciamento de segredos
   - Superfície de ataque exposta
   - OWASP Top 10 aplicável ao contexto
3. Persiste requisitos de segurança no arquivo de planejamento
4. Retorna resumo ≤ 5 linhas ao `orq`

#### CONSTRUÇÃO (spawnado por `orq`)
1. Avalia se o plano de segurança exige configs explícitas
   (CSP headers, CORS, rate limiting, WAF rules, etc.)
2. Se necessário: gera/atualiza configs de segurança
3. Persiste artefatos no arquivo e/ou no repo
4. Retorna resumo ≤ 5 linhas ao `orq`

#### REVISÃO DO PLANO (instância limpa, spawnado por `orq`)
1. Lê o plano aprovado e insumos originais (P13)
2. Revisa aspectos de segurança do plano
3. Corrige se possível (P11)
4. Registra resumo no arquivo:
   - **Achado**: o que estava errado
   - **Ação**: o que foi corrigido
   - **Severidade**: bloqueante ou melhoria
5. Retorna resumo ao `orq`

#### REVISÃO DA CONSTRUÇÃO (instância limpa, spawnado por `orq`)
1. Lê o plano aprovado e insumos originais (P13)
2. Revisa segurança da implementação (código, configs, deps)
3. Corrige se possível (P11)
4. Registra resumo no arquivo (mesmo formato P14)
5. Retorna resumo ao `orq`

#### TESTES (spawnado por `orq`)
1. Planeja testes de segurança com base no plano e na
   implementação
2. Executa testes de segurança (SAST, secrets scan, dependency
   audit, pen-test automatizado conforme disponível)
3. Se falhas encontradas: registra no arquivo
4. Retorna resultado (resumo curto) ao `orq`

### 2.3 Limites explícitos (o que NÃO faz)
- Não planeja nem executa testes funcionais (isso é do `qa`)
- Não implementa lógica de negócio
- Não faz revisão integrativa (isso é do `rev`)
- Não modela dados (isso é do `dba`)

---

## 3. Artefato: `agents/sec.md`

### 3.1 Frontmatter

```yaml
---
description: >
  Analista Cyber do workflow multi-agente. Analisa requisitos
  de segurança pós-plano de código, gera configs de segurança,
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

**Justificativa `mode: primary`**: o workflow permite que
qualquer agente consulte o humano (premissa 4). No VS Code,
apenas agentes primários spawnados por outro agente conseguem
interagir com o humano.

**Justificativa `bash: allow`**: precisa executar ferramentas
de segurança (SAST, dependency audit, secrets scan).

### 3.2 Corpo (estrutura planejada)

Seções do markdown:

1. **Identidade** — Analista Cyber, PT-BR, foco em segurança
2. **Contexto de acionamento** — spawnado pelo `orq` ou pelo
   humano diretamente
3. **Modos**
   - **PLAN**: analisa requisitos de segurança pós-plano de
     código; entrega: lista de requisitos/riscos no arquivo
   - **BUILD**: gera configs de segurança; entrega: artefatos
     no repo
   - **VAL**: duas variantes:
     - Revisão (plano ou construção): revisa, corrige,
       devolve resumo (P14)
     - Testes de segurança: planeja, executa, reporta
4. **Contrato com orq** — resultado no arquivo + resumo ≤ 5
   linhas; instância limpa em revisões (P12)
5. **Ferramentas e técnicas** — referência ao que pode usar:
   - Análise estática (semgrep, bandit, eslint-security, etc.)
   - Dependency audit (npm audit, pip-audit, trivy, etc.)
   - Secrets scan (gitleaks, trufflehog)
   - Checklist OWASP Top 10
   - Revisão manual de fluxos de auth/authz
6. **Formato de saída na revisão** — template:
   ```
   - **Achado**: <descrição>
   - **Ação**: <o que foi corrigido>
   - **Severidade**: bloqueante | melhoria
   ```
7. **Limites** — o que não faz (seção 2.3 acima)

### 3.3 Compatibilidade VS Code

O `vscode-sync.ps1` converterá `agents/sec.md` →
`sec.agent.md` em `%APPDATA%\Code\User\prompts\`:
- `Strip-AgentFrontmatter` manterá apenas `description`
- Resultado funcional sem alterações no script de sync

---

## 4. Relação com a skill `security-and-hardening`

A skill `skills/security-and-hardening/SKILL.md` já existe no
repo e contém checklist OWASP, padrões de hardening e
referências. O agente `sec` deve:
- Referenciar a skill como recurso de consulta (não duplicar)
- Usar o checklist da skill como base para revisões
- Manter separação clara: a skill é conhecimento estático;
  o agente é comportamento orquestrado

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

Os demais arquivos de teste (`commands-test.bats`,
`skills-activation-test.bats`, `mcp-test.bats`,
`prompts-test.bats`) não tocam em agentes e não precisam
de alteração.

---

## 6. Checklist de entrega

- [ ] Criar `agents/sec.md` com frontmatter + corpo
- [ ] Adicionar teste em `agents-test.bats`
- [ ] Rodar `make test` — validar que o novo agente é listado
- [ ] Verificar que `vscode-sync.ps1` gera `sec.agent.md`
- [ ] Confirmar que `AGENTS.md` já lista `sec` (ou atualizar)

---

## 7. Decisões para o humano

1. **Ferramentas de segurança**: o corpo do agente deve listar
   ferramentas específicas (semgrep, trivy, gitleaks) ou
   manter genérico ("ferramentas disponíveis no projeto")?
2. **Interação com `security-and-hardening` skill**: o agente
   deve invocar a skill explicitamente ou apenas referenciá-la
   como conhecimento de background?
3. **Harness**: a seção "Harness por Agente" do workflow está
   vazia para `sec`. Deseja definir harnesses agora ou
   deixar para iteração futura?
