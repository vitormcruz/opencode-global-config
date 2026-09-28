import org.concordion.integration.junit4.ConcordionRunner
import org.junit.runner.RunWith

import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths

// ADR-0010: remocao do plugin opencode-task-model no suporte nativo.
@RunWith(ConcordionRunner)
class Adr0010Fixture {
    private final Path root = Paths
        .get(System.getProperty('repo.root', '.'))
        .toAbsolutePath()

    private String lerArquivo(String relativo) {
        def arquivo = root.resolve(relativo)
        return Files.isRegularFile(arquivo) ? arquivo.getText('UTF-8') : null
    }

    // A citacao a opencode-task-model deve estar nas tres pontas duraveis
    // (config, README e AGENTS.base.md) enquanto o plugin esta instalado,
    // ou ausente das tres depois do procedimento; estado misto reprova.
    private boolean estadoHomogeneo() {
        def config = lerArquivo('harness-conf/opencode.json')
        def readme = lerArquivo('README.md')
        def base = lerArquivo('harness-conf/AGENTS.base.md')
        if (config == null || readme == null || base == null) {
            return false
        }
        def presente = [
            config,
            readme,
            base,
        ].collect { conteudo -> conteudo.contains('opencode-task-model') }
        return presente.every { it } || presente.none { it }
    }

    // Enquanto instalado, a entrada do config casa com versao_pinada do
    // UPSTREAM.md. Sem entrada (plugin removido), a verificacao passa.
    private boolean pinCasaComUpstream() {
        def config = lerArquivo('harness-conf/opencode.json')
        if (config == null) {
            return false
        }
        def parsed = new groovy.json.JsonSlurper().parseText(config)
        def entrada = (parsed.plugin ?: [])
            .find { it.startsWith('opencode-task-model') }
        if (entrada == null) {
            return true
        }
        def upstream = lerArquivo(
            'harness-conf/plugins/opencode-task-model/UPSTREAM.md'
        )
        if (upstream == null) {
            return false
        }
        def matcher = (upstream =~ /(?m)^versao_pinada:\s*(\S+)/)
        return matcher.find() &&
            entrada == "opencode-task-model@${matcher.group(1)}"
    }

    String executarVerificacoes() {
        def verificacoes = [
            estadoHomogeneo(),
            pinCasaComUpstream(),
        ]
        return verificacoes.every { it } ? 'pass' : 'fail'
    }

    String getVeredito() {
        return executarVerificacoes()
    }
}
