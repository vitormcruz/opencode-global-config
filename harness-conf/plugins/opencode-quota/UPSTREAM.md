# Metadados do Upstream

plugin: @slkiser/opencode-quota (npm)
versao_ratificada: 4.10.6
data: 2026-09-28
decisao: ratificado sem revisão formal por decisão humana (2026-09-28);
  flutuação vigiada por teste de aviso

## Política de versão

O pacote permanece sem pin no array `plugin` de
`harness-conf/opencode.json` e flutua para a versão mais recente a cada
restart. O teste `test_quota_plugin_version_vigiada`
(`tests/test_opencode_plugins.py`) consulta `npm view` e compara a
versão atual com `versao_ratificada`: igual, passa limpo; diferente,
emite warning instruindo o agente a perguntar ao humano se quer
validação de segurança antes de ratificar a nova versão.

Para ratificar uma versão nova: execute a revisão de segurança (ler o
tarball, refazer os findings), atualize `versao_ratificada` e a `data`
deste registro.
