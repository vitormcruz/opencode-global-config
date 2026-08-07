# Relatorio de Scanner de Seguranca — opencode-global-config

**Data:** 2026-05-27
**Objetivo:** Identificar ferramentas gratuitas/OSS para verificar CVEs e
problemas de segurança conhecidos nos 29 artefatos instalados por este repo.

---

## 1. Matriz de Recomendacao: Ferramenta × Categoria

| Categoria | Artefatos | Ferramenta Recomendada | Instalacao |
|---|---|---|---|
| **PyPI** (pipx) | docling | `pip-audit` | `pipx install pip-audit` |
| **npm global** | Playwright, Exa e plugins OpenCode | `npm audit` | nativo do Node.js |
| **PyPI** (pipx) | crawl4ai | `pip-audit` | `pipx install pip-audit` |
| **APT system** | make, pandoc e jq | `debsecan` / `trivy rootfs` | `apt install debsecan` |
| **Tarballs GitHub** | bats-core, bats-support, bats-assert, bats-file | `trivy fs` / `grype .` | binario |
| **Script remoto** | nvm install.sh (via `curl | bash`) | Auditoria manual + `gpg --verify` | N/A |
| **Node.js via nvm** | Node.js 22 | `nvm audit` (Node.js --security-revert) + `npm audit` | nativo |
| **Chromium** | Playwright browser download | `npm audit` (monitorar playwright) | nativo |

---

## 2. Scanner Unico Consolidado: Trivy

**Trivy** (Aqua Security, Apache 2.0) e a recomendacao principal por cobrir
quase todas as categorias com um unico binario:

```
trivy fs /caminho/para/projeto     # escaneia diretorio local
trivy image nome:tag               # escaneia uma imagem quando necessario
trivy rootfs /                      # escaneia SO host (apt packages)
trivy sbom sbom.json               # escaneia SBOM gerado
```

### Cobertura do Trivy vs. necessidades do repo

| Funcionalidade | Trivy | Grype |
|---|---|---|
| PyPI packages | Sim (via lockfiles) | Sim |
| npm packages | Sim (package-lock.json) | Sim |
| Docker images | Sim | Sim |
| APT packages | Sim (rootfs/filesystem) | Sim (filesystem) |
| Tarballs/FS local | Sim (`trivy fs`) | Sim (`grype .`) |
| IaC misconfig | Sim | **Nao** |
| Secrets | Sim | **Nao** |
| Licenses | Sim | **Nao** |
| SBOM gen | Sim (SPDX, CycloneDX) | Via Syft (companion) |
| K8s scanning | Sim | **Nao** |
| Velocidade | Rapido | Muito rapido |
| Falsos positivos | Baixo | Baixo |

**Grype** e alternativa focada (SBOM-first), mas exige Syft para SBOM e nao
cobre IaC, secrets ou licenses — insuficiente sozinho para este repo.

### Prós/Contras do Trivy

| Pro | Contra |
|---|---|
| Scanner unico para 90% dos casos | Banco de dados inicial ~20 MB |
| Apache 2.0, 100% gratuito | Sem analise de alcance (reachability) |
| SBOM generation nativa | Relatorio HTML requer plugin externo |
| CI/CD integrado (GH Action, GitLab) | Diferencas de resultados vs. Grype (~80%) |
| Atualizacao diaria do DB | Sem remediacao automatica |

> **Nota:** Trivy e Grype usam bancos de dados de vulnerabilidade diferentes
> e frequentemente produzem resultados divergentes (pesquisa academica mostra
> ate 80% de diferenca em algumas imagens). Recomenda-se usar **ambos** em
> pipeline ou escolher um e documentar a cobertura esperada.

---

## 3. Uso Pratico: Comandos por Categoria

### 3.1 PyPI (docling)

```bash
pip-audit --local --format markdown
```

### 3.2 npm global

```bash
npm audit --omit dev
```

### 3.3 Crawl4AI (PyPI)

```bash
pip-audit --local --format markdown
```

### 3.4 APT system packages

```bash
# Debian
debsecan --suite bookworm --only-fixed

# Qualquer distro (via Trivy)
trivy rootfs /
```

### 3.5 Tarballs e diretorios locais

