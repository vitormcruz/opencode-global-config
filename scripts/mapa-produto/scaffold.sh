#!/usr/bin/env bash
# scripts/mapa-produto/scaffold.sh
# Cria as seções vazias do /doc/README.md no arquivo destino.
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
if grep -q "^## Definição de Escopo" "$DEST" 2>/dev/null; then
  echo "Seção '## Definição de Escopo' já existe em $DEST. Nada a fazer."
  exit 0
fi

cat >> "$DEST" << 'EOF'

## Definição de Escopo

O analista deve elicitar:
- Requisitos funcionais e não funcionais
- Critérios de aceitação por exemplos
- Organizados por histórias de usuário
- Critérios devem referenciar requisitos funcionais
- Nenhum requisito pode ficar sem critério
Skill recomendada: (opcional — humano define)

## Elementos de Especificação

| Elemento | Formato/Ferramenta | Agente Responsável | Destino |
|----------|-------------------|-------------------|---------|
| (preencher) | | | |

## Regras de Documentação

(seções por elemento — preencher conforme necessidade)

## Estratégias de Indexação de Código

- (preencher com ferramentas selecionadas)
EOF

echo "Scaffold do /doc/README.md criado em: $DEST"
