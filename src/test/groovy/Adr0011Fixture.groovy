import org.concordion.integration.junit4.ConcordionRunner
import org.junit.runner.RunWith

import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths

// ADR-0011: compactacao DCP como mecanismo preferido no OpenCode.
@RunWith(ConcordionRunner)
class Adr0011Fixture {
    private final Path root = Paths
        .get(System.getProperty('repo.root', '.'))
        .toAbsolutePath()

    private String lerArquivo(String relativo) {
        def arquivo = root.resolve(relativo)
        return Files.isRegularFile(arquivo) ? arquivo.getText('UTF-8') : null
    }

    // A spec do plugin esta pinada com versao fixa no array plugin do
    // config canonico (sem faixa solta, sem autoUpdate de versao).
    private boolean pluginPinado() {
        def config = lerArquivo('harness-conf/opencode.json')
        if (config == null) {
            return false
        }
        def parsed = new groovy.json.JsonSlurper().parseText(config)
        def entrada = (parsed.plugin ?: [])
            .find { it.startsWith('@tarquinen/opencode-dcp') }
        return entrada != null &&
            entrada ==~ /@tarquinen\/opencode-dcp@\d+\.\d+\.\d+/
    }

    // A config propria do plugin existe, com autoUpdate desligado e gate
    // allow na tool compress (o rollback rapido segue sendo deny).
    private boolean configPropriaValida() {
        def config = lerArquivo('harness-conf/dcp.jsonc')
        if (config == null) {
            return false
        }
        def semComentarios = config
            .replaceAll(/(?s)\/\*.*?\*\//, '')
            .replaceAll(/(?m)\/\/.*$/, '')
        def parsed = new groovy.json.JsonSlurper().parseText(semComentarios)
        return parsed.autoUpdate == false &&
            parsed.compress?.permission == 'allow'
    }

    // As duas strategies do OpenCode declaram o destino dcp.jsonc; o
    // adapter Copilot nao declara nenhum destino DCP (fora do escopo).
    private boolean destinoSomenteNoOpencode() {
        def opencode = lerArquivo('src/opencode_config/harnesses/opencode.py')
        def copilot = lerArquivo('src/opencode_config/harnesses/copilot.py')
        if (opencode == null || copilot == null) {
            return false
        }
        return opencode.count('"dcp.jsonc"') >= 2 &&
            !copilot.contains('dcp')
    }

    // O README documenta para o humano o plugin, a tool compress e o
    // rollback.
    private boolean readmeDocumenta() {
        def readme = lerArquivo('README.md')
        return readme != null && readme.contains('@tarquinen/opencode-dcp')
    }

    String executarVerificacoes() {
        def verificacoes = [
            pluginPinado(),
            configPropriaValida(),
            destinoSomenteNoOpencode(),
            readmeDocumenta(),
        ]
        return verificacoes.every { it } ? 'pass' : 'fail'
    }

    String getVeredito() {
        return executarVerificacoes()
    }
}
