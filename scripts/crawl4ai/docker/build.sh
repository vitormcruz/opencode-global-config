#!/bin/bash
# Build da imagem crawl4ai-sanitized a partir da imagem oficial
# Usage: bash build.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
IMAGE_NAME="crawl4ai-sanitized:latest"

echo "[INFO] Construindo imagem $IMAGE_NAME ..."
docker build -t "$IMAGE_NAME" "$SCRIPT_DIR"
echo "[OK] Imagem $IMAGE_NAME construida com sucesso"
