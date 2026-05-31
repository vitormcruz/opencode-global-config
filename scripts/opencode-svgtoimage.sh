#!/usr/bin/env bash
set -euo pipefail

# Diretorio temporario em /tmp
tmp_dir="$(mktemp -d /tmp/opencode-svgtoimage-XXXXXX)"
svg_file="$tmp_dir/diagram.svg"
png_file="$tmp_dir/diagram.png"

# Le o SVG completo do stdin e grava no arquivo temporario
cat > "$svg_file"

# Escolhe o binario de conversao (permite forcar via SVG2PNG_BIN)
tool="${SVG2PNG_BIN:-auto}"

if [ "$tool" = "auto" ]; then
  if command -v resvg >/dev/null 2>&1; then
    tool="resvg"
  elif command -v rsvg-convert >/dev/null 2>&1; then
    tool="rsvg-convert"
  else
    echo "Nenhum conversor encontrado (resvg ou rsvg-convert)" >&2
    exit 1
  fi
fi

case "$tool" in
  resvg)
    # resvg <entrada.svg> <saida.png>
    resvg "$svg_file" "$png_file"
    ;;
  rsvg-convert)
    # rsvg-convert -o saida.png entrada.svg
    rsvg-convert -o "$png_file" "$svg_file"
    ;;
  *)
    echo "Conversor nao suportado: $tool" >&2
    exit 1
    ;;
esac

# Resposta para o agente em JSON simples (uma linha)
cat <<EOF
{"imagePath":"$png_file","markdown":"![]($png_file)"}
EOF

# Tentativa opcional de abrir a imagem no Windows quando rodando via WSL.
# Nao gera nenhuma saida extra (para nao quebrar o JSON acima).
if command -v explorer.exe >/dev/null 2>&1 && command -v wslpath >/dev/null 2>&1; then
  win_path="$(wslpath -w "$png_file" 2>/dev/null || true)"
  if [ -n "$win_path" ]; then
    explorer.exe "$win_path" >/dev/null 2>&1 || true
  fi
fi
