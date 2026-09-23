---
name: md-export
description: >
  Use quando o humano pedir para gerar documento Word, PowerPoint ou Excel
  a partir de arquivo Markdown, ou para exportar/converter um .md com
  template personalizado. Converte .md para docx, pptx ou xlsx usando
  Pandoc.
  Triggers: "exportar Markdown", "md para docx", "md para pptx", "md para
  xlsx", "gerar Word", "gerar PowerPoint", "md-export".
---

# md-export

Converte arquivos `.md` para `docx`, `pptx` ou `xlsx` usando Pandoc como
backend.

## Quando usar

- Humano pede para gerar `.docx`, `.pptx` ou `.xlsx` a partir de Markdown.
- Humano quer exportar um `.md` para Office, inclusive com template Word
  ou PowerPoint personalizado.

Não use se a entrada não for Markdown (`doc-extract` cobre outros
formatos) nem se a saída não for `docx`, `pptx` ou `xlsx`.

## Ferramenta

Comando: `opencode-md-export`

## Entrada (stdin, JSON)

```json
{
  "source":    "<caminho do arquivo .md>",
  "to":        "docx | pptx | xlsx",
  "outputDir": "<opcional: diretorio de saida>",
  "outputPath":"<opcional: caminho completo do arquivo de saida>",
  "template":  "<opcional: caminho do .docx ou .pptx de template>",
  "from":      "<opcional: formato de entrada, default gfm>",
  "toc":       "<opcional: true|false>",
  "metadata":  "<opcional: objeto key=value para -M>",
  "extraArgs": "<opcional: lista de strings com flags extras do pandoc>"
}
```

## Saída (stdout, 1 linha JSON)

```json
{
  "ok":        true,
  "engine":    "pandoc",
  "artifacts": ["<caminho do arquivo gerado>"],
  "stdout":    "<saida do pandoc>",
  "stderr":    "<erros/avisos do pandoc>",
  "hint":      "<instrucoes de instalacao se pandoc nao estiver disponivel>"
}
```

## Regras

1. Nunca sobrescrever arquivo existente sem `--force` explícito nas
   `extraArgs`.
2. `outputDir` default: `./out/md-export/<timestamp>/`.
3. `pandoc` fora do PATH nem do diretório portátil do repositório:
   retornar `ok: false` com `hint` de instalação; não instalar
   dependências.
4. Passe `source` como caminho absoluto ou relativo ao diretório de
   trabalho atual.

## Exemplos de uso pelo agente

```json
{"source": "relatorio.md", "to": "docx"}
{"source": "apresentacao.md", "to": "pptx", "template": "templates/empresa.pptx"}
{"source": "doc.md", "to": "docx", "toc": true, "metadata": {"title": "Meu Relatorio", "author": "Time X"}}
{"source": "dados.md", "to": "xlsx", "outputPath": "saida/tabela.xlsx"}
```

## Instalação do pandoc (quando faltar)

- Recomendado: ZIP portátil oficial extraído em `tools/pandoc/`; no
  Windows, use o `pandoc.exe` do ZIP, sem instalação administrativa.
- Linux/WSL e macOS: ZIP portátil ou instalação user-space.
- Docs: https://pandoc.org/installing.html
