import groovy.json.JsonSlurper
import java.net.URI
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths
import org.concordion.integration.junit4.ConcordionRunner
import org.junit.runner.RunWith

@RunWith(ConcordionRunner)
class SegurancaFixture {
    private static final String SPEC = 'docs/specs/Seguranca.md'
    private static final String BOOTSTRAP = 'src/opencode_config/bootstrap/ai_memory.py'
    private static final String AI_MEMORY_LIB = 'src/opencode_config/lib/ai_memory.py'
    private static final String SYNC_LIB = 'src/opencode_config/lib/sync.py'
    private static final String PROVISION_TEST = 'tests/bootstrap/test_ai_memory_provision.py'

    private final Path root = Paths
        .get(System.getProperty('repo.root', '.'))
        .toAbsolutePath()

    private String lerArquivo(String relativo) {
        def arquivo = root.resolve(relativo)
        return Files.isRegularFile(arquivo) ? arquivo.getText('UTF-8') : ''
    }

    private boolean contém(String relativo, String... trechos) {
        def conteúdo = lerArquivo(relativo)
        return !conteúdo.isEmpty() && trechos.every { trecho ->
            !trecho.isEmpty() && conteúdo.contains(trecho)
        }
    }

    private String textoDaSecao(String secId) {
        def spec = lerArquivo(SPEC)
        def início = spec.indexOf("### ${secId}")
        if (início < 0) {
            return ''
        }
        def próxima = spec.indexOf('\n### ', início + 1)
        return próxima < 0 ? spec.substring(início) : spec.substring(início, próxima)
    }

    private List<String> célulasTabela(String linha) {
        def texto = linha.trim()
        if (!texto.startsWith('|') || !texto.endsWith('|')) {
            return []
        }
        return texto.substring(1, texto.length() - 1)
            .split(/\s*\|\s*/, -1)
            .collect { célula -> célula.trim() }
    }

