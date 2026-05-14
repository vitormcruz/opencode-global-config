#!/usr/bin/env bash
# scripts/mapa-produto/scaffold.sh
# Cria as seções vazias do Mapa do Produto no arquivo destino.
# Uso: scripts/mapa-produto/scaffold.sh <arquivo-destino>
# Idempotente: se seções já existem, não duplica.

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Uso: $0 <arquivo-destino>" >&2
  exit 1
fi

DEST="$1"

# Cria diretório se não existir
mkdir -p "$(dirname "$DEST")"

# Cria arquivo se não existir
touch "$DEST"

# Verifica se seção já existe
if grep -q "^## Mapa do Produto" "$DEST" 2>/dev/null; then
  echo "Seção '## Mapa do Produto' já existe em $DEST. Nada a fazer."
  exit 0
fi

cat >> "$DEST" << 'EOF'

## Mapa do Produto

### Elementos de Especificação

| Elemento | Formato/Ferramenta | Origem | Destino |
|----------|-------------------|--------|---------|
| (preencher) | | | |

### Regras de Documentação

(seções por elemento — preencher conforme necessidade)

### Harness por Agente

| Agente | Comando de Execução | Descrição |
|--------|--------------------|-----------|
| (preencher) | | |
EOF

echo "Scaffold do Mapa do Produto criado em: $DEST"
