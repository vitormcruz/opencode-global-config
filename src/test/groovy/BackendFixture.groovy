import org.concordion.integration.junit4.ConcordionRunner
import org.junit.runner.RunWith

import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths

@RunWith(ConcordionRunner)
class BackendFixture {
    String executarVerificacoes() {
        def root = Paths.get(System.getProperty('repo.root', '.'))
        def required = [
            'docs/specs/Backend.md',
            'build.gradle',
            'src/opencode_config/product_tests/backend.py',
            'testes-produto/backend',
        ]
        return required.every { relative -> Files.isRegularFile(root.resolve(relative)) }
            ? 'pass'
            : 'fail'
    }

    String getVeredito() {
        executarVerificacoes()
    }
}
