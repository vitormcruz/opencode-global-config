# Testes por Especialidade

Scripts por especialidade e o agregador `testes-produto`.
Interface JSON: `{ status, findings[] }`. Exit 0 = pass,
exit 1 = fail. Sem argumentos.

O agregador `testes-produto` chama as suítes definidas neste documento e
consolida o relatório. Falha se qualquer suíte falhar.

Critérios e ferramentas saem da definição das Diretrizes e Regras de Produto.

**PROIBIDO:** bypassar, comentar, remover ou condicionar
qualquer verificação. Ferramenta ausente não justifica
remoção. Reporte finding com instrução de instalação.

O `README.md` da documentação e o `AGENTS.md` do projeto apenas
referenciam este arquivo. Eles não reproduzem esta especificação.

## Dois níveis de teste

1. **Testes da aplicação**: validam o produto em desenvolvimento.
   Rodam via suítes e agregador `testes-produto`, executados pelo agente
   `qa` quando solicitado, sempre que uma funcionalidade é
   desenvolvida.
2. **Testes dos scripts de teste**: os scripts de suíte e o agregador são
   código e têm testes próprios em `testes-produto/tests/`, fora da suíte
   `-m all` (separação por path, sem marker novo). Esses testes cobrem
   exatamente o que este documento define. Rodam somente quando os scripts
   mudam, nunca no ciclo normal de desenvolvimento.

## backend

**Arquivo:** `testes-produto/backend`

**Descrição:** Testes e análise do pacote Python e dos scripts do repositório.

**O que deve conter:**

- Suíte pytest completa do ambiente corrente (`-m all`, executável do
  `.venv` do SO); teste falho = bloqueante
- Análise estática Python: ruff; violação = bloqueante
- Análise estática shell: shellcheck nos scripts `.sh`; violação =
  bloqueante
- Análise estática PowerShell: PSScriptAnalyzer nos scripts `.ps1`;
  violação = bloqueante
- Cobertura: pytest-cov; cobertura total abaixo de 70% = bloqueante.
  Enquanto o repositório estiver abaixo de 70%, implemente testes até atingir o mínimo
- Specs executáveis da especialidade backend, rodadas via Concordion com
  tradutor Python interno à suíte; spec falhando = bloqueante

**Ferramentas:** pytest (`.venv` do SO), ruff, shellcheck,
PSScriptAnalyzer, pytest-cov e Concordion.

**Critérios:** qualquer teste falho, violação de lint ou cobertura
abaixo de 70% = finding bloqueante. Ferramenta ausente = finding
bloqueante com instrução de instalação.

## segurança

**Arquivo:** `testes-produto/seguranca`

**Descrição:** Segurança, secrets, dependências e análise estática.

**O que deve conter:**

- Secrets scan com gitleaks no repositório inteiro; segredo detectado =
  bloqueante
- Auditoria de dependências Python com pip-audit; vulnerabilidade
  high/critical = bloqueante; demais severidades = melhoria
- SAST com bandit no código Python próprio; achado high/critical =
  bloqueante; demais = melhoria
- Specs executáveis da especialidade segurança, rodadas via Concordion
  com tradutor Python interno à suíte; spec falhando = bloqueante

**Ferramentas:** gitleaks, pip-audit, bandit e Concordion.

**Critérios:** segredo detectado, vulnerabilidade high/critical ou
achado SAST high/critical = finding bloqueante. Ferramenta ausente =
finding bloqueante com instrução de instalação. Ferramentas com rede
seguem retry de três tentativas; esgotado = finding bloqueante com
instrução de rede.

## Agregador

**Arquivo:** `testes-produto`

Chama as suítes definidas neste documento (`testes-produto/backend` e
`testes-produto/seguranca`) e consolida o relatório no fim.
`status` é `fail` se qualquer suíte falhar. Não reabre entrevista
nem inventa check. O agente `qa` executa quando solicitado;
o `curador-produto` valida a evidência da execução.

- Interface JSON `{ status, findings[] }` em stdout, UTF-8; progresso
  em stderr; exit 0 = pass; exit 1 = fail; sem argumentos; idempotente
- Suíte que não executa, por crash ou exit inesperado, = finding
  bloqueante com instrução de correção
- Retry de rede é interno a cada suíte, com três tentativas; esgotado =
  finding bloqueante com instrução de rede
- Os scripts de suíte e o agregador são código de produção: entram no
  mesmo scan e no mesmo nível de qualidade. É proibido afrouxar o gate
  para código de teste
