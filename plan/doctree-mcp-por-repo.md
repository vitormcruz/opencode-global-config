# Plano — Doctree MCP por repo para OpenCode e Copilot

Status: PLANEJADO

---

## 1. Resumo

Separar a configuracao do Doctree por projeto, sem depender de um unico
servidor MCP global com variaveis de ambiente compartilhadas entre varios repos.

A ideia e tratar dois cenarios distintos:
- OpenCode
- GitHub Copilot via `avelino/mcp`

O bootstrap deste repo continua cuidando apenas da instalacao global das
ferramentas. A configuracao do Doctree para um projeto especifico passa a ser
responsabilidade do fluxo `/indexar-codebase` executado dentro do repo alvo.

Regra obrigatoria de compatibilidade: o fluxo atual do `/indexar-codebase`
precisa ser preservado. Antes de qualquer configuracao MCP do Doctree, ele deve
continuar verificando se existe `.env-doctree` e, se nao existir, continuar
perguntando ao humano quais pastas deseja indexar. Esse comportamento nao pode
ser removido nem atropelado pela nova arquitetura.

---

## 2. Problema

Hoje ha conflito entre:
- configuracao MCP global do `avelino/mcp`
- configuracao de corpus do Doctree por repo
- necessidade de indexar conjuntos de documentos diferentes por projeto

Exemplos:
- um repo pode usar apenas `./docs`
- outro pode usar `DOCS_ROOTS` com `./docs`, `./agents`, `./skills`, `./plan`

Se todos os projetos reutilizam o mesmo nome de servidor MCP e as mesmas vars de
ambiente globais, um projeto pode sobrescrever a configuracao do outro.

Isso e especialmente problematico quando ha varios projetos ativos no mesmo
ambiente.

---

## 3. Objetivo

Permitir que cada projeto tenha sua propria configuracao Doctree, com regras
claras para:
- instalacao do servidor no contexto do OpenCode
- instalacao da entrada no `servers.json` do `avelino/mcp` para Copilot
- definicao explicita de qual MCP o Copilot deve usar naquele repo
- fallback para configuracao generica quando o repo nao define corpus customizado
- preservacao do fluxo atual de definicao de `.env-doctree` pelo humano

---

## 4. Decisoes arquiteturais

### 4.1 Remover `scripts/doctree/doctree-run.sh`

O script atual mistura responsabilidades e criou ambiguidade entre:
- executar indexacao e sair
- subir o servidor MCP em stdio

Ele sera removido.

No novo desenho, a indexacao nao depende desse wrapper.

### 4.2 Configuracao global vs configuracao por repo

#### Bootstrap deste repo
O bootstrap deste repo:
- instala ferramentas globais
- nao configura um repo especifico para usar Doctree

Portanto, ele nao deve assumir corpus de um projeto arbitrario.

#### `/indexar-codebase`
O comando `/indexar-codebase`, executado no repo alvo, passa a ser o ponto
responsavel por configurar o Doctree daquele projeto.

---

## 5. Regras por ambiente

### 5.1 OpenCode

No OpenCode, a configuracao sera escrita no proprio projeto, dentro de
`.opencode/`.

O fluxo `/indexar-codebase` deve:
1. verificar se o Doctree esta instalado
2. se nao estiver, instalar
3. escrever a configuracao MCP do projeto em `.opencode/`
4. usar configuracao:
   - especifica, quando houver `.env-doctree` com `DOCS_ROOTS` ou `DOCS_ROOT`
   - generica, quando nao houver configuracao especifica

#### Regra de configuracao OpenCode
- se existir `.env-doctree` com corpus especifico, escrever essa configuracao no
  MCP local do projeto
- se nao existir, usar configuracao generica apontando para `./docs`
- o fluxo deve avisar explicitamente quando estiver usando a configuracao
  generica

### 5.2 Copilot + `avelino/mcp`

No Copilot, a configuracao MCP fica no arquivo global do `avelino/mcp`:
- `~/.config/mcp/servers.json`

Como esse arquivo e global, o projeto precisa receber uma entrada nomeada de
forma unica.

