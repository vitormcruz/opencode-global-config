# Plano — Integração do Shannon CLI ao Agente `sec`

Status: FUTURO (não priorizado)

---

## 1. Resumo

Agregar o Shannon CLI como ferramenta de pen testing
automatizado ao agente `sec`. Complementa o OWASP ZAP
(DAST black-box) com análise white-box code-aware e
geração de PoC exploits.

Pré-requisito: agente `sec` implementado e funcional
(ver `plan/sec-implementation.md`).

---

## 2. O que é o Shannon

- AI pentester autônomo (KeygraphHQ/shannon)
- White-box: analisa código-fonte + explora dinamicamente
- Cobertura: Injection, XSS, SSRF, Auth bypass, Authz
- Política "No Exploit, No Report" — zero falso positivo
- AGPL-3.0 (livre para uso interno)
- 96.15% no benchmark XBOW

---

## 3. Shannon vs OWASP ZAP

| Aspecto | OWASP ZAP | Shannon |
|---------|-----------|---------|
| Tipo | Black-box DAST | White-box AI pentest |
| Analisa código | Não | Sim |
| Prova exploitabilidade | Não | Sim (só reporta com PoC) |
| Headers/configs | Excelente | Não foca |
| Custo por scan | Gratuito | Zero de LLM extra (modelo já disponível) |
| Tempo | Minutos | 1–1.5h |
| Falsos positivos | Muitos | Quase zero |

**Uso combinado**: ZAP primeiro (rápido), Shannon depois
(profundo). São complementares.

---

## 4. Execução no ambiente

**Requisitos**:
- Docker (já presente no setup do sec)
- Node.js no WSL (já presente via nvm)
- Rede isolada `sec-pentest-net` (já criada pelo bootstrap)

**Invocação**:
```bash
npx @keygraph/shannon start \
  -u http://<target>:<port> \
  -r /path/to/repo
```

**Custo LLM**: zero extra. O Shannon original exige API
key do Claude (~$50/scan). Porém, via o modelo já
disponível no VS Code/OpenCode, a orquestração fica
por conta do agente `sec` que invoca as ferramentas
subjacentes (Docker tools) sem chamada API separada.

**Alternativa equivalente**: usar as ferramentas Kali
(nmap, sqlmap, nuclei, nikto) diretamente via Docker,
com o agente `sec` orquestrando — mesmo conceito do
opencode-shannon-plugin, sem dependência do plugin.

---

## 5. Isolamento de rede

Mesma infraestrutura já definida no plano principal:
- `docker network create --internal sec-pentest-net`
- App target na mesma rede isolada
- Sem acesso à rede pública

---

## 6. O que muda no agente `sec`

Quando integrado:
- Capacidade 4 ganha sub-item "Pen testing automatizado"
- Harness do catálogo ganha item DAST/Pen testing
- Script de bootstrap instala Shannon CLI
- Instruções no corpo do agente para invocar Shannon

---

## 7. O que muda no workflow

**P27** — adicionar menção a pen testing:
> Testes de segurança são do `sec`, não do `qa`. Isso
> inclui testes dinâmicos (DAST, pen testing
> automatizado) — são testes funcionais especializados
> em segurança, não testes de lógica de negócio.

---

## 8. Plugin OpenCode (referência)

O `opencode-shannon-plugin` (vichhka-git) empacota 600+
tools Kali em Docker como tools do OpenCode. Não é
necessário para o VS Code — o agente `sec` já tem
`bash: allow` e acessa as mesmas ferramentas diretamente.

Referência: https://github.com/vichhka-git/opencode-shannon-plugin
