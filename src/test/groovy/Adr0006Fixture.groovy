import groovy.json.JsonSlurper
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths
import org.concordion.integration.junit4.ConcordionRunner
import org.junit.runner.RunWith

@RunWith(ConcordionRunner)
class Adr0006Fixture {
    private static final String SPEC = 'docs/adr/0006-camada-mcp-opcional-com-fallback-cli.md'

    private final Path root = Paths
        .get(System.getProperty('repo.root', '.'))
        .toAbsolutePath()

    // A tabela da spec fornece o caminho canônico opencode.json.
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

    private Map configuracaoCanonica(String caminho) {
        def arquivo = root.resolve(caminho)
        if (!Files.isRegularFile(arquivo)) {
            return [:]
        }
        try {
            def configuracao = new JsonSlurper().parse(arquivo.toFile())
            return configuracao instanceof Map ? configuracao as Map : [:]
        } catch (Exception ignorada) {
            return [:]
        }
    }

    String verificarMcp01() {
        def secao = 'MCP-01'
        def caminho = valorEsperado(secao, 'Configuração canônica')
        def campoMcp = valorEsperado(secao, 'Campo MCP canônico')
        def chavesAprovadas = valorEsperado(secao, 'Chaves MCP aprovadas')
            .split(/\s*,\s*/)
            .findAll { chave -> !chave.isEmpty() }
            .toSet()
        def urlAprovada = valorEsperado(secao, 'URL MCP aprovada')
        def campoAlternativo = valorEsperado(secao, 'Campo alternativo proibido')
        if (!tabelaCompleta(
            secao,
            'Configuração canônica',
            'Campo MCP canônico',
            'Chaves MCP aprovadas',
            'URL MCP aprovada',
            'Campo alternativo proibido',
        ) || chavesAprovadas.isEmpty()) {
            return 'fail'
        }

        def configuracao = configuracaoCanonica(caminho)
        def servidores = configuracao[campoMcp]
        if (!(servidores instanceof Map)) {
            return 'fail'
        }
        def chavesConfiguradas = servidores.keySet()
            .collect { chave -> chave.toString() }
            .toSet()
        def entradasCorretas = servidores.every { chave, servidor ->
            chavesAprovadas.contains(chave.toString()) &&
                servidor instanceof Map && servidor.url == urlAprovada
        }
        return chavesConfiguradas == chavesAprovadas && entradasCorretas &&
            !configuracao.containsKey(campoAlternativo)
            ? 'pass'
            : 'fail'
    }

    String getVereditoMcp01() {
        return verificarMcp01()
    }

    String executarVerificacoes() {
        return [verificarMcp01()].every { resultado -> resultado == 'pass' }
            ? 'pass'
            : 'fail'
    }

    String getVeredito() {
        return executarVerificacoes()
    }
}
