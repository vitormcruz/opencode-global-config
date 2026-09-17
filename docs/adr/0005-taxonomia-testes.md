# ADR-0005: Taxonomia de testes agnóstica de SO e harness

- **Status:** Aceita
- **Data:** 2026-09-10
- **Escopo:** suíte pytest, registro de markers, documentação de comandos de teste
- **Revoga:** decisão 5 da ADR-0004 (execução das integrações atrelada a SO)

## Contexto

Os markers de teste misturavam dois eixos independentes: o harness exercitado
(`opencode`, `copilot`) e o sistema operacional onde a suíte rodava (`tools`
como proxy de Linux/WSL). Com os adapters multiplataforma (ADR-0004), essa
amarra virou incorreta: o mesmo teste de adapter vale nos três ambientes, e
testes de symlink são inaplicáveis no Windows por capacidade de SO, não por
harness. A seleção por marker havia virado seleção por plataforma por
acidente.

## Decisão

A suíte passa a usar quatro markers, nenhum deles nomeando harness ou SO:

1. **`unit`** — testes sem premissas externas: rodam em qualquer ambiente
   com o venv do repo.
2. **`integration`** — testes com qualquer premissa externa: ferramenta no
   PATH (playwright, docling, crwl, codebase-memory), binário de harness
   (Copilot CLI), Docker, ou capacidade do SO (symlink).
3. **`agent_eval`** — avaliação comportamental de agente com modelo local
   llama-server + Qwen3-0.6B no container Docker do OpenCode. Demorada;
   nunca entra em seleções padrão.
4. **`all`** — atalho de seleção traduzido literalmente para
   `unit or integration` pelo conftest raiz antes da seleção. Nunca inclui
   `agent_eval`. A tradução é documentada e literal: nada além do token
   `all` é alterado na expressão pedida; não há exclusão escondida.

Os markers `tools`, `opencode`, `copilot` e `opencode_context` são
revogados: saem do registro do `pyproject.toml` e do vocabulário da suíte.
O marker utilitário de fixture `opencode_context` passa a ser
`agent_eval_context`, com a mesma semântica.

## Requisito de ambiente declarado no próprio teste

Teste que exige capacidade de SO declara a restrição em si mesmo via
`skipif` com reason claro — hoje `requires_symlink` ("exige symlink
(POSIX)"), definido em `tests/platform_requirements.py` e aplicado aos 17
testes que exercitam symlink real. A suíte não executa o teste onde a
capacidade não se aplica e o relatório mostra o que não rodou e por quê. O
mecanismo é simétrico: testes exclusivos de Windows no futuro declaram o
próprio `skipif` pelo mesmo padrão. Nenhum hook escondido altera a seleção
pedida — quem seleciona é sempre a expressão `-m` do comando.

## Fronteira suíte/agente

O `skipif` de plataforma é mecanismo da suíte declarado no próprio teste; não
autoriza o agente a deixar de rodar teste. A regra do `AGENTS.md` permanece
intacta: o agente roda sempre a suíte completa do ambiente corrente e,
quando um pré-requisito externo não está disponível, usa `pytest.fail` com
mensagem clara e acionável — nunca seleção reduzida, nunca silêncio.

## Consequências

- Os comandos crus documentados são `-m unit`, `-m integration`, `-m all` e
  `-m agent_eval`, iguais em WSL/Linux e Windows (muda apenas o executável
  do venv).
- `-m integration` no WSL executa os testes de symlink; no Windows eles
  aparecem como skipped com o reason declarado — comportamento esperado e
  visível no relatório.
- `-m agent_eval` requer Docker e o llama-server local no WSL/Linux.
- Wrapper de execução único (`repo-test`) foi dispensado: os comandos crus
  ficam documentados no README e no AGENTS.md.

## Alternativas rejeitadas

- Wrapper `repo-test` traduzindo markers por SO: esconderia a seleção e
  criaria um segundo vocabulário além do pytest.
- Hook global desmarcando testes por plataforma: seleção escondida, contra
  o princípio da fronteira suíte/agente.
- Manter `tools`/`opencode`/`copilot` como aliases dos markers novos:
  perpetuaria o proxy de plataforma e o vocabulário por harness.

## Asserções executáveis

A fixture Concordion deste ADR expõe `executarVerificacoes()` e `veredito`.
A diretiva `execute` executa os checks preservados abaixo. A diretiva
`assertEquals` fixa o veredito esperado da decisão.

- [Executar as verificações deste ADR](#execute=executarVerificacoes()).

- `tests/test_taxonomy.py` compara via subprocess que `-m all` seleciona
  exatamente a união de `-m unit` com `-m integration`, que `all` não
  inclui `agent_eval`, e que marker desconhecido continua sem selecionar
  teste.
- `tests/test_package_setup.py` exige o registro dos markers novos e a
  ausência dos revogados no `pyproject.toml`.
- O veredito agregado da implementação é [pass](#assertEquals=veredito).
