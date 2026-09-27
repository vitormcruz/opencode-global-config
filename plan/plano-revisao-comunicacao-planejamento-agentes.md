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

## Task List

(tasks a definir após os itens do humano e as decisões)

## Risks and Mitigations

(a preencher)

## Open Questions

- Item 1 (abreviações) em discussão; itens 2 a 11 pendentes.
