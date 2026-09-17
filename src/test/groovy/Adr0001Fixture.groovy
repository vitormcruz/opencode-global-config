import org.concordion.integration.junit4.ConcordionRunner
import org.junit.runner.RunWith

import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths

// ADR-0001: migracao de MCPs locais para CLIs nativos.
// Verifica os artefatos que materializam a decisao (fonte: docs/adr).
@RunWith(ConcordionRunner)
class Adr0001Fixture {
    private final Path root = Paths
        .get(System.getProperty('repo.root', '.'))
        .toAbsolutePath()

    private boolean arquivoExiste(String relativo) {
        return Files.isRegularFile(root.resolve(relativo))
    }

    boolean entrypointsDeBootstrapExistem() {
        return arquivoExiste('scripts/bootstrap_repo/configurar-repo.sh') &&
            arquivoExiste('scripts/bootstrap_repo/configurar-repo.ps1')
    }

    boolean makefileFoiRemovido() {
        return !Files.isRegularFile(root.resolve('Makefile'))
    }

    boolean comportamentoExecutivoViveNoPacotePython() {
        return Files.isDirectory(root.resolve('src/opencode_config'))
    }

    boolean testesDeMigracaoExistem() {
        return arquivoExiste('tests/test_mcp_wrapper_cleanup.py') &&
            arquivoExiste('tests/test_crawl4ai_cleanup.py') &&
            arquivoExiste('tests/scripts/bootstrap_repo/test_repo_structure.py')
    }

    String executarVerificacoes() {
        def verificacoes = [
            entrypointsDeBootstrapExistem(),
            makefileFoiRemovido(),
            comportamentoExecutivoViveNoPacotePython(),
            testesDeMigracaoExistem(),
        ]
        return verificacoes.every { it } ? 'pass' : 'fail'
    }

    String getVeredito() {
        return executarVerificacoes()
    }
}
