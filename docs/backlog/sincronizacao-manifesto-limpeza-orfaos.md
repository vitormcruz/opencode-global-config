Nome: Sincronização genérica de artefatos com manifesto e limpeza de órfãos

Eu como desenvolvedor que utiliza múltiplos harnesses
Desejo que a sincronização registre os artefatos materializados em manifesto e remova órfãos com backup prévio
Para que recursos e perfis descontinuados não permaneçam ativos no ambiente local, preservando arquivos personalizados

## Regras de Negócio
- RN-012: Preservação de arquivos locais — Arquivos no diretório de destino que não foram gerados pela sincronização nem constam no manifesto de controle não podem ser alterados nem removidos.
- RN-013: Exclusão de órfãos do manifesto — Arquivos registrados no manifesto de sincronização anterior que deixarem de ser gerados na sincronização atual devem ser excluídos do diretório de destino.
- RN-014: Backup obrigatório prévio — Todo arquivo a ser excluído por ser órfão do manifesto deve ter uma cópia de backup preservada antes da sua remoção do diretório de destino.
- RN-015: Registro de artefatos em manifesto — Arquivos materializados por cópia durante a sincronização de um harness devem ser registrados no manifesto local para controle de ciclo de vida e rastreamento de órfãos.

## Requisitos Funcionais
- RF1: O sistema deve registrar em manifesto local os arquivos materializados durante a sincronização de um harness (atende RN-015).
- RF2: O sistema deve remover do diretório de destino os arquivos que constavam no manifesto anterior e não foram gerados na sincronização atual, gerando backup prévio (atende RN-013 e RN-014).
- RF3: O sistema deve manter inalterados no diretório de destino arquivos que não foram gerados pela sincronização nem constam no manifesto de controle (atende RN-012).

## Notas (opcional)
- Decisão de arquitetura: A lógica de controle de manifesto, validação de autoria e limpeza deve residir em módulo compartilhado na biblioteca central (`opencode_config.lib`), aplicável a agentes, skills e qualquer outro artefato sincronizado por cópia em qualquer harness.
- Proposta de implementação recomendada:
  1. Manifesto persistente: arquivo local por harness registrando os caminhos materializados (agentes, skills e arquivos avulsos) para guiar remoções em execuções futuras.
  2. Marcador de autoria: identificador no conteúdo gerado para confirmar que o arquivo pertence ao harness antes de qualquer exclusão, evitando apagar arquivos homônimos criados pelo usuário.
- Tratamento de legados locais (fora do código): Arquivos órfãos pré-existentes na máquina local antes da introdução do manifesto (como `curador-produto-editor.agent.md` e `val-harness.agent.md` em `%USERPROFILE%\.copilot\agents`) não serão tratados via código ou listas históricas embutidas; devem ser removidos pontualmente no ambiente do desenvolvedor, mantendo a implementação do produto simples e desacoplada de exceções do passado.

## Critérios de Aceitação

# language: pt

Esquema do Cenário: Registro de artefatos materializados no manifesto local (derivado de RF1)
  Dado que o repositório configura o artefato <artefato>
  Quando tento sincronizar um harness que copia os artefatos para as pastas de configuração
  E, depois, se busco o arquivo <arquivo> tanto na pasta de destino quanto no manifesto
  Então o arquivo foi <resultado_destino> no destino e <resultado_manifesto> no manifesto

  Exemplos:
    | artefato                 | arquivo                           | resultado_destino | resultado_manifesto |
    | "curador-produto"        | "curador-produto.agent.md"        | "encontrado"      | "registrado"        |
    | "skills/spec-executavel" | "skills/spec-executavel/SKILL.md" | "encontrado"      | "registrado"        |

Esquema do Cenário: Remoção do arquivo de destino após saída da configuração (derivado de RF2)
  Dado que o arquivo <arquivo> existe na pasta de destino
  E consta no manifesto anterior, mas saiu da configuração do repositório
  Quando tento sincronizar um harness que copia os artefatos para as pastas de configuração
  E, depois, se busco o arquivo <arquivo> na pasta de destino
  Então o arquivo foi <resultado_destino> no destino

  Exemplos:
    | arquivo                  | resultado_destino |
    | "agente-antigo.agent.md" | "não encontrado"  |
    | "skills/antiga/SKILL.md" | "não encontrado"  |

Esquema do Cenário: Criação de backup prévio para artefato removido (derivado de RF2)
  Dado que o arquivo <arquivo> existe na pasta de destino
  E consta no manifesto anterior, mas saiu da configuração do repositório
  Quando tento sincronizar um harness que copia os artefatos para as pastas de configuração
  E, depois, se busco o backup de <arquivo> na pasta de backup
  Então o backup foi <resultado_backup> na pasta de backup

  Exemplos:
    | arquivo                  | resultado_backup |
    | "agente-antigo.agent.md" | "encontrado"     |
    | "skills/antiga/SKILL.md" | "encontrado"     |

Esquema do Cenário: Atualização do manifesto após remoção de artefato (derivado de RF2)
  Dado que o arquivo <arquivo> consta no manifesto anterior, mas saiu da configuração do repositório
  Quando tento sincronizar um harness que copia os artefatos para as pastas de configuração
  E, depois, se consulto o registro de <arquivo> no manifesto
  Então o registro foi <resultado_manifesto> no manifesto

  Exemplos:
    | arquivo                  | resultado_manifesto |
    | "agente-antigo.agent.md" | "não registrado"    |
    | "skills/antiga/SKILL.md" | "não registrado"    |

Esquema do Cenário: Preservação de arquivos locais não gerenciados (derivado de RF3)
  Dado que o arquivo personalizado <arquivo> existe na pasta de destino
  E nunca constou em nenhum manifesto nem fazia parte da configuração do repositório
  Quando tento sincronizar um harness que copia os artefatos para as pastas de configuração
  E, depois, se busco o arquivo <arquivo> na pasta de destino e seu backup na pasta de backup
  Então o arquivo foi <resultado_destino> no destino e seu backup foi <resultado_backup> na pasta de backup

  Exemplos:
    | arquivo                       | resultado_destino | resultado_backup |
    | "meu-agente-custom.agent.md"  | "encontrado"      | "não encontrado" |
    | "skills/minha-skill/SKILL.md" | "encontrado"      | "não encontrado" |
