---
name: doc-extract
description: >
  Use quando o humano pedir para ler, analisar, resumir ou extrair dados de
  documento que não é Markdown (PDF, DOCX, PPTX, XLSX, HTML, imagem), ou
  quando uma URL apontar para arquivo binário que o crawl4ai não baixa
  (ERR_FAILED). Extrai conteúdo com Docling e converte para md, json,
  texto ou html.
  Triggers: "extrair PDF", "ler PDF", "converter PDF", "converter
  documento", "extrair texto de documento", "doc-extract", "URL binária".
---

# doc-extract

Extrai conteúdo de documentos não-Markdown com Docling e converte para
`md`, `json`, `text` ou `html`.

## Formatos

- Entrada (via Docling): `pdf`, `docx`, `pptx`, `xlsx`, `html`, `md`,
  `asciidoc`, `png`, `jpg`, `jpeg`, `tiff`, `bmp`, `gif`
- Saída: `md` (default), `json`, `text`, `html`

## Quando usar

- Humano pede para ler, analisar, resumir ou extrair dados de PDF, Word,
  PowerPoint, Excel ou imagem.
- URL aponta para arquivo binário (`crawl4ai` falha com `ERR_FAILED`):
  `.pdf`, `.docx`, `.pptx`, `.xlsx`, `.png`, `.jpg`, `.jpeg`, `.tiff`,
  `.bmp`, `.gif`.
- Humano quer converter um documento para Markdown para processamento
  posterior.

Não use se o arquivo já é `.md` (leia direto ou use `md-export` para
converter) nem para gerar documento (use `md-export`).

## Ferramenta

Comando: `opencode-doc-extract`

## Entrada (stdin, JSON)

```json
{
  "source":          "<caminho do arquivo ou URL>",
  "to":              "<opcional: md | json | text | html — default md>",
  "outputDir":       "<opcional: diretorio de saida>",
  "ocr":             "<opcional: true|false — default true>",
  "tables":          "<opcional: true|false — default true>",
  "imageExportMode": "<opcional: placeholder | embedded | referenced — default placeholder>",
  "extraArgs":       "<opcional: lista de strings com flags extras do docling>"
}
```

## Saída (stdout, 1 linha JSON)

```json
{
  "ok":        true,
  "engine":    "docling",
  "artifacts": ["<caminho(s) do(s) arquivo(s) gerado(s)>"],
  "stdout":    "<saida do docling>",
  "stderr":    "<erros/avisos do docling>",
  "hint":      "<instrucoes de instalacao se docling nao estiver disponivel>"
}
```

## Regras

1. `outputDir` default: `./out/doc-extract/<timestamp>/`.
2. `docling` fora do PATH: retornar `ok: false` com `hint` de instalação;
   não instalar dependências.
3. PDF escaneado (sem texto): OCR ativo por default, executado pelo
   próprio Docling (sem `tesseract` nem `ocrmypdf`); desative com
   `"ocr": false` se o PDF já tem texto selecionável.
4. Leia o(s) arquivo(s) gerado(s) em `artifacts` para obter o conteúdo
   extraído.
5. **Imagens base64**: o Docling emite `![Image](data:image/...base64...)`
   em linhas longas que poluem o contexto. Ao ler o `.md` gerado, ignore
   linhas que começam com `![Image](data:image/`; o conteúdo útil está
   nas demais. `"imageExportMode": "placeholder"` (default) evita o
   problema na origem.
6. **Arquivos grandes**: navegue o `.md` gerado com `Read` e `offset`/
   `limit` por seções. Para achar informação específica sem ler tudo,
   delegue ao agente `Task/explore` uma pergunta objetiva; ele usa
   `Read`+`Grep` internamente e devolve só o trecho relevante.

## Exemplos de uso pelo agente

```json
{"source": "relatorio.pdf"}
{"source": "contrato.docx", "to": "json"}
{"source": "scan.pdf", "ocr": true, "to": "md"}
{"source": "doc_com_imagens.pdf", "imageExportMode": "referenced", "outputDir": "saida/"}
```

## Instalação do docling (quando faltar)

- Recomendado (pipx): `pipx install docling`; sem pipx:
  `pip install --user pipx && pipx ensurepath`
- Alternativa (pip): `pip install --user docling`
- Ubuntu/WSL: `python3 -m pip install --user pipx && pipx install docling`
- Docs: https://github.com/docling-project/docling
