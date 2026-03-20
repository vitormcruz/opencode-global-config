---
name: svg-to-image
description: Converte um SVG em PNG para exibir ao usuario final
---

Voce e uma skill de conversao de imagens.

Protocolo:

Entrada:
- SVG completo via stdin.

Execucao:
- Script: ~/.config/opencode/scripts/opencode-svgtoimage

Saida em stdout (uma unica linha JSON):

```json
{"imagePath":"<caminho_png>","markdown":"![](<caminho_png>)"}
```

Uso:
- Agentes devem enviar o SVG cru via stdin para este script.
- Devem usar o campo `markdown` diretamente na resposta ao usuario.
