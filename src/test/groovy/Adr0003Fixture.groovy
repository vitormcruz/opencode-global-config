import org.concordion.integration.junit4.ConcordionRunner
import org.junit.runner.RunWith

import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths

// ADR-0003: Qwen3-0.6B como padrao da integracao OpenCode.
// Verifica provider unico, artefato fixado e checksum validado no servidor
// local (fonte: docs/adr).
@RunWith(ConcordionRunner)
class Adr0003Fixture {
    private final Path root = Paths
        .get(System.getProperty('repo.root', '.'))
        .toAbsolutePath()

    private String lerServidorLocal() {
        def arquivo = root.resolve('tests/integration/model/local_model_server.py')
        return Files.isRegularFile(arquivo) ? arquivo.getText('UTF-8') : null
    }

    boolean providerUnicoEFixedo() {
        def servidor = lerServidorLocal()
        return servidor != null &&
            servidor.contains('provider="qwen-local"') &&
            servidor.contains('name="qwen3-0.6b"')
    }

    boolean artefatoQwenEFixado() {
        def servidor = lerServidorLocal()
        return servidor != null &&
            servidor.contains('file_name="Qwen3-0.6B-Q8_0.gguf"')
    }

    boolean checksumDoArtefatoEValidado() {
        def servidor = lerServidorLocal()
        return servidor != null && servidor.contains(
            '9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031'
        )
    }

    String executarVerificacoes() {
        def verificacoes = [
            providerUnicoEFixedo(),
            artefatoQwenEFixado(),
            checksumDoArtefatoEValidado(),
        ]
        return verificacoes.every { it } ? 'pass' : 'fail'
    }

    String getVeredito() {
        return executarVerificacoes()
    }
}