#### Nome da entrada
Padrao:
- `doctree-mcp-<basename-do-repo>`

Exemplo:
- repo `opencode-config` -> `doctree-mcp-opencode-config`

#### Regra de criacao da entrada
O fluxo `/indexar-codebase` deve:
- editar diretamente `~/.config/mcp/servers.json`
- criar ou atualizar a entrada `doctree-mcp-<basename>` quando o projeto tiver
  referencias de docs especificas
- usar a entrada generica `doctree-mcp` quando o projeto nao tiver configuracao
  especifica e usar apenas `./docs`
- avisar explicitamente quando estiver usando a entrada generica

#### Regra de env no Copilot
Como o `avelino/mcp` suporta `env` no `servers.json`, a entrada do projeto deve
carregar diretamente:
- `DOCS_ROOT`, quando aplicavel
- `DOCS_ROOTS`, quando aplicavel

Sem wrapper para resolver repo em runtime.

---

## 6. Instrucao local do Copilot no repo

Para evitar ambiguidade sobre qual MCP usar no projeto atual, o fluxo
`/indexar-codebase` deve gerar uma instruction local do Copilot dentro de:
- `.github/`

Arquivo previsto:
- `.github/copilot-doctree.instructions.md`

Essa instruction deve conter o nome ja resolvido do MCP para aquele projeto.

Exemplo conceitual:
- usar `doctree-mcp-opencode-config` neste repo
- ou usar `doctree-mcp` quando o projeto estiver na configuracao generica

Objetivo:
- nao depender de descoberta dinamica via wrapper
- deixar explicito para o agente qual servidor Doctree consultar

---

## 7. Fonte de verdade para configuracao especifica

A configuracao especifica do Doctree por projeto sera derivada de:
- `.env-doctree`

Campos relevantes:
- `DOCS_ROOT`
- `DOCS_ROOTS`

Regra:
- `DOCS_ROOTS` tem precedencia semantica quando definido para multiplas colecoes
- `DOCS_ROOT` cobre caso simples de corpus unico
- ausencia de ambos implica fallback generico para `./docs`
- antes de assumir esse fallback, o `/indexar-codebase` deve preservar o fluxo
  atual: verificar se `.env-doctree` existe e, se nao existir, perguntar ao
  humano quais pastas deseja indexar

---

## 8. Regras de naming

### 8.1 Identificador do projeto

Foi decidido usar:
- `basename` do diretorio do repo

Exemplo:
- `/mnt/c/Users/ur5y/Projetos/opencode-config` -> `opencode-config`

Observacao:
- se no futuro houver colisao entre repos com o mesmo basename, sera necessario
  evoluir para um slug mais forte
- por ora, `basename` foi aceito como suficiente

---

## 9. Fluxo detalhado do `/indexar-codebase`

### 9.1 Descoberta e preservacao do fluxo atual
1. identificar root do repo atual
2. obter `basename` do repo
3. verificar existencia de `.env-doctree`
4. se `.env-doctree` nao existir, preservar o comportamento atual:
   - listar pastas candidatas na raiz
   - perguntar ao humano quais pastas deseja indexar
   - criar `.env-doctree` conforme a escolha do humano
5. se `.env-doctree` existir, tratá-lo como fonte de verdade
6. extrair `DOCS_ROOT` e `DOCS_ROOTS`, se existirem
7. classificar configuracao:
   - especifica
   - generica

### 9.2 OpenCode
8. garantir que o Doctree esteja instalado
9. escrever configuracao MCP local em `.opencode/` com `env`
10. se a configuracao for generica, registrar aviso claro ao humano

### 9.3 Copilot
11. garantir que a entrada correta exista em `~/.config/mcp/servers.json`
12. se a configuracao for especifica:
    - criar/atualizar `doctree-mcp-<basename>`
13. se a configuracao for generica:
    - usar `doctree-mcp`
14. gerar `.github/copilot-doctree.instructions.md` com o nome do MCP resolvido
15. se a configuracao for generica, registrar aviso claro ao humano

