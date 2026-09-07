---
name: spec-executavel
description: >
  Como escrever especificação executável — critérios de aceitação em texto
  legível que viram teste automatizado (o texto é a spec; o teste decorre
  dela). Use quando: escrever, revisar ou detalhar critérios de aceitação;
  criar cenários BDD/Gherkin; converter requisitos ou histórias em cenários
  automatizáveis; avaliar se um critério está bom o bastante para automatizar;
  estruturar `Esquema do Cenário` com `Exemplos`; escolher formato de spec
  executável; revisar specs Concordion ou ferramentas similares; ligar valores
  de regras de negócio ao código de teste. Triggers: "spec executável",
  "especificação executável", "critérios de aceitação", "critério de aceitação",
  "Gherkin", "BDD", "Cenário", "Esquema do Cenário", "Dado que", "Quando tento",
  "Então", "specification by example", "cenário verificável", "automatizar
  critérios", "concordion", "cucumber", "behavior driven".
---

# Especificação Executável

Spec executável é texto legível pelo humano que vira teste automatizado:
editar o texto muda o veredito do teste. Esta skill define como escrever e
revisar esse texto. Ela cobre o COMO escrever cada critério; definir QUAIS
cenários existem e como classificar requisitos é decisão de quem administra
o backlog, não daqui.

## Princípio central

**A spec está ótima quando o humano mexe no texto e o teste quebra.**

Corolário: linke ao máximo os valores definidos nas regras ao código de
teste — valores concretos e aspas duplas aparecem na spec apenas para
literais que mudam o veredito. Se trocar uma palavra do critério não muda o
teste correspondente, texto e teste estão soltos um do outro: aperte o link
(faça o teste ler do texto o valor que a regra define).

## Formato default: Gherkin (recomendação forte)

Gherkin é o formato recomendado por padrão: vocabulário controlado, estrutura
rígida e adoção ampla em ferramentas BDD.

**Cláusula de exceção**: avalie a adequação caso a caso. Se outro formato
expressar a regra melhor (ex.: tabela para matrizes de permissionamento),
proponha o formato alternativo ao humano e discuta antes de desviar. Sem
aprovação, mantenha Gherkin.

### Estrutura canônica do cenário

```gherkin
# language: pt
Cenário: <frase curta> (origem: <requisito/regra>)
  Dado que <contexto mínimo>
  E <contexto adicional, se precisar>
  Quando tento <ação>
  Então <resultado verificável>
  E <resultado adicional, se precisar>
```

- Exatamente 1 `Quando tento` por cenário (uma ação por vez); a forma de
  tentativa deixa o `Então` decidir o resultado, sem presumir sucesso.
- `Dado que`/`E` de contexto: o mínimo para o cenário fazer sentido.
- `Então` (+ `E`): verificações do resultado.

### Variações da mesma regra

Quando só os valores mudam e a regra é a mesma, use `Esquema do Cenário`
com `Exemplos` (tabela) em vez de repetir cenários:

```gherkin
# language: pt
Esquema do Cenário: <frase curta> (origem: <requisito/regra>)
  Dado que <contexto mínimo>
  Quando tento <ação> com <campo>
  Então <resultado verificável>

  Exemplos:
    | <campo> |
    | "A"     |
    | "B"     |
```

## Checklist de qualidade (aplique a cada cenário)

1. **Estrutura canônica**: `Cenário` + `Dado que` + `E` + exatamente
   1 `Quando tento` + `Então` (+ `E`).
2. **`Então` sempre verificável**: estado, registro criado/não criado,
   mensagem, regra aplicada — nunca frase vaga ("funciona", "está ok").
3. **Linguagem de negócio**: intenção e resultado observável; sem termos de
   UI ou implementação (tela, botão, endpoint, classe).
4. **Desambiguação real**: quando há risco de dupla interpretação (duas
   entidades ou identificadores possíveis), explicitar nome/id/matrícula no
   step que precisa.
5. **Repetição útil vs redundância**: repita no `Então` apenas o que valida
   estado/persistência (muda o veredito); contexto já fixado no `Dado que`
   não se repete em todo step.
6. **Consistência contextual**: os steps formam um todo coeso; não trate
   cada frase como isolada.
7. **Concisão**: cada passo carrega só o indispensável para validar.
8. **Link texto↔teste (princípio central)**: valores concretos e aspas
   duplas apenas para literais que mudam o veredito; ao máximo, o teste lê
   do texto os valores que a regra define.
9. **Persona/perfil**: inclua só quando o foco do cenário for
   permissão/controle de acesso.
10. **`Esquema do Cenário` + `Exemplos`** para variações da mesma regra.

## Meio e ferramenta

- **Arquivos Markdown são favorecidos** como meio da spec (difusão, review
  e versionamento naturais); exceções são possíveis quando a ferramenta de
  execução exigir outro formato.
- **Agnóstica de ferramenta**: os critérios acima valem para qualquer
  motor de execução. Concordion é um exemplo de ferramenta que executa
  specs escritas em Markdown; não é requisito nem recomendação exclusiva.

## Rastreabilidade

Todo cenário referencia a origem que o motivou — o requisito ou regra
existente (ex.: threat model → requisito de segurança; regra de limite →
requisito funcional). A referência é um link à origem (identificador ou
âncora), não uma cópia do texto de origem. Cenário sem origem identificável
é sinal de requisito implícito: traga a origem à tona antes de escrever.
