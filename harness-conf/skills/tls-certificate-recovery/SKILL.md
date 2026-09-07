---
name: tls-certificate-recovery
description: >
  Diagnostica e resolve autonomamente erros de certificado TLS/SSL que
  ferramentas CLI (Python, Node, pip, npm, git, curl, huggingface_hub,
  docling, aws-cli etc.) encontram em maquinas corporativas com proxy de
  inspecao TLS, extraindo a cadeia de certificados ja confiada pelo sistema
  operacional (Windows certificate store ou bundle CA do Linux/WSL) para um
  bundle PEM reutilizavel, sem nunca desativar a validacao TLS. Use quando o
  agente encontrar/receber qualquer um destes sinais em stdout/stderr de um
  comando: "CERTIFICATE_VERIFY_FAILED", "self-signed certificate in
  certificate chain", "unable to get local issuer certificate", "unable to
  verify the first certificate", "certificate has expired",
  "SSLCertVerificationError", "SSLError", "certificate verify failed",
  "PKIX path building failed", "x509: certificate signed by unknown
  authority", "NET::ERR_CERT_AUTHORITY_INVALID",
  "DEPTH_ZERO_SELF_SIGNED_CERT", "UNABLE_TO_VERIFY_LEAF_SIGNATURE",
  "SEC_ERROR_UNKNOWN_ISSUER", "erro de certificado", "certificado nao
  confiavel", "certificado autoassinado", "falha de verificacao SSL/TLS",
  "problema de certificado", ou quando o humano disser "tenho problema de
  certificado", "erro de certificado nessa maquina", "configura o
  certificado pra mim", "resolve esse erro de TLS/SSL".
---

Voce e uma skill de diagnostico e recuperacao de erros de certificado
TLS/SSL em ferramentas de linha de comando.

## Objetivo

Quando uma ferramenta (Python/pip, Node/npm, git, curl, huggingface_hub,
docling, aws-cli, etc.) falha por nao conseguir validar a cadeia de
certificados TLS, resolver o problema **sem desativar a validacao TLS** e
**sem introduzir uma nova autoridade nao confiavel** — reaproveitando apenas
certificados que o proprio sistema operacional ja confia.

## Por que isso acontece

Muitas ferramentas escritas em Python/Node (via `certifi`, `httpx`,
`requests`, Node `https`) **nao consultam o repositorio de certificados do
SO** (Windows Certificate Store, `/etc/ssl/certs` no Linux). Em maquinas
corporativas com proxy de inspecao TLS (MITM), o certificado raiz do proxy
costuma **ja estar instalado e confiado pelo SO** (senao o navegador tambem
falharia), mas a ferramenta ainda falha porque usa sua propria lista de CAs
embutida, que nao inclui esse certificado corporativo.

## Quando usar

Ative esta skill automaticamente, sem perguntar antes de tentar, quando:
- Um comando falhar com qualquer sinal de erro de certificado listado na
  `description` desta skill.
- O humano relatar erro de certificado/TLS/SSL em qualquer ferramenta.

## Quando NAO usar / limites de autonomia

- **Nunca** desative validacao TLS para "resolver" o erro (ver secao
  "Nunca fazer").
- Se a extracao da cadeia do SO **nao resolver** o erro (ou seja, o
  certificado do proxy/CA corporativa nao esta nem no proprio SO), **pare**
  e pergunte ao humano por uma CA PEM corporativa aprovada ou um mirror
  aprovado — nunca baixe ou invente um certificado por conta propria.
- Mudancas de configuracao **persistentes e globais** (editar
  `~/.gitconfig`, `~/.npmrc`, `pip.conf` do sistema, variaveis de ambiente
  permanentes no perfil do shell) exigem confirmacao explicita do humano.
  Por padrao, aplique a correcao **apenas no escopo do comando/sessao atual**
  (variaveis de ambiente no processo, flags do comando).

## Fluxo obrigatorio

1. **Diagnosticar**: confirme que o erro e de validacao de cadeia de
   certificado (nao de rede/DNS/firewall/proxy-auth). Releia a mensagem de
   erro completa antes de agir.
2. **Extrair a cadeia confiavel do SO** para um bundle PEM estavel e
   reutilizavel (nao apagar entre execucoes):
    - Local padrao (cross-platform via `$HOME`):
     `~/.cache/tls-certificate-recovery/system-ca-bundle.pem`

   **Windows (PowerShell)** — exporta todos os certificados de
   Root e CA intermediarias confiados pelo usuario e pela maquina:
