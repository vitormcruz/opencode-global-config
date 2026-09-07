---
name: svg-to-image
description: Converte um SVG em PNG para exibir ao usuario final
---

Voce e uma skill de conversao de imagens.

Protocolo:

Entrada:
- SVG completo via stdin.

Execucao:
- Comando: `opencode-svgtoimage`
- Backend: Playwright/Chromium, compartilhado com a skill `browser-testing`

Saida em stdout (uma unica linha JSON):

```json
{"imagePath":"<caminho_png>","markdown":"![](<caminho_png>)"}
```

Uso:
- Agentes devem enviar o SVG cru via stdin para este script.
- Devem usar o campo `markdown` diretamente na resposta ao usuario.
- Nao requer `resvg` nem `rsvg-convert`.
