---
name: doc-extract
description: >
  Extrai conteudo de documentos (PDF, DOCX, PPTX, XLSX, HTML, imagens e outros)
  convertendo para Markdown, JSON, texto ou HTML usando Docling.
  Use quando: (1) o humano pedir para ler, analisar, resumir ou extrair dados
  de um arquivo que nao e Markdown; (2) uma URL apontar para arquivo binario
  (.pdf, .docx, .pptx, .xlsx, .png, .jpg etc.) — crawl4ai falha nesses casos
  com ERR_FAILED e doc-extract e o substituto correto.
---

Voce e uma skill de extracao de conteudo de documentos.

## Objetivo

Converter documentos nos formatos `pdf`, `docx`, `pptx`, `xlsx`, `html`, `imagens` e outros
para `md`, `json`, `text` ou `html`, facilitando que a IA leia e processe o conteudo.

## Quando usar

- Humano pede para ler, analisar, resumir ou extrair dados de um PDF, Word, PowerPoint, Excel etc.
- Humano quer converter um documento para Markdown para processamento posterior
- Humano quer extrair tabelas ou texto estruturado de um arquivo
- Humano quer que a IA "entenda" o conteudo de um documento existente
- **URL aponta para PDF, DOCX, PPTX, XLSX ou imagem** — `crawl4ai` falha com `ERR_FAILED` em arquivos
  binarios; use `doc-extract` sempre que a URL terminar em `.pdf`, `.docx`, `.pptx`, `.xlsx`, `.png`,
  `.jpg`, `.jpeg`, `.tiff`, `.bmp` ou `.gif`

## Quando nao usar

- Se o arquivo ja e `.md` (use diretamente ou `md-export` para converter para outro formato)
- Se o humano quiser gerar um documento (use `md-export`)

## Ferramenta

Script: `~/.config/opencode/scripts/opencode-doc-extract`

## Formatos de entrada suportados (via Docling)

`pdf`, `docx`, `pptx`, `xlsx`, `html`, `md`, `asciidoc`, `png`, `jpg`, `jpeg`, `tiff`, `bmp`, `gif`

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

## Saida (stdout, 1 linha JSON)

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

1. `outputDir` default: `./out/doc-extract/<timestamp>/`
2. Se `docling` nao estiver no PATH, retornar `ok: false` com `hint` de instalacao.
3. Nao tentar instalar dependencias; apenas informar.
4. Para PDFs escaneados (sem texto), OCR e ativado por padrao; desative com `"ocr": false` se o PDF
   ja tiver texto selecionavel.
5. O agente deve ler o(s) arquivo(s) gerados em `artifacts` para obter o conteudo extraido.
6. **Imagens base64 no output**: o Docling inclui imagens como `![Image](data:image/...base64...)`.
   Essas linhas sao longas e poluem o contexto. Ao ler o `.md` gerado, ignore linhas que comecem com
   `![Image](data:image/` — o conteudo util (texto, tabelas, headings) esta nas demais linhas.
   Para evitar o problema na origem, prefira `"imageExportMode": "placeholder"` (ja e o default).
7. **Arquivos grandes**: use `Read` com `offset` e `limit` para navegar o `.md` gerado em secoes
   (ex: `offset=1, limit=100`, depois `offset=101, limit=100`, etc.).
   Para extrair uma informacao especifica sem ler tudo, delegue ao agente `Task/explore` com uma
   pergunta objetiva — ele usa `Read offset+limit` e `Grep` internamente e devolve so o trecho
   relevante, economizando contexto.

## Exemplos de uso pelo agente

Extrair PDF para Markdown (default):
```json
{"source": "relatorio.pdf"}
```

Extrair DOCX para JSON (mais estruturado):
```json
{"source": "contrato.docx", "to": "json"}
```

Extrair PPTX para texto simples:
```json
{"source": "apresentacao.pptx", "to": "text"}
```

Extrair Excel para Markdown (tabelas):
```json
{"source": "planilha.xlsx", "to": "md"}
```

Extrair PDF escaneado com OCR:
```json
{"source": "scan.pdf", "ocr": true, "to": "md"}
```

Extrair PDF com imagens referenciadas:
```json
{"source": "doc_com_imagens.pdf", "imageExportMode": "referenced", "outputDir": "saida/"}
```

## Fluxo recomendado para analise

1. Chamar `doc-extract` com o arquivo
2. Ler o arquivo `.md` (ou `.json`) retornado em `artifacts`
3. Processar/analisar o conteudo extraido
4. Se necessario, gerar um novo documento com `md-export`

## Sugestoes de instalacao (quando docling faltar)

- Recomendado (pipx): `pipx install docling`
  - Se pipx nao estiver instalado: `pip install --user pipx && pipx ensurepath`
- Alternativa (pip): `pip install --user docling`
- Ubuntu/WSL (pipx via apt): `sudo apt-get install -y pipx && pipx install docling`
- Docs: https://github.com/docling-project/docling
