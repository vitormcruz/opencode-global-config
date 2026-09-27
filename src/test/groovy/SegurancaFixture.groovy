import org.concordion.integration.junit4.ConcordionRunner
import org.junit.runner.RunWith

import groovy.json.JsonSlurper
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths

@RunWith(ConcordionRunner)
class SegurancaFixture {
    private final Path root = Paths
        .get(System.getProperty('repo.root', '.'))
        .toAbsolutePath()

    private boolean contém(String relativo, String... trechos) {
        def arquivo = root.resolve(relativo)
        if (!Files.isRegularFile(arquivo)) {
            return false
        }
        def conteúdo = arquivo.getText('UTF-8')
        return trechos.every { trecho -> conteúdo.contains(trecho) }
    }

    private String resultado(boolean válido) {
        válido ? 'pass' : 'fail'
    }

    String verificarSec01() {
        resultado(
            contém(
                'src/opencode_config/bootstrap/ai_memory.py',
                'AI_MEMORY_WRAPPER_URL',
                'urlopen(url, timeout=_DOWNLOAD_IDLE_TIMEOUT_SECONDS)',
            ) && contém(
                'tests/bootstrap/test_ai_memory_provision.py',
                'test_ai_memory_provision_downloads_verified_wrapper_and_restricts_container',
            ),
        )
    }

    String getVereditoSec01() { verificarSec01() }

    String verificarSec02() {
        resultado(
            contém(
                'src/opencode_config/bootstrap/ai_memory.py',
                'AI_MEMORY_WRAPPER_SHA256',
                'expected_sha256=expected_hash',
            ) && contém(
                'tests/bootstrap/test_ai_memory_provision.py',
                'test_ai_memory_download_hash_mismatch_blocks_installation',
            ),
        )
    }

    String getVereditoSec02() { verificarSec02() }

    String verificarSec03() {
        resultado(
            contém(
                'src/opencode_config/bootstrap/ai_memory.py',
                'AI_MEMORY_HOST = "127.0.0.1"',
                '"--publish"',
            ) && contém(
                'tests/bootstrap/test_ai_memory_provision.py',
                '127.0.0.1:49374:49374',
            ),
        )
    }

    String getVereditoSec03() { verificarSec03() }

    String verificarSec04() {
        resultado(
            contém(
                'src/opencode_config/bootstrap/ai_memory.py',
                '_port_is_in_use',
                'libere a porta antes de reexecutar',
            ) && contém(
                'tests/bootstrap/test_ai_memory_provision.py',
                'test_ai_memory_occupied_loopback_port_aborts_before_container_creation',
            ),
        )
    }

    String getVereditoSec04() { verificarSec04() }

    String verificarSec05() {
        resultado(
            contém(
                'src/opencode_config/bootstrap/ai_memory.py',
                'plugin_hash_before',
                'AVISO: o hash de ai-memory.ts mudou',
            ) && contém(
                'tests/bootstrap/test_ai_memory_provision.py',
                'test_ai_memory_plugin_hash_drift_is_reported',
            ),
        )
    }

    String getVereditoSec05() { verificarSec05() }

    String verificarSec06() {
        resultado(
            contém(
                'src/opencode_config/bootstrap/ai_memory.py',
                'AI_MEMORY_WRAPPER_SHA256',
                'docker, "pull", AI_MEMORY_IMAGE',
            ) && contém(
                'tests/bootstrap/test_ai_memory_provision.py',
                'test_ai_memory_second_run_does_not_download_or_pull_again',
                'test_ai_memory_existing_wrapper_drift_requires_explicit_upgrade',
            ),
        )
    }

    String getVereditoSec06() { verificarSec06() }

    String verificarSec07() {
        resultado(
            contém(
                'README.md',
                '~/.local/share/ai-memory/',
                'dado sensível',
                'não o versione',
            ) && contém(
                'src/opencode_config/bootstrap/ai_memory.py',
                'Dados preservados em',
                'data_directory.chmod(0o700)',
            ),
        )
    }

