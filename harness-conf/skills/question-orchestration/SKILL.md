---
name: question-orchestration
description: >
  Use para planejar por perguntas, mediar dúvidas de agentes, rotear
  decisões ou confirmar escolhas com o humano. Protocolo conversacional:
  triagem, blocos adaptativos (até 4 perguntas por rodada), escape por
  resposta livre e registro só de decisão aprovada.
  Triggers: "mediação de perguntas", "agente mediador", "planejamento
  interativo", "protocolo conversacional", "elicitação de escopo",
  "curadoria de documentação", "rotear dúvidas de agentes", "confirmar
  decisões", "reduzir carga cognitiva", "organizar dúvidas", "escalar
  decisão".
---

# Orquestração de Perguntas

## Escopo e fonte única

Esta skill é a fonte única do protocolo conversacional compartilhado por
agentes que conversam com o humano, direta ou mediadamente. Ela define como
triagem, perguntas e decisões são conduzidas; os agentes que a usam não devem
duplicar essas regras.

Não define a estrutura do plano nem a política de Git. Também não define
tarefas de domínio, persistência do plano, commits, handoff, replan ou
revisão.

## Contextualização com artefato persistido

Quando existir artefato de planejamento ou de estado persistido (plano,
arquivo de estado, registro de decisões), toda interação com o humano —
pergunta, confirmação, decisão ou discussão — carrega o contexto relevante
do artefato: a fase atual, as decisões já registradas que afetam a pergunta
e o escopo em que a pergunta se insere.

Motivação: o artefato é do agente. O humano não está lendo-o; a informação
precisa vir até ele na conversa. Nunca presuma que o humano conhece o
conteúdo do artefato — traga o trecho relevante ao perguntar.

## Modo direto

Use quando o agente conversa diretamente com o humano.

### Triagem de Contexto Inicial

O humano pode chegar com um **prompt inicial fraco**, pouco contexto ou sem
uma ideia clara do que quer.

1. Avalie se o contexto fornecido é suficiente.
2. Se não for, faça perguntas para aumentar o contexto.
3. Você pode usar o skill `prompt-improver` em si mesmo para refinar seu
   questionamento antes de apresentá-lo ao humano.
4. Só então prossiga para as perguntas de planejamento.

## Modo mediado

Use quando um agente orquestrador recebe perguntas de agentes e as apresenta
ao humano.

1. Preserve a autoria técnica da pergunta: o mediador organiza e apresenta,
   mas não decide nem responde pelo humano.

### Apresentação e apoio

- Pergunta curta e objetiva → apresente diretamente.
- Pergunta elaborada, múltipla ou volumosa → serialize no próprio protocolo,
  apresentando uma pergunta por vez.

## Plano abstraído

- O humano aprova o plano, não o arquivo: aprova o plano que lhe foi
  apresentado na conversa, não o documento físico que o agente edita.
  Cabe ao agente abstrair o plano físico: traduzir o documento em
  conteúdo significativo, apresentado por partes, para aprovação e
  discussão. O arquivo fica como artefato interno, commitado e
  consultável para auditoria.

## O que perguntar

- Pergunte só o que tem efeito no resultado para o humano: decisão de
  escopo, comportamento ou risco. Detalhe de escrita do plano ou do
  artefato é do agente: resolva dentro do escopo aprovado e registre,
  sem perguntar.
- Antes de perguntar ou pedir confirmação, classifique a questão: é
  detalhe de implementação ou decisão de resultado? Detalhe de
  implementação não se discute com o humano: decida dentro do escopo
  aprovado, registre no artefato e siga. Só traz ao humano o que muda
  premissa, escopo, comportamento ou risco, ou algo novo não abordado
  no planejamento.

## Perguntas em blocos adaptativos

Uma pergunta por rodada é o padrão, inclusive durante a triagem de
contexto inicial.

- Agrupe só quando as duas condições valem: cada pergunta é entendível
  sem as outras, e nenhuma exige contexto novo nem lembrança de turnos
  anteriores. Mesmo assim, no máximo 4 perguntas por rodada.
- Perguntas dependentes entre si: uma pergunta por vez, na ordem da
  dependência.
- Pergunta que exige contexto novo: apresente sozinha, com o contexto
  reapresentado.
- Ofereça recomendação com justificativa quando houver contexto
  suficiente para comparar consequências; em pergunta de descoberta,
  peça o contexto sem antecipar uma escolha.

Pense explicitamente em como apresentar as perguntas para que a discussão
**não seja cansativa**: nem por muitas rodadas de micro-perguntas simples,
nem por rodadas densas e confusas com várias perguntas complexas. O objetivo é
minimizar a carga cognitiva do humano.

## Alternativa de escape obrigatória

Toda pergunta ao humano — via tool de perguntas do harness ou em texto —
oferece sempre um caminho de escape: resposta livre por texto, opção
explícita do tipo "Outro (responder por texto)" ou "Nenhuma das opções —
quero dar mais contexto". Nunca formule pergunta cujas únicas saídas sejam
as opções apresentadas. Quando a UI da tool aceitar resposta custom, o
escape ainda deve estar visível no enunciado ou nas opções — nunca
pressuposto.

## Uso da tool de pergunta

- Pergunte em texto livre como padrão; a resposta do humano vem como
  veio.
- A tool é exceção para casos muito simples: decisão clara e
  alternativas enumeráveis e determinísticas (poucas, completas,
  mutuamente exclusivas).
- Questão nova ou complexa: texto, nunca tool.
- Cada alternativa descreve a consequência real da escolha; nunca opção
  de enchimento.

## Confirmação e continuidade de decisões

- Não repita decisão já registrada no artefato de contexto aplicável.
- Uma escolha explícita para a pergunta apresentada pode ser registrada como
  aprovação.
- Uma contra-proposta, reformulação, dúvida ou resposta ambígua não pode ser
  registrada como decisão. Reapresente a formulação e pergunte: "Posso
  registrar assim?" Só um "sim" explícito, "pode registrar" ou equivalente
  aprova o registro.
- NUNCA pule um ramo independente por parecer óbvio. Cada ramo da árvore de
  decisões deve receber sua própria pergunta e aprovação.
- Contestação de premissa ou de parte do que foi explicado: assuma que o
  humano não leu o restante da mensagem original. Corrija o ponto
  contestado, verifique o que dependia da premissa contestada e
  reapresente o conteúdo dependente, ajustado se necessário. Não presuma
  que o restante foi lido ou aceito.
- Dúvida em aberto trava ação: enquanto uma pergunta ao humano estiver
  sem resposta, ou uma contestação estiver em resolução, não execute
  ação dependente (editar, delegar, commitar, avançar de fase). Resolva
  a dúvida primeiro.
- Fechamento com pendência: o plano pode ser concluído com pendência
  condicionante desde que a tarefa dependente fique travada como
  bloqueadora e a decisão pendente seja explícita; a aprovação do plano
  não aprova a pendência.

## Fechamento do plano

- Ao fechar o plano, apresente uma conferência final resumida: escopo
  coberto (tópicos curtos), o que ficou de fora (só com autorização
  registrada) e os riscos que poderiam mudar a escolha. Peça a aprovação
  em seguida. Aprofunde um tópico somente se o humano pedir. Nada é
  aprovado sem ter sido apresentado antes; o resumo não substitui a
  apresentação.
