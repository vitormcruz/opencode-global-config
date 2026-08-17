# Workflow Agêntico Simples

## Propósito

Este documento define um ciclo genérico de planejar, executar e revisar uma mudança aprovada.
Ele não substitui os workflows especializados nem define fases, especialidades ou agentes do
`workflow-agentes-dev.md`.

## Papéis

| Papel | Responsabilidade |
|---|---|
| Humano | Aprova plano, autoriza execução, escolhe modelos e decide bloqueios. |
| Orquestrador | Mantém o plano, media decisões e cria instâncias por capacidade. |
| Executor | Implementa somente o escopo aprovado e reporta estado ou impedimento. |
| Revisor | Avalia independentemente o resultado e reporta aprovação ou achados. Não corrige. |

O plano é a fonte de verdade: registra decisões, estado, modelos, trabalho concluído, bloqueios
e relatórios de revisão. As instâncias não usam o histórico de conversa como substituto do plano.

## Máquina de Estados

```text
PLANEJANDO -> AGUARDANDO_APROVAÇÃO -> AGUARDANDO_AUTORIZAÇÃO
    -> EXECUTANDO -> REVISANDO -> APROVADO_TECNICAMENTE
                        |                    |
                        | achados            | finalização opcional de commit
                        v                    v
                   CORRIGINDO -> REVISANDO  COM_COMMIT_E_PLANO_REMOVIDO
                                               ou SEM_COMMIT
                                      |
                                      v
                                REPLANEJANDO -> EXECUTANDO ou REVISANDO
```

- A transição para `EXECUTANDO` requer plano aprovado e autorização explícita do humano.
- `REVISANDO` inicia somente depois de o executor concluir.
- Achados retornam a `CORRIGINDO`; após cada correção há uma nova instância revisora.
- Qualquer decisão pendente leva a `REPLANEJANDO`, nunca a uma decisão inventada pelo agente.

## Seleção por Capacidade e Plataforma

Antes de iniciar uma instância, o orquestrador detecta o mecanismo nativo de subagente oferecido
pela plataforma. Não presume nomes, ferramentas ou parâmetros universais.

| Plataforma | Seleção |
|---|---|
| OpenCode | Usa o agente genérico de construção que a plataforma expuser, como `build` quando disponível. |
| Copilot CLI | Usa o mecanismo padrão ou genérico de subagente disponível na instalação. |
| Sem capacidade compatível | Para o ciclo, registra o bloqueio e apresenta ao humano a alternativa compatível. |

O briefing é passado diretamente ao spawn a partir do plano. O fluxo não produz prompts ou
arquivos de handoff como saída normal.

## Modelos

O humano seleciona e o plano registra modelos separados para executor e revisor. O orquestrador
reutiliza essas escolhas em novas instâncias até uma alteração humana.

Quando a plataforma permite definir o modelo ao iniciar, a instância recebe o modelo do seu papel.
Quando não permite, o orquestrador instrui a troca manual e aguarda confirmação humana antes do
spawn. Não inicia uma instância com modelo diferente do escolhido sem essa confirmação.

## Bloqueios e Replanejamento

Executor ou revisor retorna ao orquestrador ao encontrar bloqueio, ambiguidade, risco ou requisito
novo. O orquestrador:

1. Persiste estado, impacto e trabalho concluído no plano.
2. Media a decisão diretamente com o humano.
3. Atualiza o plano após a decisão humana.
4. Cria uma nova instância no estado apropriado, com a capacidade e o modelo selecionados.

## Sessões Independentes e Término

Executor e revisor sempre são instâncias independentes. O revisor não corrige: seus achados voltam
ao executor em nova instância. Toda correção exige uma nova instância revisora independente.

A conclusão técnica ocorre somente após aprovação explícita do revisor, sem achados pendentes,
bloqueios, ambiguidades, riscos ou decisões humanas abertas. A aprovação do plano não encerra o
ciclo. A finalização opcional de commit não é um gate e não reabre a revisão.

## Finalização Opcional do Commit Local

Após a aprovação técnica, o orquestrador apresenta ao humano um resumo conciso, os arquivos da
unidade lógica aprovada e uma mensagem Conventional Commit sugerida. Em seguida, pergunta se pode
criar o commit local e aguarda confirmação explícita.

Com aprovação humana, prepara somente os arquivos da unidade lógica, remove o arquivo de planejamento
com `git rm`, revisa o `git diff --staged`, cria o commit local e informa o SHA. A remoção do plano
entra no mesmo commit local. Nunca executa `git push` sem nova confirmação explícita do humano.

Se o humano recusar ou adiar, a conclusão técnica permanece válida, e o plano e as mudanças ficam sem
commit.
