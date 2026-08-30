# Interface Padronizada de Harness

Scripts de harness seguem esta interface:

## Contrato de Saída

- **Sem argumentos** — paths e configs internos
- **UTF-8 forçado** em stdout/stderr. Ecoe o progresso em
  stderr, sem ecoar a linha JSON do resultado.
- **Saída stdout**: JSON:

```json
{
  "status": "pass | fail",
  "findings": [
    {
      "severity": "bloqueante | melhoria",
      "tool": "nome-da-ferramenta",
      "message": "descrição do problema"
    }
  ],
  "prompt": "instrução adicional (opcional)"
}
```

- **Exit code**: 0 = pass, 1 = fail
- **Idempotente**: mesmo script para construção e revisão

## Retry e Falhas

- Em falha transitória de rede, até 3 tentativas; esgotado é
  finding bloqueante com instrução para chamar o humano e
  resolver a rede.

## Proibições

- Não bypassar verificações, usar `failOnViolation=false`,
  excluir teste do scan, usar fail-open em audit ou cache sem
  fallback.
- Ferramenta ausente é finding `bloqueante`: instale a
  ferramenta ou remova-a do harness e ajuste, salvo se o
  humano retirar o check do escopo.

## Pass-through

Se o humano não definiu ferramentas para um agente, o script
retorna `{ "status": "pass", "findings": [], "prompt": "" }`
sem verificações.

## Orçamento de Tempo

Tetos sugeridos, ajustáveis pelo humano:

| Categoria | Teto |
|-----------|------|
| Check isolado barato | < 15s |
| Harness quente (cache hit) | < 30s |
| Harness frio aceitável | < 3 min |
| Soma dos seis no caminho quente | < 10 min |

Estouro exige aprovação explícita e motivo.

## Avaliação de Ferramenta

Quando o humano oferece uma ferramenta, analise estes pontos:

1. Qual risco outro check aprovado não pega
2. Se está no toolchain (wrapper, registry e licença)
3. Qual o tempo esperado
4. Se é bloqueante ou melhoria
5. Se, sendo cara e determinística, precisa de fingerprint
   SHA-256 em `harness/target/` (não versionado), com fallback
   para a suíte completa

## Agregador de Harness

- Fica na seção própria `## Agregador de Harness` do `AGENTS.md`
- Comando sem argumentos (padrão: `harness/agregar`)
- Destino: `docs/harness-report/harness-report.md`
- É um script coletor, **não** um gate que reexecuta harnesses
- Artefatos em dados estruturados nativos (JSON/JUnit) para o
  script montar tabelas no MD
- HTML (ou report não resumível) é copiado para subpasta
  `docs/harness-report/<ferramenta>/` e linkado
- Regeneração substitui a subpasta; origem ausente → MD declara
  ausente
- Links só para a cópia; nunca para `target/` nem path de build

## Cobertura Estática

O código de teste entra no mesmo scan e no mesmo nível de
qualidade que produção. Proibido afrouxar o gate.
