---
name: tls-certificate-recovery
description: >
  Use quando ferramenta CLI (Python, Node, pip, npm, git, curl, huggingface_hub, docling, aws-cli etc.) falhar por
  validacao de cadeia de certificado TLS em maquina corporativa com proxy de inspecao TLS: extrai a cadeia ja confiada
  pelo SO para bundle PEM reutilizavel e aplica no escopo do comando, sem nunca desativar a validacao TLS. Ativa
  automaticamente ao detectar qualquer um destes sinais em stdout/stderr de comando, ou quando o humano reportar
  problema de certificado. Triggers: "CERTIFICATE_VERIFY_FAILED", "self-signed certificate in certificate chain",
  "unable to get local issuer certificate", "unable to verify the first certificate", "certificate has expired",
  "SSLCertVerificationError", "SSLError", "certificate verify failed", "PKIX path building failed", "x509: certificate
  signed by unknown authority", "NET::ERR_CERT_AUTHORITY_INVALID", "DEPTH_ZERO_SELF_SIGNED_CERT",
  "UNABLE_TO_VERIFY_LEAF_SIGNATURE", "SEC_ERROR_UNKNOWN_ISSUER", "erro de certificado", "certificado nao confiavel",
  "certificado autoassinado", "falha de verificacao SSL/TLS", "problema de certificado", ou quando o humano disser
  "tenho problema de certificado", "erro de certificado nessa maquina", "configura o certificado pra mim", "resolve
  esse erro de TLS/SSL".
---

# Recuperação de Certificado TLS/SSL

## Objetivo

Ferramenta CLI (Python/pip, Node/npm, git, curl, huggingface_hub, docling,
aws-cli etc.) falhou por não validar a cadeia de certificados TLS: resolver
**sem desativar a validação TLS** e **sem introduzir autoridade não
confiável**, reaproveitando apenas certificados que o próprio SO já confia.

## Causa raiz

Ferramentas Python/Node (`certifi`, `httpx`, `requests`, Node `https`) não
consultam o repositório de certificados do SO (Windows Certificate Store,
`/etc/ssl/certs` no Linux) e usam sua própria lista embutida de CAs. Em
máquina corporativa com proxy de inspeção TLS (MITM), a raiz do proxy já
está instalada e confiada pelo SO (o navegador funciona), mas a lista
embutida da ferramenta não a contém — e a ferramenta falha.

## Quando usar

Ative automaticamente, sem perguntar antes de tentar, quando:

- Um comando falha com qualquer sinal de erro de certificado listado na
  `description` desta skill.
- O humano relata erro de certificado/TLS/SSL em qualquer ferramenta.

## Limites de autonomia

- Mudança de configuração **persistente e global** (`~/.gitconfig`,
  `~/.npmrc`, `pip.conf` do sistema, variável de ambiente permanente no
  perfil do shell) exige confirmação explícita do humano. Por padrão,
  aplique a correção **apenas no escopo do comando/sessão atual**
  (variável de ambiente no processo, flag do comando).
- Se a extração da cadeia do SO não resolver (a CA corporativa não está
  nem no próprio SO), **pare** e pergunte ao humano por uma CA PEM
  corporativa aprovada ou um mirror aprovado. Nunca baixe nem invente um
  certificado por conta própria (ver "Nunca fazer").

## Fluxo obrigatório

1. **Diagnosticar**: confirme que o erro é de validação de cadeia de
   certificado, não de rede/DNS/firewall/proxy-auth. Releia a mensagem de
   erro completa antes de agir.
