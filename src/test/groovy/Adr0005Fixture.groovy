import org.concordion.integration.junit4.ConcordionRunner
import org.junit.runner.RunWith

import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths

// ADR-0005: taxonomia de testes agnostica de SO e harness.
// Verifica os markers aceitos, a ausencia dos revogados e os guardas da
// taxonomia (fonte: docs/adr).
@RunWith(ConcordionRunner)
class Adr0005Fixture {
    private final Path root = Paths
        .get(System.getProperty('repo.root', '.'))
        .toAbsolutePath()

    private String lerArquivo(String relativo) {
        def arquivo = root.resolve(relativo)
        return Files.isRegularFile(arquivo) ? arquivo.getText('UTF-8') : null
    }

    private boolean declaraMarker(String pyproject, String marker) {
        return pyproject.contains("    \"${marker}:")
    }

    boolean markersAceitosEstaoRegistrados() {
        def pyproject = lerArquivo('pyproject.toml')
        return pyproject != null && ['unit', 'integration', 'agent_eval', 'all']
            .every { declaraMarker(pyproject, it) }
    }

    boolean markersRevogadosEstaoAusentes() {
        def pyproject = lerArquivo('pyproject.toml')
        if (pyproject == null) {
            return false
        }
        def revogados = ['tools', 'opencode', 'copilot', 'opencode_context']
        return revogados.every { !declaraMarker(pyproject, it) }
    }

    boolean guardaDaTaxonomiaExiste() {
        return Files.isRegularFile(root.resolve('tests/test_taxonomy.py')) &&
            Files.isRegularFile(root.resolve('tests/test_package_setup.py'))
    }

    String executarVerificacoes() {
        def verificacoes = [
            markersAceitosEstaoRegistrados(),
            markersRevogadosEstaoAusentes(),
            guardaDaTaxonomiaExiste(),
        ]
        return verificacoes.every { it } ? 'pass' : 'fail'
    }

    String getVeredito() {
        return executarVerificacoes()
    }
}