```powershell
  $bundle = Join-Path $env:USERPROFILE '.cache\tls-certificate-recovery\system-ca-bundle.pem'
   New-Item -ItemType Directory -Force -Path (Split-Path -Parent $bundle) | Out-Null
   $stores = @('Cert:\CurrentUser\Root','Cert:\CurrentUser\CA','Cert:\LocalMachine\Root','Cert:\LocalMachine\CA')
   $seen = @{}
   $blocks = New-Object System.Collections.Generic.List[string]
   foreach ($store in $stores) {
     foreach ($cert in (Get-ChildItem -Path $store -ErrorAction SilentlyContinue)) {
       $thumb = $cert.Thumbprint.ToUpperInvariant()
       if ($seen.ContainsKey($thumb)) { continue }
       $seen[$thumb] = $true
       $b64 = [Convert]::ToBase64String($cert.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert))
       $lines = New-Object System.Collections.Generic.List[string]
       for ($i = 0; $i -lt $b64.Length; $i += 64) { [void]$lines.Add($b64.Substring($i, [Math]::Min(64, $b64.Length - $i))) }
       [void]$blocks.Add("-----BEGIN CERTIFICATE-----`r`n$($lines -join "`r`n")`r`n-----END CERTIFICATE-----")
     }
   }
   Set-Content -Path $bundle -Value ($blocks -join "`r`n") -Encoding ascii
```

   **Linux/WSL** — reaproveita o bundle que o proprio SO ja usa (nao
   reconstroi do zero); so copia para o caminho padrao da skill:
```bash
  bundle="$HOME/.cache/tls-certificate-recovery/system-ca-bundle.pem"
   mkdir -p "$(dirname "$bundle")"
   for candidate in /etc/ssl/certs/ca-certificates.crt \
                    /etc/pki/tls/certs/ca-bundle.crt \
                    /etc/ssl/cert.pem; do
     if [ -f "$candidate" ]; then cp "$candidate" "$bundle"; break; fi
   done
```
   Se nenhum caminho existir e o erro persistir, isso indica que a CA
   corporativa **nao esta instalada nem no SO** — pare e escale ao humano
   (nao tente `update-ca-certificates`/instalar CA sem `sudo` e sem
   aprovacao explicita).

3. **Aplicar o bundle apenas no escopo do comando**, escolhendo a(s)
   variavel(is) certa(s) conforme a ferramenta que falhou:

   | Ferramenta | Variavel/flag |
   |---|---|
   | Python (`requests`, `httpx`, `pip`, `huggingface_hub`) | `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`, `PIP_CERT` |
   | Node.js / npm | `NODE_EXTRA_CA_CERTS` |
   | curl | `CURL_CA_BUNDLE` ou `curl --cacert <bundle>` |
   | git (por invocacao, sem alterar config global) | `GIT_SSL_CAINFO=<bundle> git ...` |
   | AWS CLI | `AWS_CA_BUNDLE` |
   | Geral/OpenSSL | `SSL_CERT_FILE` |

   Exemplo (PowerShell, escopo do processo):
```powershell
  $env:SSL_CERT_FILE = $bundle
   $env:REQUESTS_CA_BUNDLE = $bundle
```
   Exemplo (bash, escopo do processo):
```bash
  export SSL_CERT_FILE="$bundle"
   export REQUESTS_CA_BUNDLE="$bundle"
```

4. **Repetir o comando original** que falhou, com as variaveis aplicadas.
5. **Se funcionar**: informe ao humano, em poucas linhas, que a cadeia de
   certificados do SO foi extraida para o caminho do bundle e qual variavel
   resolveu o problema, para que ele saiba que nenhuma nova autoridade foi
   introduzida.
6. **Se persistir o erro de certificado** apos o passo 4: pare de tentar
   variacoes automaticamente. Pergunte ao humano (via `ask_user` quando
   disponivel) com duas opcoes: (a) caminho de uma CA PEM corporativa
   aprovada, ou (b) um mirror interno aprovado. Nao prossiga sem resposta.

## Nunca fazer

- Nunca desative validacao TLS: `--insecure`/`-k` (curl), `verify=False`
  (Python), `NODE_TLS_REJECT_UNAUTHORIZED=0`, `git config
  http.sslVerify false`, `npm config set strict-ssl false`,
  `PYTHONHTTPSVERIFY=0`.
- Nunca baixe um certificado de uma URL arbitraria e o adicione como
  confiavel "para funcionar".
- Nunca invente ou gere um certificado/CA por conta propria.
- Nunca oculte do humano que um bundle de certificados foi criado/alterado.
- Nunca altere configuracao global persistente (`~/.gitconfig`, `~/.npmrc`,
  `pip.conf` do sistema, variaveis de ambiente permanentes) sem confirmacao
  explicita do humano.

## Saida esperada

Ao concluir, resuma ao humano:
- Qual erro de certificado foi detectado.
- Caminho do bundle PEM gerado/reaproveitado.
- Quais variaveis de ambiente foram usadas e em qual escopo (processo atual,
  nao persistente).
- Confirmacao de que nenhuma validacao TLS foi desativada.
- Se precisou escalar, o que exatamente foi pedido ao humano.

## Caso de referencia

Em uma maquina Windows corporativa, `docling-tools models download` falhou
com `SSL: CERTIFICATE_VERIFY_FAILED: self-signed certificate in certificate
chain`ao acessar`huggingface.co\`. A skill extraiu os certificados de
`Cert:\CurrentUser\Root`, `Cert:\CurrentUser\CA`, `Cert:\LocalMachine\Root` e
`Cert:\LocalMachine\CA` para um bundle PEM, aplicou `SSL_CERT_FILE` e
`REQUESTS_CA_BUNDLE` no escopo do processo, e o download foi concluido com
sucesso sem qualquer alteracao permanente no sistema.
