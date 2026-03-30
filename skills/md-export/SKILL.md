---
name: md-export
description: >
  Converte arquivos Markdown para docx, pptx ou xlsx usando Pandoc.
  Use quando o humano pedir para gerar um documento Word, PowerPoint ou Excel
  a partir de um arquivo .md ou de conteudo Markdown.
---

Voce e uma skill de exportacao de documentos Markdown.

## Objetivo

Converter arquivos `.md` para `docx`, `pptx` ou `xlsx` usando o Pandoc como backend.

## Quando usar

- Humano pede para gerar um `.docx`, `.pptx` ou `.xlsx` a partir de Markdown
- Humano quer exportar/converter um arquivo `.md` para Office
- Humano quer usar um template Word ou PowerPoint personalizado

## Quando nao usar

- Se o arquivo de entrada nao for Markdown (use `doc-extract` para outros formatos)
- Se o formato de saida nao for `docx`, `pptx` ou `xlsx`

## Ferramenta

Script: `~/.config/opencode/scripts/opencode-md-export`

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

## Saida (stdout, 1 linha JSON)

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

1. Nunca sobrescrever arquivo existente sem `--force` explicito nas `extraArgs`.
2. `outputDir` default: `./out/md-export/<timestamp>/`
3. Se `pandoc` nao estiver no PATH, retornar `ok: false` com `hint` de instalacao.
4. Nao tentar instalar dependencias; apenas informar.
5. O agente deve passar `source` como caminho absoluto ou relativo ao diretorio de trabalho atual.

## Exemplos de uso pelo agente

Converter para DOCX simples:
```json
{"source": "relatorio.md", "to": "docx"}
```

Converter para PPTX com template:
```json
{"source": "apresentacao.md", "to": "pptx", "template": "templates/empresa.pptx"}
```

Converter para DOCX com sumario e metadata:
```json
{"source": "doc.md", "to": "docx", "toc": true, "metadata": {"title": "Meu Relatorio", "author": "Time X"}}
```

Converter para XLSX (tabelas Markdown):
```json
{"source": "dados.md", "to": "xlsx", "outputPath": "saida/tabela.xlsx"}
```

## Sugestoes de instalacao (quando pandoc faltar)

- Ubuntu/WSL: `sudo apt-get update && sudo apt-get install -y pandoc`
- macOS: `brew install pandoc`
- Windows: `winget install JohnMacFarlane.Pandoc`
- Ou baixe em: https://pandoc.org/installing.html
