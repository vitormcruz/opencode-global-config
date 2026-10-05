import org.concordion.integration.junit4.ConcordionRunner
import org.junit.runner.RunWith

import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths

// ADR-0007: o contrato CLI é `harness-skills detect FAMILY`.
@RunWith(ConcordionRunner)
class Adr0007Fixture {
    private final Path root = Paths
        .get(System.getProperty('repo.root', '.'))
        .toAbsolutePath()

    private String lerArquivo(String relativo) {
        def arquivo = root.resolve(relativo)
        return Files.isRegularFile(arquivo) ? arquivo.getText('UTF-8') : null
    }

    boolean comandoDeDeteccaoExiste() {
        def codigo = lerArquivo('src/opencode_config/cli/skills_sync.py')
        return codigo != null &&
            codigo.contains('"detect"') &&
            codigo.contains('_detect_upstream')
    }

    boolean cloneTemporarioFicaForaDoRepo() {
        def codigo = lerArquivo('src/opencode_config/cli/skills_sync.py')
        return codigo != null &&
            codigo.contains('outside_repo=repo_root') &&
            codigo.contains('show_progress=True') &&
            codigo.contains('temporary.cleanup()')
    }

    boolean testesGuardamAsRegrasDaDeteccao() {
        def testes = lerArquivo('tests/skills_mgmt/test_upstream_detect.py')
        return testes != null &&
            testes.contains('test_detect_is_read_only_repeats_refused_changes_and_cleans_clone') &&
            testes.contains('test_detect_omits_frozen_skills_from_family_changes') &&
            testes.contains('test_detect_expands_shallow_clone_when_base_sha_is_missing')
    }

    String executarVerificacoes() {
        def verificacoes = [
            comandoDeDeteccaoExiste(),
            cloneTemporarioFicaForaDoRepo(),
            testesGuardamAsRegrasDaDeteccao(),
        ]
        return verificacoes.every { it } ? 'pass' : 'fail'
    }

    String getVeredito() {
        return executarVerificacoes()
    }
}