    String getVereditoSec07() { verificarSec07() }

    String verificarSec08() {
        resultado(
            contém(
                'src/opencode_config/bootstrap/ai_memory.py',
                'def rollback_ai_memory(',
                '_restore_legacy_jsonc',
                '_remove_wrapper_artifacts',
            ) && contém(
                'tests/bootstrap/test_ai_memory_provision.py',
                'test_ai_memory_rollback_removes_runtime_but_preserves_data',
            ) && contém('README.md', 'opencode-bootstrap --rollback-ai-memory'),
        )
    }

    String getVereditoSec08() { verificarSec08() }

    String verificarSec09() {
        resultado(
            contém(
                'src/opencode_config/bootstrap/ai_memory.py',
                'Docker ausente.',
                'O bloco MCP foi desabilitado nos harnesses.',
            ) && contém(
                'tests/bootstrap/test_ai_memory_provision.py',
                'test_ai_memory_without_docker_warns_and_cleans_active_hooks',
            ) && contém(
                'tests/harnesses/test_opencode.py',
                'test_opencode_without_provisioned_ai_memory_filters_symlink_config',
            ) && contém(
                'tests/harnesses/test_copilot.py',
                'test_copilot_adapter_removes_ai_memory_entry_when_provisioning_is_incomplete',
            ),
        )
    }

    String getVereditoSec09() { verificarSec09() }

    String verificarSec10() {
        resultado(
            contém(
                'src/opencode_config/harnesses/copilot.py',
                'def _sync_mcp_config(',
                'backup_copy(destination, backup_dir)',
            ) && contém(
                'tests/harnesses/test_copilot.py',
                'test_copilot_adapter_merges_ai_memory_without_losing_existing_servers',
                'mcp-config.json',
            ),
        )
    }

    String getVereditoSec10() { verificarSec10() }

    String verificarSec11() {
        def configFile = root.resolve('harness-conf/opencode.json')
        if (!Files.isRegularFile(configFile)) {
            return 'fail'
        }
        def config = new JsonSlurper().parse(configFile.toFile())
        def server = config.mcp?.get('ai-memory')
        def credentialFields = ['headers', 'environment', 'token', 'apiKey']
        return server?.url == 'http://127.0.0.1:49374/mcp' &&
            !credentialFields.any { field -> server.containsKey(field) }
            ? 'pass'
            : 'fail'
    }

    String getVereditoSec11() { verificarSec11() }

    String verificarSec21() {
        resultado(
            contém(
                'src/opencode_config/bootstrap/ai_memory.py',
                '"--internal"',
                'AI_MEMORY_NETWORK',
            ) && contém(
                'tests/bootstrap/test_ai_memory_provision.py',
                'test_ai_memory_provision_downloads_verified_wrapper_and_restricts_container',
                'network", "create',
            ),
        )
    }

    String getVereditoSec21() { verificarSec21() }

    String executarVerificacoesAiMemory() {
        def verificações = [
            verificarSec01(), verificarSec02(), verificarSec03(),
            verificarSec04(), verificarSec05(), verificarSec06(),
            verificarSec07(), verificarSec08(), verificarSec09(),
            verificarSec10(), verificarSec11(), verificarSec21(),
        ]
        verificações.every { it == 'pass' } ? 'pass' : 'fail'
    }

    String getVereditoAiMemory() { executarVerificacoesAiMemory() }

    String executarVerificacoes() {
        def root = Paths.get(System.getProperty('repo.root', '.'))
        def required = [
            'docs/specs/Seguranca.md',
            'docs/adr/0006-camada-mcp-opcional-com-fallback-cli.md',
            'src/opencode_config/product_tests/security.py',
            'testes-produto/seguranca',
        ]
        return required.every { relative -> Files.isRegularFile(root.resolve(relative)) } &&
            executarVerificacoesAiMemory() == 'pass'
            ? 'pass'
            : 'fail'
    }

    String getVeredito() {
        executarVerificacoes()
    }
}
