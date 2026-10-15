import org.concordion.integration.junit4.ConcordionRunner
import org.junit.runner.RunWith

import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths

// ADR-0012: permissoes de delegacao (tool task) abertas.
@RunWith(ConcordionRunner)
class Adr0012Fixture {
    private final Path root = Paths
        .get(System.getProperty('repo.root', '.'))
        .toAbsolutePath()

    private String lerArquivo(String relativo) {
        def arquivo = root.resolve(relativo)
        return Files.isRegularFile(arquivo) ? arquivo.getText('UTF-8') : null
    }

    // Entradas indentadas do bloco task do frontmatter (linhas de 4+
    // espacos apos "  task:", ate a primeira linha menos indentada).
    private List<String> entradasDoBlocoTask(String conteudo) {
        def linhas = conteudo.split('\n', -1)
        def inicio = linhas.findIndexOf { it == '  task:' }
        if (inicio < 0) {
            return []
        }
        def entradas = []
        for (int i = inicio + 1; i < linhas.length; i++) {
            def linha = linhas[i]
            if (!linha.startsWith('    ')) {
                break
            }
            entradas << linha
        }
        return entradas
    }

    // Nenhum agente declara deny na secao permission.task (wildcard ou
    // nomeada); todo bloco task declarado usa o wildcard "*": allow.
    private boolean delegacaoAbertaNosAgentes() {
        def agentes = root.resolve('harness-conf/agents')
        if (!Files.isDirectory(agentes)) {
            return false
        }
        def arquivos = Files.list(agentes).toList().findAll {
            it.fileName.toString().endsWith('.md')
        }
        if (arquivos.empty) {
            return false
        }
        return arquivos.every { arquivo ->
            def conteudo = arquivo.getText('UTF-8')
            def semTask = !conteudo.contains('  task:')
            def denyNomeadoEmTask = entradasDoBlocoTask(conteudo)
                .any { it.contains('deny') }
            return !conteudo.contains('"*": deny') &&
                !denyNomeadoEmTask &&
                (semTask || conteudo.contains('    "*": allow'))
        }
    }

    // O adapter Copilot emite instrucao de delegacao aberta quando ha
    // wildcard allow e mantem a instrucao restritiva para politicas
    // fechadas de repositorios consumidores.
    private boolean adapterCobreOsDoisModos() {
        def copilot = lerArquivo('src/opencode_config/harnesses/copilot.py')
        return copilot != null &&
            copilot.contains('_open_delegation_instructions') &&
            copilot.contains('somente com estes')
    }

    // A guarda anti-regressao reprova qualquer deny em permission.task
    // e cita esta ADR como fonte da politica.
    private boolean guardaAntiRegressaoExiste() {
        def guarda = lerArquivo('tests/agents/test_task_spawnable_modes.py')
        return guarda != null &&
            guarda.contains('_find_task_deny_entries') &&
            guarda.contains('docs/adr/0012-permissoes-task-abertas.md')
    }

    String executarVerificacoes() {
        def verificacoes = [
            delegacaoAbertaNosAgentes(),
            adapterCobreOsDoisModos(),
            guardaAntiRegressaoExiste(),
        ]
        return verificacoes.every { it } ? 'pass' : 'fail'
    }

    String getVeredito() {
        return executarVerificacoes()
    }
}
