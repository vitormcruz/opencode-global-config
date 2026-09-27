# Plano — Revisão de Comunicação e Planejamento dos Agentes

## Overview

O humano anotou problemas de comunicação e de planejamento no uso dos
agentes. Este plano percorre os problemas item a item: para cada um,
ajustamos a formulação da regra e conferimos o resultado esperado
(comportamento observável e forma de verificar). O produto final é um
insumo de revisão e ajuste, autocontido, a ser executado pelo `devflow`,
que adapta ao projeto global (`harness-conf/`) o que for validado aqui.

Duas frentes, já acordadas em conversa anterior:

- **Comunicação**: regras que valem para todos os agentes. Testes de
  diálogo cobrem todos.
- **Planejamento**: protocolo específico de `smart-planner` e `devflow`.
  Revisores só entram se suas instruções mudarem.

## Problemas relatados pelo humano (insumo, 2026-09-27)

1. Abreviações demais na comunicação.
2. Referências a numerações do plano sem contexto: o humano não lê o
   plano; o agente apresenta o que está sendo discutido em termos
   simples, contextualizado, por partes; resumo dirigido ao final.
3. Texto demais quando o humano reclama, em vez de separar em partes.
4. Várias perguntas ao mesmo tempo exigindo muito contexto; o agente
   superestima a memória e a capacidade de processamento do humano.
5. Tool de pergunta com alternativas para questões sem entendimento
   confirmado, com alternativas aleatórias; usar só em escolhas
   fechadas e óbvias.
6. Contestação de premissa: assumir que o humano não leu o restante;
   reapresentar e, se necessário, ajustar o conteúdo dependente.
7. Perguntas demais sobre detalhe de escrita do plano; perguntar só o
   que afeta o resultado.
8. Esquecer o protocolo: texto longo ou resumo com informação que o
   humano não passou.
9. Avançar para ações durante resolução de dúvidas, sem terminar a
   discussão.
10. Planejador e revisor tratarem alteração como simples ou postergável
    sem autorização; padrão é cobrir tudo, salvo ordem explícita.
11. Pedir confirmação para detalhe de implementação que não muda
    premissas.

## Architecture Decisions

### Diretriz de localização (decisão do planejador, detalhe de
### implementação)

- Regras gerais de comunicação: `harness-conf/AGENTS.base.md`, seção
  Comunicação.
- Protocolo de perguntas, confirmação e ritmo da conversa: skill
  `question-orchestration`.
- Cobertura de escopo do planejamento e revisão: `smart-planner` e
  revisores.

### Regras aprovadas (item a item)

**Item 1 — Abreviações (aprovado).** Destino: `AGENTS.base.md`, seção
Comunicação, subseção "Sem abreviações":

- Escreva palavras por extenso; não abrevie palavras nem crie siglas
  próprias.
- Sigla consagrada da área técnica (TDD, API, CI) pode aparecer sem
  expansão.
- Sigla interna do projeto ou do plano, e termo de domínio afastado,
  exigem nome por extenso no primeiro uso, em linguagem simples.

Verificação: conversa roteirizada em que o agente explica uma decisão;
a transcrição não pode ter abreviação nem sigla sem definição. Caso
futuro da suíte de comunicação.

**Item 2 — Referências ao plano (aprovado).** Destino: `AGENTS.base.md`,
seção Comunicação, subseção "Conversa sobre plano" (reformulação):

- Plano e artefatos de estado são do agente; o humano não os lê.
- Toda pergunta, decisão ou discussão é autocontida: traga a fase atual,
  o trecho relevante e o escopo da questão, em termos simples.
- Nunca referencie número, código, sigla ou link interno do plano:
  apresente o conteúdo discutido, contextualizado.
- Apresente por partes: uma etapa ou decisão por vez. Resumo de etapas
  é permitido; ao encerrar, um resumo dirigido do todo, também por
  partes.

Verificação: conversa roteirizada com várias decisões em jogo; a
transcrição não pode ter número, código ou link do plano sem o conteúdo
contextualizado. Caso futuro da suíte de comunicação.

**Item 3 — Volume na comunicação (aprovado).** Destino: `AGENTS.base.md`,
seção Comunicação, seção Concisão (acréscimo operacional):

- Uma ideia central por resposta. Duas ou mais ideias? Separe e
  apresente uma por turno.
- Antes de enviar, confira: a resposta tem uma única ação ou decisão?
  Se não, corte o excedente e guarde para o turno seguinte.
- Reclamação de confusão: reapresente o ponto em menos linhas do que a
  mensagem original. Nunca reescreva tudo nem acrescente detalhe.
- Cada resposta se sustenta sozinha: antes da novidade, reapresente em
  uma linha o ponto da conversa a que ela se refere.

Verificação: conversa roteirizada; nenhuma resposta concentra mais de
uma ideia central por turno; resposta a reclamação de confusão menor
que a original. Caso futuro da suíte de comunicação.

## Task List

(tasks a definir após os itens do humano e as decisões)

## Risks and Mitigations

(a preencher)

## Open Questions

- Item 1 (abreviações) em discussão; itens 2 a 11 pendentes.
