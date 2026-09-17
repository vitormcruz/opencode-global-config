# Interface Padronizada de Testes de Produto

Scripts de testes-produto seguem esta interface:

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
  ]
}
```

- **Exit code**: 0 = pass, 1 = fail
- **Idempotente**: repetir o script produz o mesmo veredicto

## Retry e Falhas

- Em falha transitória de rede, até 3 tentativas; esgotado é
  finding bloqueante com instrução para chamar o humano e
  resolver a rede.

## Proibições

- Não bypassar verificações, usar `failOnViolation=false`,
  excluir teste do scan, usar fail-open em audit ou cache sem
  fallback.
- Ferramenta ausente é finding `bloqueante`: instale a
  ferramenta ou remova-a dos testes-produto e ajuste, salvo se o
  humano retirar o check do escopo.

## Pass-through

Se o humano não definiu ferramentas para uma especialidade,
o script retorna `{ "status": "pass", "findings": [] }`
sem verificações.

## Orçamento de Tempo

Tetos sugeridos, ajustáveis pelo humano:

| Categoria | Teto |
|-----------|------|
| Check isolado barato | < 15s |
| Suíte quente (cache hit) | < 30s |
| Suíte fria aceitável | < 3 min |
| Soma das suítes no caminho quente | < 10 min |

Estouro exige aprovação explícita e motivo.

## Avaliação de Ferramenta

Quando o humano oferece uma ferramenta, analise estes pontos:

1. Qual risco outro check aprovado não pega
2. Se está no toolchain (wrapper, registry e licença)
3. Qual o tempo esperado
4. Se é bloqueante ou melhoria
5. Se, sendo cara e determinística, precisa de fingerprint
   SHA-256 em `testes-produto/target/` (não versionado), com
   fallback para a suíte completa

## Agregador

- Comando sem argumentos (padrão: `testes-produto`)
- Chama as quatro suítes (backend, dados, segurança, frontend)
  e consolida `findings`
- `status` é `fail` se qualquer suíte falhar
- Execução na fase Testes do workflow: agente `qa` (o script
  apenas agrega suítes)
- Evidência da execução validada pelo `curador-produto`
- Não substitui a entrevista de ferramentas por especialidade
- Especificação executável É UM TESTE: cada suíte roda
  internamente as specs executáveis da sua especialidade via
  Concordion (tradutor Python como infra interna da suíte, como o
  pytest é do backend)
- Os testes dos scripts de suíte e do agregador (suíte meta) vivem
  em `testes-produto/tests/`: fora da suíte `-m all` (separação por
  path, sem marker novo), rodam quando os scripts mudam

## Cobertura Estática

O código de teste entra no mesmo scan e no mesmo nível de
qualidade que produção. Proibido afrouxar o gate.
