---
name: svg-to-image
description: >
  Use quando o humano pedir para converter SVG em imagem para exibição.
  Recebe o SVG cru via stdin, converte com opencode-svgtoimage
  (Playwright/Chromium) e devolve JSON com imagePath e markdown pronto.
  Triggers: "converter SVG", "SVG para PNG", "renderizar SVG",
  "svg-to-image".
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