2. **Extrair a cadeia confiada pelo SO** para um bundle PEM estável e
   reutilizável (não apagado entre execuções) em
   `$HOME/.cache/tls-certificate-recovery/system-ca-bundle.pem`.

   **Windows (PowerShell)** — exporta os certificados de Root e CA
   intermediária confiados pelo usuário e pela máquina:
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
       $type = [System.Security.Cryptography.X509Certificates.X509ContentType]::Cert
       $b64 = [Convert]::ToBase64String($cert.Export($type))
       $lines = New-Object System.Collections.Generic.List[string]
       for ($i = 0; $i -lt $b64.Length; $i += 64) {
         [void]$lines.Add($b64.Substring($i, [Math]::Min(64, $b64.Length - $i)))
       }
       [void]$blocks.Add("-----BEGIN CERTIFICATE-----`r`n$($lines -join "`r`n")`r`n-----END CERTIFICATE-----")
     }
   }
   Set-Content -Path $bundle -Value ($blocks -join "`r`n") -Encoding ascii
   ```

   **Linux/WSL** — reaproveita o bundle que o próprio SO já usa (não
   reconstrói do zero); só copia para o caminho padrão da skill:
   ```bash
   bundle="$HOME/.cache/tls-certificate-recovery/system-ca-bundle.pem"
   mkdir -p "$(dirname "$bundle")"
   for candidate in /etc/ssl/certs/ca-certificates.crt \
                    /etc/pki/tls/certs/ca-bundle.crt \
                    /etc/ssl/cert.pem; do
     if [ -f "$candidate" ]; then cp "$candidate" "$bundle"; break; fi
   done
   ```

   Nenhum caminho existente e erro persistente = a CA corporativa não está
   nem no SO. **Pare** e escale ao humano; não tente
   `update-ca-certificates` nem instalar CA sem `sudo` e sem aprovação
   explícita.

3. **Aplicar o bundle apenas no escopo do comando**, com a variável certa
   para a ferramenta que falhou:

   | Ferramenta | Variável/flag |
   |---|---|
   | Python (`requests`, `httpx`, `pip`, `huggingface_hub`) | `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`, `PIP_CERT` |
   | Node.js / npm | `NODE_EXTRA_CA_CERTS` |
   | curl | `CURL_CA_BUNDLE` ou `curl --cacert <bundle>` |
   | git (por invocação, sem alterar config global) | `GIT_SSL_CAINFO=<bundle> git ...` |
   | AWS CLI | `AWS_CA_BUNDLE` |
   | Geral/OpenSSL | `SSL_CERT_FILE` |

   ```powershell
   $env:SSL_CERT_FILE = $bundle
   $env:REQUESTS_CA_BUNDLE = $bundle
   ```
   ```bash
   export SSL_CERT_FILE="$bundle"
   export REQUESTS_CA_BUNDLE="$bundle"
   ```

4. **Repetir o comando original** que falhou, com as variáveis aplicadas.
5. **Se resolver**: informe ao humano, em poucas linhas, que a cadeia do
   SO foi extraída para o caminho do bundle e qual variável resolveu —
   nenhuma autoridade nova foi introduzida.
6. **Se o erro persistir** após o passo 4: pare de tentar variações
   automaticamente. Pergunte ao humano (via `ask_user` quando disponível)
   entre: (a) caminho de uma CA PEM corporativa aprovada, ou (b) um mirror
   interno aprovado. Não prossiga sem resposta.

## Nunca fazer

- **Desativar validação TLS**: `--insecure`/`-k` (curl), `verify=False`
  (Python), `NODE_TLS_REJECT_UNAUTHORIZED=0`, `git config http.sslVerify
  false`, `npm config set strict-ssl false`, `PYTHONHTTPSVERIFY=0`.
- **Baixar** certificado de URL arbitrária para confiar "para funcionar".
- **Inventar ou gerar** certificado/CA por conta própria.
- **Ocultar** do humano que um bundle foi criado ou alterado.
- **Alterar** configuração global persistente sem confirmação explícita.

## Saída esperada

Ao concluir, resuma ao humano:

- Qual erro de certificado foi detectado.
- Caminho do bundle PEM gerado/reaproveitado.
- Quais variáveis de ambiente foram usadas e em qual escopo (processo
  atual, não persistente).
- Confirmação de que nenhuma validação TLS foi desativada.
- Se escalou: o que exatamente foi pedido ao humano.
