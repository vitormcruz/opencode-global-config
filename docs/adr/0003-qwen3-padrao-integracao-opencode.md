# ADR-0003: Qwen3-0.6B como padrão da integração OpenCode

- **Status:** Aceita
- **Data:** 2026-08-18
- **Escopo:** Integração OpenCode no WSL/Linux, llama-server, Docker e cache local
- **Substitui:** Decisões de modelo específico do ADR-0002 para esta integração

## Contexto

O harness OpenCode precisa de um único endpoint de inferência local, previsível
e verificável. A seleção de modelos introduzia ramificações no servidor, nas
fixtures, na configuração e nos comandos de teste. Isso também permitia que
uma execução escolhesse um provider diferente do contrato aprovado.

O Qwen3-0.6B Q8_0 foi aprovado no experimento de modelos locais por licença,
compatibilidade OpenAI, checksum fixo e desempenho adequado. Needle 2 continua
fora de escopo e o adapter Copilot não é alterado.

## Decisão

1. O único provider é `qwen-local`, com o modelo `qwen3-0.6b`.
2. O artefato é `Qwen3-0.6B-Q8_0.gguf`, do repositório
   `Qwen/Qwen3-0.6B-GGUF`, validado pelo SHA-256
   `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`.
3. O llama-server Prism `prism-b9596-9fcaed7` permanece no host WSL/Linux e é
   reutilizado pelo cache do usuário.
4. O container usa somente `opencode-test-net --internal` e acessa o host por
   `host.docker.internal:8080/v1`, com proxy limitado a localhost.
5. O bootstrap não baixa pesos. O harness provisiona binário e pesos sob
   demanda; depois da validação do cache, a execução permanece offline.
6. Não há seletor, provider alternativo ou fallback silencioso. Falhas de
   provisionamento e inferência são explícitas.
7. Os timeouts existentes são invariantes e não foram alterados.
8. O bootstrap WSL/Linux provisiona `libgomp.so.1` em cache user-space a partir
   do pacote Debian Snapshot `libgomp1_12.2.0-14+deb12u1_amd64.deb`, fixado por
   URL, versão, arquitetura e SHA-256. O arquivo é GPLv3-or-later com GCC
   Runtime Library Exception 3.1; avisos e origem devem ser preservados.
   O SHA-256 do pacote é
   `48fec46bda7f5b1638b9e959889bfbc20491247d402d120bb152687eb48143d7` e o da
   biblioteca extraída é
   `f9a9ad78a8dc39c0e90a265ffa551fae6c92a40f360889b44a7e141f9a2adfb1`.
9. Antes de iniciar o Prism, o servidor valida a runtime e usa
   `ld-linux-x86-64.so.2 --library-path`, sem `LD_LIBRARY_PATH` ou alteração
   global. Runtime ausente, inválida ou incompatível falha com instrução para
   executar `opencode-bootstrap --yes`.

## Decisões substituídas

Esta decisão substitui, somente para o contrato OpenCode, as decisões do
ADR-0002 que permitiam um modelo/provider diferente do Qwen fixado e uma
seleção por execução. O ADR-0002 permanece imutável como registro histórico.

## Consequências

- A configuração efetiva declara exatamente um provider local.
- Os agentes `plan` e `build` sempre usam `qwen-local/qwen3-0.6b`.
- O cache reduz downloads repetidos e permite execução offline após o primeiro
  provisionamento.
- A ausência de uma alternativa torna insuficiente qualquer falha do Qwen,
  mas evita mascarar erros de privacidade, integridade ou disponibilidade.
- O gate operacional é `.venv/bin/pytest -m opencode` no WSL/Linux com Docker,
  incluindo rede interna, endpoint local e bloqueio de egress.
- A runtime nativa não depende de `libgomp1` instalado globalmente; após o
  bootstrap, o provisionamento e a execução permanecem offline.

## Rollback

O rollback suportado é `git revert` do conjunto de commits da migração. Não se
reativa um caminho alternativo no harness nem se reescreve o ADR-0002.
