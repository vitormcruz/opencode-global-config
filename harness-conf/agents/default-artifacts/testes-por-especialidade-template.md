<!-- TEMPLATE: tabela-índice das suítes colada no AGENTS.md do
     projeto-alvo; aponta por âncora para a seção "Testes por
     Especialidade" do docs/README.md, que é o único spec. -->
## Testes por Especialidade

| Especialidade | Script |
|---------------|--------|
| backend | `testes-produto/backend` |
| dados | `testes-produto/dados` |
| segurança | `testes-produto/seguranca` |
| frontend | `testes-produto/frontend` |

Agregador: `testes-produto`

Chama as suítes da tabela e consolida o relatório; cada suíte roda
os checks e as specs executáveis da sua especialidade (via
Concordion, quando o projeto usa spec executável). Executado pelo
agente `qa` na fase Testes; a evidência é validada pelo
`curador-produto`. Testes dos scripts de suíte e do agregador:
`testes-produto/tests/`.

Spec: [docs/README.md#testes-por-especialidade](docs/README.md#testes-por-especialidade)
