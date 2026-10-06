# Regras de Negócio

Este documento consolida decisões aprovadas para o bootstrap, os adapters e o
fluxo de atualização de skills. Cada regra aponta uma verificação objetiva já
existente. Esta edição não cria testes.

## Bootstrap e ai-memory

1. **RN-001, configuração dos harnesses.** Por padrão, o bootstrap configura
   todos os harnesses instalados no sistema corrente. Harness ausente é
   ignorado com aviso. A opção `--harness` restringe a seleção. A instalação
   ocorre em user-space, sem `sudo` ou administrador.
   - **Verificação:** `tests/harnesses/test_factory.py` cobre a seleção padrão.
     `tests/bootstrap/test_installers.py` cobre instaladores user-space.
   - **Fonte:** ADR-0001 e ADR-0004.

2. **RN-002, provisionamento tudo-ou-nada.** O bootstrap habilita ai-memory
   somente após validar wrapper, imagem, container, volume e hooks. Docker
   ausente ou provisionamento incompleto desativa os hooks e remove as
   declarações MCP gerenciadas de todos os harnesses. Após resolver o
   pré-requisito, a reexecução conclui o provisionamento antes de habilitar MCP.
   - **Verificação:** `tests/bootstrap/test_ai_memory_provision.py`,
     `tests/harnesses/test_opencode.py` e `tests/harnesses/test_copilot.py`.
   - **Fonte:** P1, SEC-09, ADR-0008 e SEC-01..SEC-11/SEC-21 em
     `docs/specs/Seguranca.md`.

3. **RN-003, integridade dos artefatos.** O bootstrap baixa o wrapper oficial
   `v2.4.1` por HTTPS e valida o SHA-256 fixado no código. A imagem usa
   `akitaonrails/ai-memory:latest` qualificada pelo digest linux/amd64
   `5ce8700b2d0a5243370a544c805f86c32d19aaca2251ecae32d66c09d221ef6e`.
   O código também registra o digest do índice OCI
   `a626d115e0350afe934954c02c9064d30b708c58316763a9c6674ef5d0c8e3d9`.
   Falha de TLS ou divergência do checksum do wrapper bloqueia a instalação.
   - **Verificação:** SEC-01/SEC-02 em `docs/specs/Seguranca.md`,
     `src/opencode_config/bootstrap/ai_memory.py` e
     `tests/bootstrap/test_ai_memory_provision.py`.
   - **Fonte:** decisão posterior de pins em 2026-09-27, SEC-01/SEC-02.

4. **RN-004, isolamento de rede.** O container usa a rede Docker `internal`,
   sem rota de saída padrão. O bootstrap aceita publicação no host somente em
   `127.0.0.1:49374`. Sem publicação efetiva, usa o IPv4 privado do container
   após validar a conectividade e a resposta Host. O fallback não abre listener
   no host. A allowlist inclui o IPv4 do container.
   - **Verificação:** SEC-03/SEC-21 em `docs/specs/Seguranca.md` e
     `tests/bootstrap/test_ai_memory_provision.py`.
   - **Fonte:** S2, SEC-03, SEC-21 e ADR-0008.

5. **RN-005, dados e rollback.** O marcador `.bootstrap-mcp-url` fica em
   `~/.local/state/ai-memory/`, fora do volume `~/.local/share/ai-memory/`.
   O rollback remove a integração gerenciada e preserva o volume de dados.
   Os hooks de compactação ficam limitados ao OpenCode. O Copilot recebe o
   endpoint MCP, sem os hooks.
   - **Verificação:** SEC-07/SEC-08 em `docs/specs/Seguranca.md` e
     `tests/bootstrap/test_ai_memory_provision.py`.
   - **Fonte:** SEC-07/SEC-08 e ADR-0008.

## Atualização de skills externas

6. **RN-006, detecção somente leitura.** `harness-skills detect` compara
   commits e mostra mudanças sem gravar metadados ou aplicar conteúdo. O clone
   temporário fica fora do checkout e não usa submódulos. Se o clone shallow
   não contiver o SHA base, o comando busca o histórico completo. Conteúdo
   upstream não é executado e a saída é marcada como não confiável.
   - **Verificação:** `tests/skills_mgmt/test_upstream_detect.py` cobre estado
     read-only, aviso, remoção do clone e fallback do histórico.
   - **Fonte:** P3, SEC-12..SEC-14 e ADR-0007.

