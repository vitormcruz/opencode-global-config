import org.concordion.integration.junit4.ConcordionRunner
import org.junit.runner.RunWith

import java.nio.file.Files
import java.nio.file.Paths

@RunWith(ConcordionRunner)
class SegurancaFixture {
    String executarVerificacoes() {
        def root = Paths.get(System.getProperty('repo.root', '.'))
        def required = [
            'docs/specs/Seguranca.md',
            'docs/adr/0006-camada-mcp-opcional-com-fallback-cli.md',
            'src/opencode_config/product_tests/security.py',
            'testes-produto/seguranca',
        ]
        return required.every { relative -> Files.isRegularFile(root.resolve(relative)) }
            ? 'pass'
            : 'fail'
    }

    String getVeredito() {
        executarVerificacoes()
    }
}
