import groovy.json.JsonSlurper
import org.concordion.integration.junit4.ConcordionRunner
import org.junit.runner.RunWith

import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths

@RunWith(ConcordionRunner)
class Adr0008Fixture {
    private final Path root = Paths
        .get(System.getProperty('repo.root', '.'))
        .toAbsolutePath()

    private String lerArquivo(String relativo) {
        def arquivo = root.resolve(relativo)
        return Files.isRegularFile(arquivo) ? arquivo.getText('UTF-8') : null
    }

    boolean configuracaoMcpCanonicaNaoTemCredenciais() {
        def arquivo = root.resolve('harness-conf/opencode.json')
        if (!Files.isRegularFile(arquivo)) {
            return false
        }
        def config = new JsonSlurper().parse(arquivo.toFile())
        def servidor = config.mcp?.get('ai-memory')
        def camposDeCredencial = ['headers', 'environment', 'token', 'apiKey']
        return servidor?.url == 'http://127.0.0.1:49374/mcp' &&
            !camposDeCredencial.any { campo -> servidor.containsKey(campo) }
    }

    boolean provisionamentoExigeMarcadorCompleto() {
        def bootstrap = lerArquivo('src/opencode_config/bootstrap/ai_memory.py')
        def shared = lerArquivo('src/opencode_config/lib/ai_memory.py')
        return bootstrap != null && shared != null &&
            shared.contains('AI_MEMORY_READY_MARKER') &&
            bootstrap.contains('_write_ready_marker(context.paths, network_is_owned)') &&
            bootstrap.contains('AI_MEMORY_WRAPPER_SHA256') &&
            bootstrap.contains('"--internal"')
    }

    boolean adaptersCondicionamORegistroMcp() {
        def opencode = lerArquivo('src/opencode_config/harnesses/opencode.py')
        def copilot = lerArquivo('src/opencode_config/harnesses/copilot.py')
        return opencode != null && copilot != null &&
            opencode.contains('materialize_filtered_config') &&
            opencode.contains('filter_ai_memory_config') &&
            copilot.contains('def _sync_mcp_config(') &&
            copilot.contains('is_ai_memory_provisioned')
    }

    boolean testesProtegemOsContratos() {
        def bootstrap = lerArquivo('tests/bootstrap/test_ai_memory_provision.py')
        def opencode = lerArquivo('tests/harnesses/test_opencode.py')
        def copilot = lerArquivo('tests/harnesses/test_copilot.py')
        return bootstrap != null && opencode != null && copilot != null &&
            bootstrap.contains('test_ai_memory_second_run_does_not_download_or_pull_again') &&
            bootstrap.contains('test_ai_memory_rollback_removes_runtime_but_preserves_data') &&
            opencode.contains('test_opencode_without_provisioned_ai_memory_filters_symlink_config') &&
            copilot.contains('test_copilot_adapter_merges_ai_memory_without_losing_existing_servers')
    }

    String executarVerificacoes() {
        def verificacoes = [
            configuracaoMcpCanonicaNaoTemCredenciais(),
            provisionamentoExigeMarcadorCompleto(),
            adaptersCondicionamORegistroMcp(),
            testesProtegemOsContratos(),
        ]
        return verificacoes.every { it } ? 'pass' : 'fail'
    }

    String getVeredito() {
        return executarVerificacoes()
    }
}
