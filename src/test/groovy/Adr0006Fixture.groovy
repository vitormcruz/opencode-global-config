import org.concordion.integration.junit4.ConcordionRunner
import org.junit.runner.RunWith

import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths
import groovy.json.JsonSlurper

// ADR-0006: camada MCP opcional com fallback CLI garantido.
// Decisao de processo; a regra de revisao do proprio ADR exige ausencia de
// entradas MCP nao aprovadas nas configs canonicas dos harnesses gerenciados
// (fonte: docs/adr).
@RunWith(ConcordionRunner)
class Adr0006Fixture {
    private final Path root = Paths
        .get(System.getProperty('repo.root', '.'))
        .toAbsolutePath()

    private Path arquivoCanonicodaConfig() {
        return root.resolve('harness-conf/opencode.json')
    }

    private Map configCanonica() {
        def arquivo = arquivoCanonicodaConfig()
        if (!Files.isRegularFile(arquivo)) {
            return [:]
        }
        return new JsonSlurper().parse(arquivo) as Map
    }

    boolean configCanonicaExiste() {
        return Files.isRegularFile(arquivoCanonicodaConfig())
    }

    boolean nenhumaEntradaMcpNaoAprovada() {
        def config = configCanonica()
        return !config.containsKey('mcp') && !config.containsKey('mcpServers')
    }

    String executarVerificacoes() {
        def verificacoes = [
            configCanonicaExiste(),
            nenhumaEntradaMcpNaoAprovada(),
        ]
        return verificacoes.every { it } ? 'pass' : 'fail'
    }

    String getVeredito() {
        return executarVerificacoes()
    }
}
