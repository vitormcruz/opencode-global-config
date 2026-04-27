# Plano: Seleção de modelo via OPENCODE_CONFIG

## Contexto

O script `container-test-opencode.sh` hoje seleciona o modelo de teste
assim:

1. Se `OPENCODE_TEST_MODEL` já estiver definido, usa ele
2. Senão, lista modelos via `opencode --pure models` e tenta achar
   `big-pickle` automaticamente
3. Se não achar, pede escolha interativa

**Problema:** não há como reaproveitar os modelos já definidos no
`opencode.json` do usuário. O big-pickle é sempre o padrão.

## Objetivo

Antes de tentar big-pickle, verificar se a variável `OPENCODE_CONFIG`
aponta para um arquivo `opencode.json` válido. Se sim, extrair os
modelos distintos de `agent.*.model` e oferecê-los em seleção
interativa. Se não, manter o comportamento atual.

## Pré-requisitos

- `jq` disponível no container (já está no Dockerfile, linha 9)

## Passo a passo

### 1. Extrair modelos do config (nova função)

**Arquivo:** `tests/opencode-int-test/docker/container-test-opencode.sh`

Criar função `extract_models_from_config()`:

- Recebe o caminho do arquivo como argumento
- Usa `jq` para extrair valores únicos de `.agent[].model`
  (filtrando nulls)
- Retorna uma linha por modelo (stdout)
- Retorna 1 se nenhum modelo encontrado

```bash
extract_models_from_config() {
  local config_file="$1"
  jq -r '
    [.agent[]? | .model? // empty] | unique | .[]
  ' "$config_file" 2>/dev/null
}
```

### 2. Alterar `select_model_if_needed()`

**Arquivo:** `tests/opencode-int-test/docker/container-test-opencode.sh`

Inserir bloco **antes** da detecção de big-pickle (após o check de
`OPENCODE_TEST_MODEL`):

```
Se OPENCODE_CONFIG definido:
  Se arquivo existe:
    config_models = extract_models_from_config(OPENCODE_CONFIG)
    Se config_models não vazio:
      log "Modelos encontrados em OPENCODE_CONFIG"
      OPENCODE_TEST_MODEL = choose_model_interactively(config_models)
      return
    Senão:
      warn "Nenhum modelo encontrado em OPENCODE_CONFIG, usando detecção padrão"
  Senão:
    warn "OPENCODE_CONFIG aponta para arquivo inexistente: $OPENCODE_CONFIG"
```

### 3. Passar OPENCODE_CONFIG para o container

**Arquivo:** `tests/opencode-int-test/docker/container-test-opencode.sh`
— função `start_container()`

Adicionar `-e OPENCODE_CONFIG` no `docker run` caso a variável esteja
definida no host.

### 4. Testes BATS

**Arquivo:** `tests/opencode-int-test/docker/container-test-opencode-test.bats`

Cenários:

| # | Cenário                                      | Esperado                              |
|---|----------------------------------------------|---------------------------------------|
| 1 | `OPENCODE_CONFIG` com arquivo válido + modelos | `extract_models_from_config` retorna modelos |
| 2 | `OPENCODE_CONFIG` com arquivo sem `agent`     | Função retorna vazio (fallback)       |
| 3 | `OPENCODE_CONFIG` não definido                | Fluxo big-pickle (comportamento atual)|
| 4 | `OPENCODE_CONFIG` com arquivo inexistente     | Warn + fallback                       |
| 5 | Config com modelos duplicados                 | Retorna lista sem duplicatas          |

Abordagem: testar `extract_models_from_config` isoladamente com
fixtures JSON temporários (não precisa subir container).

### 5. Atualizar help do script

Adicionar menção a `OPENCODE_CONFIG` na seção `--help`.

### 6. Remover container existente

Antes de qualquer teste manual, remover o container atual (se existir)
para garantir que a próxima execução use a imagem atualizada:

```bash
docker rm -f opencode-config-test 2>/dev/null || true
```

### 7. Rodar testes

```bash
make test
```

Validar que todos os cenários do passo 4 passam e que os testes
existentes não quebraram.

## Ordem de execução

1. Criar função `extract_models_from_config`
2. Alterar `select_model_if_needed`
3. Alterar `start_container` (passthrough da env var)
4. Atualizar `--help`
5. Criar testes BATS
6. Remover container existente
7. Rodar `make test`
