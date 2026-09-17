import org.concordion.integration.junit4.ConcordionRunner
import org.junit.runner.RunWith

import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths

// ADR-0002: testes de integracao com modelo on-premises.
// Verifica que a integracao roda no harness local com rede Docker interna,
// sem caminho de egress para provedor externo (fonte: docs/adr).
@RunWith(ConcordionRunner)
class Adr0002Fixture {
    private final Path root = Paths
        .get(System.getProperty('repo.root', '.'))
        .toAbsolutePath()

    private String lerArquivo(String relativo) {
        def arquivo = root.resolve(relativo)
        return Files.isRegularFile(arquivo) ? arquivo.getText('UTF-8') : null
    }

    boolean suiteComportamentalExiste() {
        return lerArquivo('tests/integration/docker/container_test_opencode.py') != null
    }

    boolean redeDockerDedicadaEIinterna() {
        def script = lerArquivo('tests/integration/docker/container_test_opencode.py')
        return script != null &&
            script.contains('NETWORK_NAME = "opencode-test-net"') &&
            script.contains('internal')
    }

    boolean modeloLocalExisteNoHost() {
        return Files.isRegularFile(root.resolve('tests/integration/model/local_model_server.py'))
    }

    String executarVerificacoes() {
        def verificacoes = [
            suiteComportamentalExiste(),
            redeDockerDedicadaEIinterna(),
            modeloLocalExisteNoHost(),
        ]
        return verificacoes.every { it } ? 'pass' : 'fail'
    }

    String getVeredito() {
        return executarVerificacoes()
    }
}