```bash
trivy fs /caminho/para/.opencode/
grype /caminho/para/scripts/
```

### 3.6 NVM / Node.js

```bash
nvm install 22  # usa a versao mais recente do Node
npm audit
```

---

## 4. Riscos Conhecidos Atualmente

### 4.1 Playwright (< 1.56.0) — CVEs Ativas

| CVE | Descricao | Severidade | Fixado em |
|---|---|---|---|
| CVE-2025-9611 | Missing Origin header validation no MCP | Media | 1.56.0 |
| CVE-2025-59288 | SSL certificate verification bypass no download de browsers | Alta (CVSS 8.7) | 1.56.0 |
| GHSA-qxm8-4v54-964r | curl -k permite MitM no installer | Critica (RCE) | 1.56.0 |

**Impacto neste repo:** O script `install-playwright.sh` usa `npx playwright
install chromium` — a gravidade depende da versao do Playwright instalada.
Urgente: verificar versao com `npx playwright --version` e atualizar.

### 4.2 Crawl4AI CLI

O `crawl4ai` e instalado via pipx e deve ser auditado como dependencia PyPI,
nao como imagem ou servico local.

### 4.3 NVM — CVE Corrigida

| CVE | Descricao | Severidade | Fixado em |
|---|---|---|---|
| CVE-2026-1665 | Command injection via NVM_AUTH_HEADER no wget path | Alta | nvm 0.40.4 |

**Status:** Script deste repo usa `nvm-sh/nvm v0.40.1`. Atualizar para
`v0.40.4` para corrigir esta CVE.

### 4.4 BATS, Docling, Graphifyy

Nenhuma CVE publica conhecida ate a data deste relatorio.

---

## 5. Pipeline Sugerido (Script Unico)

Criar `scripts/security-scan` que executa:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== 1. PyPI audit ==="
pip-audit --local --format markdown || true

echo "=== 2. npm audit ==="
npm audit --omit dev || true

echo "=== 3. Docker image scan ==="
if command -v trivy &>/dev/null; then
  docker images --format "{{.Repository}}:{{.Tag}}" |
    while IFS= read -r img; do
      trivy image --severity CRITICAL,HIGH "$img"
    done
fi

echo "=== 4. System packages ==="
if command -v debsecan &>/dev/null; then
  debsecan --suite "$(lsb_release -cs)" --only-fixed
fi

echo "=== 5. Filesystem scan (scripts/) ==="
if command -v trivy &>/dev/null; then
  trivy fs --scanners vuln,secret scripts/
fi

echo "=== 6. Version check ==="
npx playwright --version 2>/dev/null || echo "playwright not found"
nvm --version 2>/dev/null || echo "nvm not found"
```

---

## 6. Limitacoes

| Limitacao | Explicacao |
|---|---|
| **Sem reachability** | Trivy/Grype reportam CVEs mesmo se o codigo vulneravel nao for executado |
| **Tarballs sem lockfile** | BATS tarballs nao tem SBOM — Trivy escaneia apenas arquivos extraidos |
| **Scripts remotos (`curl | bash`)** | Nenhum scanner automatico cobre isso; requer auditoria manual |
| **Dependencias transitivas** | APT e npm tem dependencias que nao sao escaneadas recursivamente |
| **Falsos positivos** | `debsecan` no Ubuntu reporta CVEs Debian que nao se aplicam (uso limitado a Debian puro) |
| **Node.js versao movel** | `nvm install 22` instala a versao mais recente do minor — muda sem aviso |
| **Chromium sem scanner** | Binario do Chromium baixado pelo Playwright nao e escaneado |

---

## 7. Resumo de Acoes Recomendadas

| Prioridade | Acao | Artefato |
|---|---|---|
| **Alta** | Verificar versao do Playwright e atualizar para >= 1.56.0 | @playwright/test |
| **Alta** | Atualizar nvm de v0.40.1 para v0.40.4 | nvm |
| **Media** | Adicionar `scripts/security-scan` ao repo | Pipeline |
| **Media** | Fixar versao do Node.js (ex: `nvm install 22.14.0`) em vez de `22` | Node.js |
| **Baixa** | Avaliar switch de `debsecan` para `trivy rootfs` (portavel entre distros) | APT scan |