7. **RN-007, freeze sob decisão humana.** O campo
   `sincronizacao: congelada` exclui a skill de `sync`, `update` e detecção.
   O comando `list` exibe o estado. Nenhum subcomando cria ou remove o campo
   sozinho. A alteração exige decisão explícita do humano.
   - **Verificação:** `tests/skills_mgmt/test_sync.py` e
     `tests/skills_mgmt/test_upstream_detect.py` cobrem os subcomandos e a
     preservação do campo.
   - **Fonte:** P3 e ADR-0007.

8. **RN-008, aplicação e SHA do upstream.** O agente avalia as mudanças,
   resume a recomendação e aguarda a decisão humana. Uma recusa sem freeze
   mantém o SHA anterior, para que a mudança reapareça na próxima detecção.
   Uma atualização aprovada usa edição assistida. O SHA novo só é registrado
   após a aplicação.
   - **Verificação:** `tests/skills_mgmt/test_upstream_detect.py` cobre a
     repetição após recusa. `tests/skills_mgmt/test_sync.py` cobre a
     preservação de `SKILL.md`.
   - **Fonte:** P3 e ADR-0007.

## Roteamento de skills e configuração dos adapters

9. **RN-009, roteamento de skills no Copilot.** O mapa global
   `permission.skill` determina o destino. Skills globais ficam em
   `.copilot/skills/`. Skills de domínio ficam em
   `.copilot/referencias/skills/`, fora da descoberta automática. A cópia
   materializada de cada perfil recebe referências somente às skills de
   domínio autorizadas para aquele agente. Cada referência contém a descrição
   completa da fonte e o caminho absoluto resolvido da cópia auxiliar. O perfil
   fonte permanece intacto. As contagens 10 globais e 23 de domínio registram o
   estado do ciclo, não valores fixos do contrato.
   - **Verificação:** `tests/harnesses/test_copilot.py` cobre classificação,
     destino, autorização por perfil e preservação da fonte.
   - **Fonte:** P4, SEC-16/SEC-17 e ADR-0009.

10. **RN-010, preservação da configuração do usuário.** No POSIX, o adapter
    OpenCode não escreve pelo symlink nem altera a configuração canônica. Sem
    provisionamento, o adapter materializa uma cópia filtrada. Com endpoint de
    bridge, materializa uma cópia local com a URL ativa. O adapter Copilot
    mescla servidores sem remover entradas existentes, cria backup antes da
    escrita e bloqueia colisão com um servidor `ai-memory` do usuário.
    - **Verificação:** `tests/harnesses/test_opencode.py` e
      `tests/harnesses/test_copilot.py` cobrem filtro, URL de bridge, merge,
      backup e colisão.
    - **Fonte:** ADR-0008.

## Política dos agentes

11. **RN-011, compactação e chamadas de ferramentas.** O agente avalia a
    compactação após salvar o resultado de uma etapa. O agente reduz contexto
    com leituras direcionadas e trechos. O agente agrupa operações
    independentes e executa operações dependentes na ordem necessária.
    - **Verificação:** as seções `Compactação de contexto` e `Chamadas de
      ferramentas` existem em `harness-conf/AGENTS.base.md`. A guarda fica em
      `tests/agents/test_workflow_consistency.py`.
    - **Fonte:** P5.

## Decisões de verificação do ciclo

Estas decisões controlam a auditoria e os testes do ciclo. Elas não descrevem
comportamento de runtime.

- **P2, amostra de auditoria:** 16 skills, compostas por 7 core, 4 com
  upstream, 4 locais de domínio e `writing-for-agents`. A decisão prevê ampliar
  para 33 skills se a auditoria encontrar muitos problemas. O plano registra
  a amostra, sua composição e o gatilho, sem definir um limiar numérico.
- **Q1, guarda de largura:** `tests/agents/test_line_width.py` cobre apenas
  `harness-conf/agents/*.md` e `harness-conf/AGENTS.base.md` neste ciclo.
  `SKILL.md` e `references/` ficam fora da guarda.
- **Q2, roteiro manual:** o roteiro não usa ambiente separado. A sequência
  cobre o estado atual do piloto, rollback com preservação do volume,
  reprovisionamento e leitura da wiki anterior. O humano acompanha as fases
  que alteram sua máquina.

**Verificação objetiva:** P2 corresponde à amostra descrita em
`plan/otimizacao-custo-contexto.md`. Q1 corresponde ao escopo de
`tests/agents/test_line_width.py`. Q2 corresponde às fases A-D e aos passos
RM-1..RM-13 do plano. Nenhum teste novo foi criado neste ciclo.
