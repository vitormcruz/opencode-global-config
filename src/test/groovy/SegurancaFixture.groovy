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
            contém('docs/specs/Seguranca.md', '`v2.4.1`') && contém(
                'src/opencode_config/bootstrap/ai_memory.py',
                'AI_MEMORY_WRAPPER_VERSION = "v2.4.1"',
                'https://github.com/akitaonrails/ai-memory/releases/download/',
                'urlopen(url, timeout=_DOWNLOAD_IDLE_TIMEOUT_SECONDS)',
            ) && contém(
                'tests/bootstrap/test_ai_memory_provision.py',
                'test_ai_memory_upstream_release_pins_match_reviewed_artifacts',
                'test_ai_memory_provision_downloads_verified_wrapper_and_restricts_container',
            ),
        )
    }

    String getVereditoSec01() { verificarSec01() }

    String verificarSec02() {
        resultado(
            contém(
                'docs/specs/Seguranca.md',
                '49c965a0319dbe9c525d552a9a4c8b3464e5dd278e36d5dc7a03edee8b5502e6',
                'a626d115e0350afe934954c02c9064d30b708c58316763a9c6674ef5d0c8e3d9',
                '5ce8700b2d0a5243370a544c805f86c32d19aaca2251ecae32d66c09d221ef6e',
            ) && contém(
                'src/opencode_config/bootstrap/ai_memory.py',
                'AI_MEMORY_WRAPPER_SHA256',
                '49c965a0319dbe9c525d552a9a4c8b3464e5dd278e36d5dc7a03edee8b5502e6',
                'AI_MEMORY_IMAGE_MANIFEST_SHA256',
                'a626d115e0350afe934954c02c9064d30b708c58316763a9c6674ef5d0c8e3d9',
                'AI_MEMORY_IMAGE_LINUX_AMD64_SHA256',
                '5ce8700b2d0a5243370a544c805f86c32d19aaca2251ecae32d66c09d221ef6e',
                'AI_MEMORY_IMAGE = f"{AI_MEMORY_IMAGE_TAG}@sha256:',
                '{AI_MEMORY_IMAGE_LINUX_AMD64_SHA256}"',
                'expected_sha256=expected_hash',
            ) && contém(
                'tests/bootstrap/test_ai_memory_provision.py',
                'test_ai_memory_upstream_release_pins_match_reviewed_artifacts',
                'test_ai_memory_download_hash_mismatch_blocks_installation',
            ),
        )
    }

    String getVereditoSec02() { verificarSec02() }

    String verificarSec03() {
        resultado(
            contém(
                'docs/specs/Seguranca.md',
                '127.0.0.1',
                'IPv4 privado do container',
                'http://<ipv4-da-bridge>:49374/mcp',
                'AI_MEMORY_ALLOWED_HOSTS',
                'host.docker.internal',
                '405',
                '403',
            ) && contém(
                'src/opencode_config/bootstrap/ai_memory.py',
                'AI_MEMORY_HOST = "127.0.0.1"',
                'def _resolve_mcp_url(',
                'def _resolve_internal_bridge_mcp_url(',
                'AI_MEMORY_CONTAINER_START_SCRIPT',
                'AI_MEMORY_ALLOWED_HOSTS=',
                'localhost,127.0.0.1,::1,host.docker.internal,$container_ip',
                'return f"http://{address.compressed}:{AI_MEMORY_PORT}/mcp"',
                'hostname -i',
                '"--publish"',
            ) && contém(
                'tests/bootstrap/test_ai_memory_provision.py',
                '127.0.0.1:49374:49374',
                'test_ai_memory_uses_internal_bridge_url_when_docker_does_not_publish_loopback',
                'test_ai_memory_endpoint_probe_rejects_disallowed_host_response',
                'test_ai_memory_endpoint_probe_accepts_method_not_allowed_from_mcp_get',
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
                'docs/specs/Seguranca.md',
                '`~/.local/state/ai-memory/`',
                '`.bootstrap-mcp-url`',
            ) && contém(
                'README.md',
                '~/.local/share/ai-memory/',
                '~/.local/state/ai-memory/',
                '.bootstrap-mcp-url',
                'dado sensível',
                'não o versione',
            ) && contém(
                'src/opencode_config/bootstrap/ai_memory.py',
                'return paths.home / ".local" / "state" / "ai-memory" / AI_MEMORY_URL_MARKER',
                'Dados preservados em',
                'data_directory.chmod(0o700)',
            ) && contém(
                'tests/bootstrap/test_ai_memory_provision.py',
                'test_ai_memory_uses_internal_bridge_url_when_docker_does_not_publish_loopback',
                'test_ai_memory_rollback_removes_runtime_but_preserves_data',
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
                'docs/specs/Seguranca.md',
                'rede Docker `internal`',
                'não altera o isolamento',
            ) && contém(
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
