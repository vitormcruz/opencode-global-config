import org.concordion.integration.junit4.ConcordionRunner
import org.junit.runner.RunWith

import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths

// ADR-0004: adapters de harness multiplataforma.
// Verifica registry de harnesses, factory com injecao de strategy por SO e
// utilitarios de lib compartilhados (fonte: docs/adr).
@RunWith(ConcordionRunner)
class Adr0004Fixture {
    private final Path root = Paths
        .get(System.getProperty('repo.root', '.'))
        .toAbsolutePath()

    private String lerArquivo(String relativo) {
        def arquivo = root.resolve(relativo)
        return Files.isRegularFile(arquivo) ? arquivo.getText('UTF-8') : null
    }

    boolean registryDeHarnessesExiste() {
        def contrato = lerArquivo('src/opencode_config/harnesses/__init__.py')
        return contrato != null && contrato.contains('HARNESSES')
    }

    boolean factoryInjetaStrategyPorSo() {
        def opencode = lerArquivo('src/opencode_config/harnesses/opencode.py')
        return opencode != null &&
            opencode.contains('class OpenCodePosix') &&
            opencode.contains('class OpenCodeWindows')
    }

    boolean utilitariosDeLibSaoCompartilhados() {
        return Files.isRegularFile(root.resolve('src/opencode_config/lib/sync.py')) &&
            Files.isRegularFile(root.resolve('src/opencode_config/lib/windows_env.py'))
    }

    String executarVerificacoes() {
        def verificacoes = [
            registryDeHarnessesExiste(),
            factoryInjetaStrategyPorSo(),
            utilitariosDeLibSaoCompartilhados(),
        ]
        return verificacoes.every { it } ? 'pass' : 'fail'
    }

    String getVeredito() {
        return executarVerificacoes()
    }
}
