---
name: question-orchestration
description: >
  Protocolo conversacional para smart-planner, devflow, analista e
  curador-produto-editor: conduz triagem, perguntas adaptativas e confirmações
  de decisão sem cansar o humano. Use quando precisar planejar por perguntas,
  mediar dúvidas de agentes, rotear decisões ou reduzir carga cognitiva.
  Triggers: "mediação de perguntas", "rotear perguntas", "perguntas de
  agentes", "devflow", "smart-planner", "analista", "curador-produto-editor",
  "elicitação de escopo", "curadoria de documentação", "organizar dúvidas",
  "escalar decisão", "planejamento interativo".
---

# Orquestração de Perguntas

## Escopo e fonte única

Esta skill é a fonte única do protocolo conversacional compartilhado por
smart-planner, devflow, analista e curador-produto-editor. Ela define como
triagem, perguntas e decisões são conduzidas; os agentes que a usam não devem
duplicar essas regras.

Não define a estrutura do plano nem a política de Git. Também não define
tarefas de domínio, persistência do plano, commits, handoff, replan ou
revisão.

## Modo direto

Use quando o agente conversa diretamente com o humano, como o smart-planner.

### Triagem de Contexto Inicial

O humano pode chegar com um **prompt inicial fraco**, pouco contexto ou sem
uma ideia clara do que quer.

1. Avalie se o contexto fornecido é suficiente.
2. Se não for, faça perguntas para aumentar o contexto.
3. Você pode usar o skill `prompt-improver` em si mesmo para refinar seu
   questionamento antes de apresentá-lo ao humano.
4. Só então prossiga para as perguntas de planejamento.

Premissa: assuma que o humano pode estar começando sem ter pensado bem no
prompt inicial.

## Modo mediado

Use quando um orquestrador recebe perguntas de agentes e as apresenta ao
humano, como o devflow.

1. Preserve a autoria técnica da pergunta: o mediador organiza e apresenta,
   mas não decide nem responde pelo humano.

### Apresentação e apoio

- Pergunta curta e objetiva → apresente diretamente.
- Pergunta elaborada, múltipla ou volumosa → serialize no próprio protocolo,
  apresentando uma pergunta por vez.

## Perguntas em blocos adaptativos

Conduza a conversa por perguntas em blocos adaptativos, com no máximo 4
perguntas por rodada, inclusive durante a triagem de contexto inicial.

- Perguntas complexas, dependentes entre si ou com muitos tópicos distintos
  devem ser apresentadas uma pergunta por vez.
- Perguntas provavelmente simples podem ser numeradas e enviadas juntas.
- Para cada pergunta, ofereça recomendação com justificativa.

Pense explicitamente em como apresentar as perguntas para que a discussão
**não seja cansativa**: nem por muitas rodadas de micro-perguntas simples,
nem por rodadas densas e confusas com várias perguntas complexas. O objetivo é
minimizar a carga cognitiva do humano.

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
