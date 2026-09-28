import groovy.json.JsonSlurper
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths
import org.concordion.integration.junit4.ConcordionRunner
import org.junit.runner.RunWith

@RunWith(ConcordionRunner)
class Adr0008Fixture {
    private static final String SPEC = 'docs/adr/0008-ai-memory-bootstrap-mcp.md'
    private static final String BOOTSTRAP = 'src/opencode_config/bootstrap/ai_memory.py'
    private static final String SHARED_AI_MEMORY = 'src/opencode_config/lib/ai_memory.py'
    private static final String OPENCODE = 'src/opencode_config/harnesses/opencode.py'
    private static final String COPILOT = 'src/opencode_config/harnesses/copilot.py'
    private static final String PROVISION_TEST = 'tests/bootstrap/test_ai_memory_provision.py'
    private static final String OPENCODE_TEST = 'tests/harnesses/test_opencode.py'
    private static final String COPILOT_TEST = 'tests/harnesses/test_copilot.py'

    private final Path root = Paths
        .get(System.getProperty('repo.root', '.'))
        .toAbsolutePath()

    private String lerArquivo(String relativo) {
        def arquivo = root.resolve(relativo)
        return Files.isRegularFile(arquivo) ? arquivo.getText('UTF-8') : ''
    }

    private String textoDaSecao(String id) {
        def spec = lerArquivo(SPEC)
        def inicio = spec.indexOf("### ${id}:")
        if (inicio < 0) {
            return ''
        }
        def proxima = spec.indexOf('\n### ', inicio + 1)
        return proxima < 0 ? spec.substring(inicio) : spec.substring(inicio, proxima)
    }

    private List<String> celulasTabela(String linha) {
        def texto = linha.trim()
        if (!texto.startsWith('|') || !texto.endsWith('|')) {
            return []
        }
        return texto.substring(1, texto.length() - 1)
            .split(/\s*\|\s*/, -1)
            .collect { celula -> celula.trim() }
    }