    private String textoDaCelula(String célula) {
        def texto = célula.trim()
        def link = texto =~ /^\[([^\]]+)\]\(-\s+["'](?:\?=|c:assert-equals=)[^"']+["']\)$/
        if (link.matches()) {
            return link[0][1]
        }
        def código = texto =~ /^`([^`]+)`$/
        return código.matches() ? código[0][1] : texto
    }

    private Map<String, String> lerValoresEsperados(String secId) {
        def linhas = textoDaSecao(secId)
            .readLines()
            .findAll { linha -> linha.trim().startsWith('|') }
        if (linhas.size() < 3 || célulasTabela(linhas[0]) != [
            'Entrada',
            'Resultado esperado',
        ]) {
            return [:]
        }

        def valores = [:]
        for (linha in linhas.drop(1)) {
            def campos = célulasTabela(linha)
            if (campos.every { campo -> campo ==~ /:?-{3,}:?/ }) {
                continue
            }
            if (campos.size() != 2) {
                return [:]
            }
            def entrada = textoDaCelula(campos[0])
            def esperado = textoDaCelula(campos[1])
            if (entrada.isEmpty() || esperado.isEmpty() || valores.containsKey(entrada)) {
                return [:]
            }
            valores[entrada] = esperado
        }
        return valores
    }

    private String valorEsperado(String secId, String entrada) {
        def valores = lerValoresEsperados(secId)
        return valores.containsKey(entrada) ? valores[entrada] : ''
    }

    private boolean tabelaCompleta(String secId, String... entradas) {
        def valores = lerValoresEsperados(secId)
        return valores['Veredito'] == 'pass' && entradas.every { entrada ->
            valores.containsKey(entrada) && !valores[entrada].isEmpty()
        }
    }

    private String trechoDoTeste(String relativo, String nome) {
        def conteúdo = lerArquivo(relativo)
        def início = conteúdo.indexOf("def ${nome}(")
        if (início < 0) {
            return ''
        }
        def próxima = conteúdo.indexOf('\n@pytest.mark', início + 1)
        return próxima < 0
            ? conteúdo.substring(início)
            : conteúdo.substring(início, próxima)
    }

    private String trechoDeCódigo(String relativo, String início, String fim) {
        def conteúdo = lerArquivo(relativo)
        def posiçãoInicial = conteúdo.indexOf(início)
        if (posiçãoInicial < 0) {
            return ''
        }
        def posiçãoFinal = conteúdo.indexOf(fim, posiçãoInicial + início.length())
        return posiçãoFinal < 0
            ? conteúdo.substring(posiçãoInicial)
            : conteúdo.substring(posiçãoInicial, posiçãoFinal)
    }

    private String expressãoDeCaminhoPython(String caminho, String base) {
        def relativo = caminho.replaceFirst('^~/', '').replaceAll('/+$', '')
        def partes = relativo.split('/')
        if (partes.length == 0 || partes.any { parte -> parte.isEmpty() }) {
            return ''
        }
        return "${base} / " + partes.collect { parte -> "\"${parte}\"" }.join(' / ')
    }

    private boolean caminhoPythonConfere(String caminho, String constante) {
        return caminhoPythonConfere(caminho, constante, BOOTSTRAP)
    }

    private boolean caminhoPythonConfere(
        String caminho,
        String constante,
        String arquivo
    ) {
        def relativo = caminho.replaceFirst('^~/', '').replaceAll('/+$', '')
        def partes = relativo.split('/')
        if (partes.length < 2) {
            return false
        }
        def diretórios = partes.take(partes.length - 1)
        def expressão = 'return paths.home / ' +
            diretórios.collect { parte -> "\"${parte}\"" }.join(' / ') +
            " / ${constante}"
        def declaração = "${constante} = \"${partes.last()}\""
        return contém(arquivo, expressão, declaração)
    }

    private int contarOcorrencias(String texto, String trecho) {
        if (trecho.isEmpty()) {
            return 0
        }
        def quantidade = 0
        def início = 0
        while ((início = texto.indexOf(trecho, início)) >= 0) {
            quantidade++
            início += trecho.length()
        }
        return quantidade
    }

    private String resultado(boolean válido) {
        válido ? 'pass' : 'fail'
    }

    private boolean urlReleaseConfere(
        String urlEsperada,
        String versao,
        String esquema,
        String codigo
    ) {
        try {
            def uri = new URI(urlEsperada)
            def posiçãoVersão = urlEsperada.lastIndexOf(versao)
            if (posiçãoVersão < 0) {
                return false
            }
            def prefixo = urlEsperada.substring(0, posiçãoVersão)
            def sufixo = urlEsperada.substring(posiçãoVersão + versao.length())
            return uri.scheme == esquema && uri.path.contains("/${versao}/") &&
                codigo.contains("\"${prefixo}\"") &&
                codigo.contains("f\"{AI_MEMORY_WRAPPER_VERSION}${sufixo}\"")
        } catch (Exception ignorada) {
            return false
        }
    }

    String verificarSec01() {
        def versao = valorEsperado('SEC-01', 'Versão da release')
        def url = valorEsperado('SEC-01', 'URL de download')
        def esquema = valorEsperado('SEC-01', 'Esquema da URL')
        def codigo = lerArquivo(BOOTSTRAP)
        resultado(
            tabelaCompleta(
                'SEC-01',
                'Versão da release',
                'URL de download',
                'Esquema da URL',
            ) &&
                contém(
                    BOOTSTRAP,
                    "AI_MEMORY_WRAPPER_VERSION = \"${versao}\"",
                    'with urllib.request.urlopen(',
                    'timeout=_DOWNLOAD_IDLE_TIMEOUT_SECONDS',
                ) &&
                urlReleaseConfere(url, versao, esquema, codigo) &&
                contém(
                    PROVISION_TEST,
                    'test_ai_memory_upstream_release_pins_match_reviewed_artifacts',
                    'test_ai_memory_provision_downloads_verified_wrapper_and_restricts_container',
                ),
        )
    }

    String getVereditoSec01() { verificarSec01() }

    String verificarSec02() {
        def wrapperSha = valorEsperado('SEC-02', 'SHA-256 do wrapper')
        def manifestSha = valorEsperado('SEC-02', 'Digest do índice OCI')
        def imageTag = valorEsperado('SEC-02', 'Tag da imagem')
        def imageSha = valorEsperado('SEC-02', 'Digest linux/amd64')
        def imageReference = valorEsperado('SEC-02', 'Referência')
        resultado(
            tabelaCompleta(
                'SEC-02',
                'SHA-256 do wrapper',
                'Digest do índice OCI',
                'Tag da imagem',
                'Digest linux/amd64',
                'Referência',
            ) &&
                imageReference == "${imageTag}@sha256:${imageSha}" &&
                contém(
                    BOOTSTRAP,
                    'AI_MEMORY_WRAPPER_SHA256',
                    wrapperSha,
                    'AI_MEMORY_IMAGE_MANIFEST_SHA256',
                    manifestSha,
                    "AI_MEMORY_IMAGE_TAG = \"${imageTag}\"",
                    'AI_MEMORY_IMAGE_LINUX_AMD64_SHA256',
                    imageSha,
                    'AI_MEMORY_IMAGE = f"{AI_MEMORY_IMAGE_TAG}@sha256:',
                    '{AI_MEMORY_IMAGE_LINUX_AMD64_SHA256}"',
                    'expected_sha256=expected_hash',
                ) && contém(
                    PROVISION_TEST,
                    'test_ai_memory_upstream_release_pins_match_reviewed_artifacts',
                    'test_ai_memory_download_hash_mismatch_blocks_installation',
                ),
        )
    }

    String getVereditoSec02() { verificarSec02() }

    String verificarSec03() {
        def host = valorEsperado('SEC-03', 'Host do bind loopback')
        def porta = valorEsperado('SEC-03', 'Porta MCP')
        def bind = valorEsperado('SEC-03', 'Bind Docker')
        def loopback = valorEsperado('SEC-03', 'URL MCP no loopback')
        def bridge = valorEsperado('SEC-03', 'URL de bridge no teste')
        def hosts = valorEsperado('SEC-03', 'Hosts permitidos')
        def statusAceito = valorEsperado('SEC-03', 'Status HTTP aceito')
        def statusRejeitado = valorEsperado('SEC-03', 'Status HTTP rejeitado')
        def bridgeUri
        def loopbackUri
        try {
            bridgeUri = new URI(bridge)
            loopbackUri = new URI(loopback)
        } catch (Exception ignorada) {
            return 'fail'
        }
        def resolverBridge =
            'return f"http://{address.compressed}:{AI_MEMORY_PORT}' +
            bridgeUri.path + '"'
        def tabelaOk = tabelaCompleta(
            'SEC-03',
            'Host do bind loopback',
            'Porta MCP',
            'Bind Docker',
            'URL MCP no loopback',
            'URL de bridge no teste',
            'Hosts permitidos',
            'Status HTTP aceito',
            'Status HTTP rejeitado',
        )
        def bindOk = bind == "${host}:${porta}:${porta}"
        def urlOk = loopbackUri.scheme == bridgeUri.scheme &&
            loopbackUri.port.toString() == porta &&
            bridgeUri.port.toString() == porta &&
            loopbackUri.path == bridgeUri.path
        def código = lerArquivo(BOOTSTRAP)
        def códigoShared = lerArquivo(AI_MEMORY_LIB)
        def partesCodigo = [
            host: código.contains("AI_MEMORY_HOST = \"${host}\""),
            porta: código.contains("AI_MEMORY_PORT = ${porta}"),
            url: códigoShared.contains("AI_MEMORY_MCP_URL = \"${loopback}\""),
            hosts: código.contains("AI_MEMORY_ALLOWED_HOSTS=\"${hosts}\""),
            status: código.contains("return error.code == ${statusAceito}"),
            bind: código.contains('f"{AI_MEMORY_HOST}:{AI_MEMORY_PORT}:{AI_MEMORY_PORT}"'),
            bridge: código.contains(resolverBridge),
            hostname: código.contains('hostname -i'),
            publish: código.contains('"--publish"'),
        ]
        def codigoOk = partesCodigo.values().every { parte -> parte }
        def testesOk = contém(
            PROVISION_TEST,
            bridge,
            "${statusRejeitado},",
            "${statusAceito},",
            'test_ai_memory_uses_internal_bridge_url_when_docker_does_not_publish_loopback',
            'test_ai_memory_endpoint_probe_rejects_disallowed_host_response',
            'test_ai_memory_endpoint_probe_accepts_method_not_allowed_from_mcp_get',
        )
        resultado(
            tabelaOk && bindOk && urlOk && codigoOk && testesOk,
        )
    }

    String getVereditoSec03() { verificarSec03() }

    String verificarSec04() {
        def host = valorEsperado('SEC-04', 'Host ocupado')
        def porta = valorEsperado('SEC-04', 'Porta ocupada')
        def endereço = valorEsperado('SEC-04', 'Endereço ocupado')
        def mensagem = valorEsperado('SEC-04', 'Trecho da mensagem')
        def teste = trechoDoTeste(
            PROVISION_TEST,
            'test_ai_memory_occupied_loopback_port_aborts_before_container_creation',
        )
        resultado(
            tabelaCompleta(
                'SEC-04',
                'Host ocupado',
                'Porta ocupada',
                'Endereço ocupado',
                'Trecho da mensagem',
            ) && endereço == "${host}:${porta}" && contém(
                BOOTSTRAP,
                '_port_is_in_use',
                "AI_MEMORY_HOST = \"${host}\"",
                "AI_MEMORY_PORT = ${porta}",
                mensagem,
            ) && teste.contains("assert \"${porta}\" in result.message") &&
                teste.contains('assert not runner.container_available'),
        )
    }

    String getVereditoSec04() { verificarSec04() }

    String verificarSec05() {
        def caminhoPlugin = valorEsperado('SEC-05', 'Caminho do plugin')
        def aviso = valorEsperado('SEC-05', 'Aviso de drift')
        def teste = trechoDoTeste(
            PROVISION_TEST,
            'test_ai_memory_plugin_hash_drift_is_reported',
        )
        def expressãoPlugin = expressãoDeCaminhoPython(caminhoPlugin, 'context.paths.home')
        resultado(
            tabelaCompleta('SEC-05', 'Caminho do plugin', 'Aviso de drift') &&
                !expressãoPlugin.isEmpty() &&
                contém(BOOTSTRAP, 'plugin_hash_before', aviso) &&
                teste.contains("plugin = ${expressãoPlugin}") &&
                teste.contains('test_ai_memory_plugin_hash_drift_is_reported') &&
                teste.contains('"AVISO"') && teste.contains('"ai-memory.ts"'),
        )
    }

    String getVereditoSec05() { verificarSec05() }

    String verificarSec06() {
        def execuções = valorEsperado('SEC-06', 'Execuções do provisionamento')
        def downloads = valorEsperado('SEC-06', 'Downloads totais do wrapper')
        def pulls = valorEsperado('SEC-06', 'Pulls totais da imagem')
        def upgrade = valorEsperado('SEC-06', 'Upgrade com hash divergente')
        def backup = valorEsperado('SEC-06', 'Trecho da instrução de backup')
        def reexecução = valorEsperado('SEC-06', 'Trecho da instrução de reexecução')
        def testeIdempotência = trechoDoTeste(
            PROVISION_TEST,
            'test_ai_memory_second_run_does_not_download_or_pull_again',
        )
        def testeUpgrade = trechoDoTeste(
            PROVISION_TEST,
            'test_ai_memory_existing_wrapper_drift_requires_explicit_upgrade',
        )
        def listaDownloads = testeIdempotência =~ /assert downloads == \[(.*?)\]/
        def quantidadeDownloads = -1
        if (listaDownloads.find()) {
            def itens = listaDownloads.group(1).trim()
            quantidadeDownloads = itens.isEmpty() ? 0 : itens.split(/\s*,\s*/).length
        }
        resultado(
            tabelaCompleta(
                'SEC-06',
                'Execuções do provisionamento',
                'Downloads totais do wrapper',
                'Pulls totais da imagem',
                'Upgrade com hash divergente',
                'Trecho da instrução de backup',
                'Trecho da instrução de reexecução',
            ) &&
                execuções.isInteger() && downloads.isInteger() && pulls.isInteger() &&
                contarOcorrencias(
                    testeIdempotência,
                    'ai_memory.provision_ai_memory(',
                ) == execuções.toInteger() &&
                quantidadeDownloads == downloads.toInteger() &&
                testeIdempotência.contains(
                    "assert runner.pull_count == ${pulls}",
                ) && upgrade == 'bloqueado' &&
                testeUpgrade.contains('assert not result.provisioned') &&
                testeUpgrade.contains("assert \"${backup}\" in result.message.lower()") &&
                testeUpgrade.contains(
                    "assert \"${reexecução}\" in result.message.lower()",
                ) && contém(
                    BOOTSTRAP,
                    'AI_MEMORY_WRAPPER_SHA256',
                    'docker, "pull", AI_MEMORY_IMAGE',
                ),
        )
    }

    String getVereditoSec06() { verificarSec06() }

    String verificarSec07() {
        def volume = valorEsperado('SEC-07', 'Diretório de dados')
        def marcador = valorEsperado('SEC-07', 'Marcador MCP')
        def modo = valorEsperado('SEC-07', 'Modo POSIX')
        def conteúdoPreservado = valorEsperado('SEC-07', 'Conteúdo após rollback')
        def modoCódigo = modo.replaceFirst('^0', '')
        def marcadorDiretório = marcador.substring(0, marcador.lastIndexOf('/') + 1)
        def testeRollback = trechoDoTeste(
            PROVISION_TEST,
            'test_ai_memory_rollback_removes_runtime_but_preserves_data',
        )
        resultado(
            tabelaCompleta(
                'SEC-07',
                'Diretório de dados',
                'Marcador MCP',
                'Modo POSIX',
                'Conteúdo após rollback',
            ) && !marcador.startsWith(volume) && modo.matches('0?[0-7]{3,4}') &&
                caminhoPythonConfere(
                    volume,
                    'AI_MEMORY_DATA_NAME',
                    AI_MEMORY_LIB,
                ) &&
                caminhoPythonConfere(
                    marcador,
                    'AI_MEMORY_URL_MARKER',
                    AI_MEMORY_LIB,
                ) && contém(
                    'README.md',
                    volume,
                    marcadorDiretório,
                    marcador.substring(marcador.lastIndexOf('/') + 1),
                    'dado sensível',
                    'não o versione',
                ) && contém(
                    BOOTSTRAP,
                    "mode=0o${modoCódigo}",
                    "data_directory.chmod(0o${modoCódigo})",
                    'Dados preservados em',
                ) && contém(
                    PROVISION_TEST,
                    'test_ai_memory_uses_internal_bridge_url_when_docker_does_not_publish_loopback',
                    'test_ai_memory_rollback_removes_runtime_but_preserves_data',
                ) && testeRollback.contains("== \"${conteúdoPreservado}\""),
        )
    }

    String getVereditoSec07() { verificarSec07() }

    String verificarSec08() {
        def comando = valorEsperado('SEC-08', 'Comando de rollback')
        def configLegada = valorEsperado('SEC-08', 'Configuração restaurada')
        def marcador = valorEsperado('SEC-08', 'Marcador removido')
        def volume = valorEsperado('SEC-08', 'Volume preservado')
        def arquivoDados = valorEsperado('SEC-08', 'Arquivo de dados preservado')
        def testeRollback = trechoDoTeste(
            PROVISION_TEST,
            'test_ai_memory_rollback_removes_runtime_but_preserves_data',
        )
        resultado(
            tabelaCompleta(
                'SEC-08',
                'Comando de rollback',
                'Configuração restaurada',
                'Marcador removido',
                'Volume preservado',
                'Arquivo de dados preservado',
            ) && contém(
                BOOTSTRAP,
                'def rollback_ai_memory(',
                '_restore_legacy_jsonc',
                '_remove_wrapper_artifacts',
            ) && contém(
                PROVISION_TEST,
                'test_ai_memory_rollback_removes_runtime_but_preserves_data',
            ) && contém(
                'README.md',
                "opencode-bootstrap ${comando}",
                configLegada,
                volume,
            ) && caminhoPythonConfere(
                marcador,
                'AI_MEMORY_URL_MARKER',
                AI_MEMORY_LIB,
            ) &&
                testeRollback.contains("data_directory / \"${arquivoDados}\""),
        )
    }

    String getVereditoSec08() { verificarSec08() }

    String verificarSec09() {
        def condição = valorEsperado('SEC-09', 'Condição')
        def chaveMcp = valorEsperado('SEC-09', 'Chave MCP')
        def estadoOpenCode = valorEsperado('SEC-09', 'Resultado OpenCode')
        def estadoCopilot = valorEsperado('SEC-09', 'Resultado Copilot')
        def instrução = valorEsperado('SEC-09', 'Instrução sem elevação')
        def testeSemDocker = trechoDoTeste(
            PROVISION_TEST,
            'test_ai_memory_without_docker_warns_and_cleans_active_hooks',
        )
        resultado(
            tabelaCompleta(
                'SEC-09',
                'Condição',
                'Chave MCP',
                'Resultado OpenCode',
                'Resultado Copilot',
                'Instrução sem elevação',
            ) && estadoOpenCode == 'ausente' && estadoCopilot == 'ausente' && contém(
                    BOOTSTRAP,
                    "${condição}.",
                    'O bloco MCP foi desabilitado nos harnesses.',
                    instrução,
                ) && contém(
                    PROVISION_TEST,
                    "assert \"${chaveMcp}\" not in disabled_config[\"mcp\"]",
                ) && contém(
                    'tests/harnesses/test_opencode.py',
                    'test_opencode_without_provisioned_ai_memory_filters_symlink_config',
                ) && contém(
                    'tests/harnesses/test_copilot.py',
                    'test_copilot_adapter_removes_ai_memory_entry_when_provisioning_is_incomplete',
            ) && testeSemDocker.contains("assert \"${instrução}\" in output.getvalue()"),
        )
    }

    String getVereditoSec09() { verificarSec09() }

    String verificarSec10() {
        def arquivoConfig = valorEsperado('SEC-10', 'Arquivo de configuração Copilot')
        def servidorExistente = valorEsperado('SEC-10', 'Servidor preexistente')
        def urlExistente = valorEsperado('SEC-10', 'URL preexistente')
        def urlAiMemory = valorEsperado('SEC-10', 'URL MCP ai-memory')
        def padrãoBackup = valorEsperado('SEC-10', 'Padrão do nome do backup')
        def formatoTimestamp = valorEsperado('SEC-10', 'Formato do timestamp')
        def localBackup = valorEsperado('SEC-10', 'Local do backup')
        def prefixoSaida = valorEsperado('SEC-10', 'Prefixo da saída')
        def formatoPython = [
            'YYYYMMDD-HHMMSS': '%Y%m%d-%H%M%S',
        ][formatoTimestamp]
        def nomeBaseBackup = padrãoBackup.contains('<timestamp>')
            ? padrãoBackup.substring(0, padrãoBackup.indexOf('<timestamp>'))
            : ''
        def testeMerge = trechoDoTeste(
            'tests/harnesses/test_copilot.py',
            'test_copilot_adapter_merges_ai_memory_without_losing_existing_servers',
        )
        def códigoMerge = trechoDeCódigo(
            'src/opencode_config/harnesses/copilot.py',
            'def _sync_mcp_config(',
            '\ndef _print_plan(',
        )
        def códigoBackup = trechoDeCódigo(
            SYNC_LIB,
            'def backup_copy_with_timestamp(',
            '\ndef backup_move(',
        )
        def códigoCopilot = lerArquivo('src/opencode_config/harnesses/copilot.py')
        def caminhoConfig = expressãoDeCaminhoPython(arquivoConfig, 'home')
        def posiçãoBackup = códigoMerge.indexOf(
            'backup_path = backup_copy_with_timestamp(destination, backup_timestamp)',
        )
        def posiçãoSaída = códigoMerge.indexOf(
            "output(f\"${prefixoSaida} {backup_path}\")",
            posiçãoBackup,
        )
        def posiçãoEscrita = códigoMerge.indexOf('_write_utf8(', posiçãoSaída)
        resultado(
            tabelaCompleta(
                'SEC-10',
                'Arquivo de configuração Copilot',
                'Servidor preexistente',
                'URL preexistente',
                'URL MCP ai-memory',
                'Padrão do nome do backup',
                'Formato do timestamp',
                'Local do backup',
                'Prefixo da saída',
            ) && !caminhoConfig.isEmpty() && formatoPython != null &&
                padrãoBackup == 'mcp-config.json.<timestamp>[.<n>].bak' &&
                localBackup == 'mesmo diretório da configuração' &&
                nomeBaseBackup == 'mcp-config.json.' &&
                códigoCopilot.contains(
                    "datetime.now().strftime(\"${formatoPython}\")",
                ) &&
                códigoMerge.contains("destination = ${caminhoConfig}") &&
                posiçãoBackup >= 0 && posiçãoSaída > posiçãoBackup &&
                posiçãoEscrita > posiçãoSaída &&
                códigoBackup.contains('path.with_name(') &&
                códigoBackup.contains('f"{path.name}.{timestamp}.bak"') &&
                códigoBackup.contains(
                    'f"{path.name}.{timestamp}.{index}.bak"',
                ) &&
                códigoBackup.contains('shutil.copy2(path, candidate)') &&
                testeMerge.contains("glob(\"${nomeBaseBackup}*.bak\")") &&
                testeMerge.contains('backup_path.parent == config_path.parent') &&
                testeMerge.contains(
                    'backup_path.read_text(encoding="utf-8") == original_config_content',
                ) &&
                testeMerge.contains(
                    "assert f\"${prefixoSaida} {backup_path}\" in output",
                ) &&
                contém(
                    'tests/harnesses/test_copilot.py',
                    'test_copilot_adapter_merges_ai_memory_without_losing_existing_servers',
                ) && testeMerge.contains(servidorExistente) &&
                testeMerge.contains(urlExistente) && testeMerge.contains(urlAiMemory),
        )
    }

    String getVereditoSec10() { verificarSec10() }

    String verificarSec11() {
        def configPath = valorEsperado('SEC-11', 'Arquivo canônico')
        def serverName = valorEsperado('SEC-11', 'Chave MCP')
        def url = valorEsperado('SEC-11', 'URL MCP canônica')
        def credentialFields = valorEsperado('SEC-11', 'Campos de credencial')
            .split(',')
            .collect { field -> field.trim() }
        if (!tabelaCompleta(
            'SEC-11',
            'Arquivo canônico',
            'Chave MCP',
            'URL MCP canônica',
            'Campos de credencial',
        )) {
            return 'fail'
        }
        def configFile = root.resolve(configPath)
        if (!Files.isRegularFile(configFile)) {
            return 'fail'
        }
        def config = new JsonSlurper().parse(configFile.toFile())
        def server = config.mcp?.get(serverName)
        return server instanceof Map && server.url == url &&
            !credentialFields.any { field -> server.containsKey(field) }
            ? 'pass'
            : 'fail'
    }

    String getVereditoSec11() { verificarSec11() }

    String verificarSec21() {
        def rede = valorEsperado('SEC-21', 'Rede Docker')
        def flagInternal = valorEsperado('SEC-21', 'Opção de isolamento')
        def estadoInternal = valorEsperado('SEC-21', 'Estado internal esperado')
        def rota = valorEsperado('SEC-21', 'Rota padrão de saída')
        resultado(
            tabelaCompleta(
                'SEC-21',
                'Rede Docker',
                'Opção de isolamento',
                'Estado internal esperado',
                'Rota padrão de saída',
            ) && contém(
                BOOTSTRAP,
                "AI_MEMORY_NETWORK = \"${rede}\"",
                "\"${flagInternal}\"",
                "if internal_flag.lower() != \"${estadoInternal}\"",
            ) && contém('README.md', rota) && contém(
                PROVISION_TEST,
                'test_ai_memory_provision_downloads_verified_wrapper_and_restricts_container',
                'network", "create',
                "\"${flagInternal}\"",
            ),
        )
    }

    String getVereditoSec21() { verificarSec21() }

    String executarVerificacoesAiMemory() {
        def verificações = [
            verificarSec01(), verificarSec02(), verificarSec03(),
            verificarSec04(), verificarSec05(), verificarSec06(),
            verificarSec07(), verificarSec08(), verificarSec09(),
            verificarSec10(), verificarSec11(), verificarSec21(),
        ]
        verificações.every { it == 'pass' } ? 'pass' : 'fail'
    }

    String getVereditoAiMemory() { executarVerificacoesAiMemory() }

    String executarVerificacoes() {
        def root = Paths.get(System.getProperty('repo.root', '.'))
        def required = [
            'docs/specs/Seguranca.md',
            'docs/adr/0006-camada-mcp-opcional-com-fallback-cli.md',
            'src/opencode_config/product_tests/security.py',
            'testes-produto/seguranca',
        ]
        return required.every { relative -> Files.isRegularFile(root.resolve(relative)) } &&
            executarVerificacoesAiMemory() == 'pass'
            ? 'pass'
            : 'fail'
    }

    String getVeredito() {
        executarVerificacoes()
    }
}