### 9.4 Indexacao
16. executar a indexacao do corpus configurado
17. reportar resultado ao humano

---

## 10. Arquivos que devem mudar

### 10.1 Remover
- `scripts/doctree/doctree-run.sh`

### 10.2 Atualizar
- `commands/index-codebase.md`
- `README.md` se houver impacto em instalacao ou uso
- `AGENTS.md` se a regra global de descoberta Doctree precisar apontar para a
  nova instruction local do projeto
- scripts de sync/adaptacao do Copilot, se houver dependencia antiga do
  `doctree-run`

### 10.3 Criar ou passar a gerar
- `.github/copilot-doctree.instructions.md` no repo alvo
- configuracao MCP em `.opencode/` no repo alvo
- entradas especificas no `~/.config/mcp/servers.json`

---

## 11. Impactos e compatibilidade

### 11.1 Impactos positivos
- elimina conflito de variaveis globais entre multiplos projetos
- deixa explicito qual servidor Doctree usar em cada repo
- separa corretamente o papel do bootstrap global e da indexacao por projeto
- evita depender de wrapper para inferencia de contexto no Copilot

### 11.2 Riscos
- `basename` pode colidir entre projetos diferentes com mesmo nome de pasta
- `servers.json` pode acumular entradas orfas de projetos removidos
- instrucoes locais do Copilot podem ficar stale se o repo for renomeado

### 11.3 Mitigacoes
- registrar claramente o nome resolvido no arquivo de instruction local
- atualizar a entrada sempre que `/indexar-codebase` rodar
- considerar comando futuro de limpeza de entradas MCP orfas

---

## 12. Validacoes necessarias

### 12.1 OpenCode
- confirmar formato exato da configuracao MCP em `.opencode/`
- validar suporte a `env` com `DOCS_ROOTS`
- validar comportamento com fallback generico `./docs`

### 12.2 Copilot + `avelino/mcp`
- validar edicao segura de `~/.config/mcp/servers.json`
- validar funcionamento de entrada com `env` usando `DOCS_ROOTS`
- validar uso da instruction local `.github/copilot-doctree.instructions.md`

### 12.3 Fluxo de indexacao
- validar repo com apenas `./docs`
- validar repo com `DOCS_ROOT`
- validar repo com `DOCS_ROOTS`
- validar rerun idempotente de `/indexar-codebase`

---

## 13. Ordem recomendada de implementacao

1. escrever este plano
2. atualizar `commands/index-codebase.md` para refletir a nova arquitetura
3. remover referencias a `doctree-run.sh`
4. implementar escrita da configuracao OpenCode por projeto
5. implementar edicao do `servers.json` para Copilot
6. implementar geracao de `.github/copilot-doctree.instructions.md`
7. ajustar docs e testes
8. remover `scripts/doctree/doctree-run.sh`

---

## 14. Decisoes confirmadas nesta conversa

- remover `scripts/doctree/doctree-run.sh`
- o bootstrap deste repo nao configura um repo especifico para Doctree
- a configuracao especifica do projeto acontece no `/indexar-codebase`
- tratar sempre dois cenarios: OpenCode e Copilot
- no Copilot, editar diretamente `~/.config/mcp/servers.json`
- no Copilot, gerar uma instruction local em `.github/` com o nome resolvido do
  MCP do projeto
- usar `basename` como referencia do projeto
- sem wrapper de serve para resolver repo em runtime
- no OpenCode, usar configuracao MCP local do projeto com suporte a `env`
- quando nao houver configuracao especifica, usar a configuracao generica e
  avisar o humano
- preservar o comportamento atual do `/indexar-codebase` que pergunta ao humano
  sobre `.env-doctree` e sobre quais pastas indexar quando o arquivo nao existe

---

## 15. Pendencias abertas

- confirmar nome exato e formato do arquivo MCP local do OpenCode no repo alvo
- definir estrategia de limpeza futura para entradas orfas no `servers.json`
- decidir se `AGENTS.md` precisa mesmo ser alterado ou se a instruction local do
  Copilot e suficiente