    private String textoDaCelula(String celula) {
        def texto = celula.trim()
        def link = texto =~ /^\[([^\]]+)\]\(-\s+["'](?:\?=|c:assert-equals=)[^"']+["']\)$/
        if (link.matches()) {
            return link[0][1]
        }
        def codigo = texto =~ /^`([^`]+)`$/
        return codigo.matches() ? codigo[0][1] : texto
    }

    private Map<String, String> lerValoresEsperados(String id) {
        def linhas = textoDaSecao(id)
            .readLines()
            .findAll { linha -> linha.trim().startsWith('|') }
        if (linhas.size() < 3 || celulasTabela(linhas[0]) != [
            'Entrada',
            'Resultado esperado',
        ]) {
            return [:]
        }

        def valores = [:]
        for (linha in linhas.drop(1)) {
            def campos = celulasTabela(linha)
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

    private String valorEsperado(String id, String entrada) {
        def valores = lerValoresEsperados(id)
        return valores.containsKey(entrada) ? valores[entrada] : ''
    }

    private boolean tabelaCompleta(String id, String... entradas) {
        def valores = lerValoresEsperados(id)
        return valores['Veredito'] == 'pass' && entradas.every { entrada ->
            valores.containsKey(entrada) && !valores[entrada].isEmpty()
        }
    }

    private Map lerObjetoJson(String relativo) {
        def arquivo = root.resolve(relativo)
        if (!Files.isRegularFile(arquivo)) {
            return [:]
        }
        try {
            def objeto = new JsonSlurper().parse(arquivo.toFile())
            return objeto instanceof Map ? objeto as Map : [:]
        } catch (Exception ignorada) {
            return [:]
        }
    }

    private String trechoDoTeste(String relativo, String nome) {
        def conteudo = lerArquivo(relativo)
        def inicio = conteudo.indexOf("def ${nome}(")
        if (inicio < 0) {
            return ''
        }
        def proxima = conteudo.indexOf('\n@pytest.mark', inicio + 1)
        return proxima < 0 ? conteudo.substring(inicio) : conteudo.substring(inicio, proxima)
    }

    private boolean constanteContem(String relativo, String nome, String valor) {
        def conteudo = lerArquivo(relativo)
        def inicio = conteudo.indexOf("${nome} =")
        if (inicio < 0) {
            return false
        }
        def proxima = conteudo.indexOf('\n\n', inicio + 1)
        def declaracao = proxima < 0
            ? conteudo.substring(inicio)
            : conteudo.substring(inicio, proxima)
        return declaracao.contains(valor)
    }

    String verificarA801() {
        def secao = 'A8-01'
        def caminho = valorEsperado(secao, 'Arquivo de configuração canônica')
        def campoMcp = valorEsperado(secao, 'Campo de servidores MCP')
        def chave = valorEsperado(secao, 'Chave do servidor')
        def url = valorEsperado(secao, 'URL MCP canônica')
        def credenciais = valorEsperado(secao, 'Campos de credencial proibidos')
            .split(/\s*,\s*/)
            .findAll { campo -> !campo.isEmpty() }
        if (!tabelaCompleta(
            secao,
            'Arquivo de configuração canônica',
            'Campo de servidores MCP',
            'Chave do servidor',
            'URL MCP canônica',
            'Campos de credencial proibidos',
        )) {
            return 'fail'
        }

        def configuracao = lerObjetoJson(caminho)
        def servidores = configuracao[campoMcp]
        def servidor = servidores instanceof Map ? servidores[chave] : null
        return servidor instanceof Map && servidor.url == url &&
            !credenciais.any { campo -> servidor.containsKey(campo) }
            ? 'pass'
            : 'fail'
    }

    String getVereditoA801() {
        return verificarA801()
    }

    String verificarA802() {
        def secao = 'A8-02'
        def marcador = valorEsperado(secao, 'Marcador de prontidão')
        def chamadaMarcador = valorEsperado(secao, 'Chamada de gravação do marcador')
        def hashWrapper = valorEsperado(secao, 'SHA-256 do wrapper')
        def digestIndice = valorEsperado(secao, 'Digest do índice OCI')
        def tagImagem = valorEsperado(secao, 'Tag da imagem')
        def digestPlataforma = valorEsperado(secao, 'Digest linux/amd64')
        def redeIsolada = valorEsperado(secao, 'Opção de rede isolada')
        def testePins = valorEsperado(secao, 'Teste dos pins aprovados')
        def imagem = "${tagImagem}@sha256:${digestPlataforma}"
        def codigoBootstrap = lerArquivo(BOOTSTRAP)
        def blocoPins = trechoDoTeste(PROVISION_TEST, testePins)
        def pinsTestados = [hashWrapper, digestIndice, tagImagem, digestPlataforma]
            .every { valor -> blocoPins.contains(valor) }
        if (!tabelaCompleta(
            secao,
            'Marcador de prontidão',
            'Chamada de gravação do marcador',
            'SHA-256 do wrapper',
            'Digest do índice OCI',
            'Tag da imagem',
            'Digest linux/amd64',
            'Opção de rede isolada',
            'Teste dos pins aprovados',
        )) {
            return 'fail'
        }

        return lerArquivo(SHARED_AI_MEMORY).contains(
            "AI_MEMORY_READY_MARKER = \"${marcador}\"",
        ) && codigoBootstrap.contains(chamadaMarcador) &&
            constanteContem(BOOTSTRAP, 'AI_MEMORY_WRAPPER_SHA256', hashWrapper) &&
            constanteContem(BOOTSTRAP, 'AI_MEMORY_IMAGE_MANIFEST_SHA256', digestIndice) &&
            constanteContem(
                BOOTSTRAP,
                'AI_MEMORY_IMAGE_LINUX_AMD64_SHA256',
                digestPlataforma,
            ) && constanteContem(BOOTSTRAP, 'AI_MEMORY_IMAGE_TAG', tagImagem) &&
            codigoBootstrap.contains("\"${redeIsolada}\"") &&
            codigoBootstrap.contains(
                'AI_MEMORY_IMAGE = f"{AI_MEMORY_IMAGE_TAG}@sha256:' +
                    '{AI_MEMORY_IMAGE_LINUX_AMD64_SHA256}"',
            ) && lerArquivo(SPEC).contains("`${imagem}`") && pinsTestados
            ? 'pass'
            : 'fail'
    }

    String getVereditoA802() {
        return verificarA802()
    }

    String verificarA803() {
        def secao = 'A8-03'
        def filtro = valorEsperado(secao, 'Função de filtro OpenCode')
        def gateMarcador = valorEsperado(secao, 'Função de gate do marcador')
        def materializador = valorEsperado(secao, 'Método de materialização filtrada')
        def mergeCopilot = valorEsperado(secao, 'Método de merge Copilot')
        def testeOpenCode = valorEsperado(secao, 'Teste OpenCode sem provisionamento')
        def testeMergeCopilot = valorEsperado(
            secao,
            'Teste Copilot com servidor existente',
        )
        def testeCopilotSemProvisionamento = valorEsperado(
            secao,
            'Teste Copilot sem provisionamento',
        )
        return tabelaCompleta(
            secao,
            'Função de filtro OpenCode',
            'Função de gate do marcador',
            'Método de materialização filtrada',
            'Método de merge Copilot',
            'Teste OpenCode sem provisionamento',
            'Teste Copilot com servidor existente',
            'Teste Copilot sem provisionamento',
        ) && lerArquivo(SHARED_AI_MEMORY).contains(filtro) &&
            lerArquivo(OPENCODE).contains(filtro) &&
            lerArquivo(SHARED_AI_MEMORY).contains(gateMarcador) &&
            lerArquivo(OPENCODE).contains(gateMarcador) &&
            lerArquivo(OPENCODE).contains(materializador) &&
            lerArquivo(COPILOT).contains(gateMarcador) &&
            lerArquivo(COPILOT).contains(mergeCopilot) &&
            lerArquivo(OPENCODE_TEST).contains(testeOpenCode) &&
            lerArquivo(COPILOT_TEST).contains(testeMergeCopilot) &&
            lerArquivo(COPILOT_TEST).contains(testeCopilotSemProvisionamento)
            ? 'pass'
            : 'fail'
    }

    String getVereditoA803() {
        return verificarA803()
    }

    String executarVerificacoes() {
        def verificacoes = [verificarA801(), verificarA802(), verificarA803()]
        return verificacoes.every { resultado -> resultado == 'pass' }
            ? 'pass'
            : 'fail'
    }

    String getVeredito() {
        return executarVerificacoes()
    }
}
