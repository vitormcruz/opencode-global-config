import org.concordion.integration.junit4.ConcordionRunner
import org.junit.runner.RunWith

import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths

// ADR-0009: referências de skills de domínio ficam somente na cópia Copilot.
@RunWith(ConcordionRunner)
class Adr0009Fixture {
    private final Path root = Paths
        .get(System.getProperty('repo.root', '.'))
        .toAbsolutePath()

    private String lerArquivo(String relativo) {
        def arquivo = root.resolve(relativo)
        return Files.isRegularFile(arquivo) ? arquivo.getText('UTF-8') : null
    }

    boolean adapterGeraBlocoDeReferencias() {
        def codigo = lerArquivo('src/opencode_config/harnesses/copilot.py')
        return codigo != null &&
            codigo.contains('_skill_reference_block') &&
            codigo.contains('_agent_skill_allow_patterns') &&
            codigo.contains('<!-- BEGIN COPILOT GENERATED SKILLS -->') &&
            codigo.contains('route.destination.parent == skill_plan.auxiliary_directory')
    }

    boolean testeGuardaOContratoDoBloco() {
        def testes = lerArquivo('tests/harnesses/test_copilot.py')
        return testes != null &&
            testes.contains(
                'test_copilot_adapter_generates_skill_references_only_for_allowed_agents'
            ) &&
            testes.contains('Descrição completa da skill') &&
            testes.contains('expected_skill_path') &&
            testes.contains('EXTERNAL_SKILL_BODY_MARKER')
    }

    String executarVerificacoes() {
        def verificacoes = [
            adapterGeraBlocoDeReferencias(),
            testeGuardaOContratoDoBloco(),
        ]
        return verificacoes.every { it } ? 'pass' : 'fail'
    }

    String getVeredito() {
        return executarVerificacoes()
    }
}
