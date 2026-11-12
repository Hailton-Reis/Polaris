# Conquistas e grimórios — P20261112.1

Beta.11/código112 em desenvolvimento, posterior a fdc768e. A beta.10 pública permanece igual. Esta revisão conclui o refinamento das artes e amplia o desbloqueio dos ícones com conquistas locais.

## Quatro caminhos alternativos

O Grimório Polaris fica sempre disponível. Para cada alternativa, basta cumprir **uma** das condições da linha:

| Grimório | Pontos de leitura | Obras na biblioteca | Obras iniciadas | Obras concluídas lidas |
| --- | ---: | ---: | ---: | ---: |
| Três folhas | 900 | 5 | 3 | 1 |
| Quatro folhas · Amado pela mana | 4.500 | 25 | 10 | 5 |
| Cinco folhas · sombrio | 9.000 | 100 | 25 | 10 |

São 12 conquistas, divididas entre Leitor, Colecionador, Explorador e Finalizador. Os nomes, requisitos, progresso e condição de disponibilidade aparecem na Jornada e na seleção dos ícones. Não é necessário cumprir os quatro caminhos. As conquistas não gastam nem acrescentam XP; o cálculo de XP existente continua ligado à leitura. Temas e recursos do leitor permanecem disponíveis.

## O que é contado

A contagem usa a projeção lógica da biblioteca de quadrinhos, antes de filtros de busca/categoria. Edições já vinculadas aparecem como uma obra; registros repetidos com o mesmo ID não multiplicam a conquista. Obras distintas que ainda não puderam ser associadas com segurança seguem a apresentação da biblioteca. Não se promete reconhecer duplicatas apenas pelo título.

Iniciada significa ter ao menos um capítulo marcado como lido. Concluída exige capítulos conhecidos em quantidade maior que zero, todos lidos e situação de conclusão em todas as edições vinculadas. Estar em dia com uma publicação em andamento ou sem metadados suficientes não basta. A indicação ainda depende dos metadados locais das fontes.

Os marcos guardam as maiores contagens observadas na biblioteca, não somam cada operação de adicionar/remover. Remover e recolocar cinco obras não vira uma coleção de dez. Não há catálogo permanente de todos os títulos que já passaram pelo aparelho. Dados antigos/restaurados podem cumprir os critérios ao serem carregados; não é necessário começar do zero.

## Atualização e custo

As conquistas reaproveitam as emissões já existentes da biblioteca e os dados obtidos ao abrir Jornada/Aparência ou atualizar o progresso de leitura. O novo cálculo não cria observador de banco, varredura de capítulos ou consulta de rede próprios. Grava somente quando os marcos mudam. Falha na atualização das conquistas não interrompe o carregamento da biblioteca.

## Persistência e backup

Os três marcos adicionais usam uma preferência String comum (`polaris_profile_achievements_v1`), pequena e validada. Ícones liberados continuam no StringSet existente, com os mesmos nomes internos/aliases. Escolhas anteriores são mantidas. A restauração de configurações do app combina os maiores marcos e os ícones conhecidos, preservando conquistas locais diante de um backup mais antigo. Tipos incorretos nos campos cosméticos novos são ignorados; essa combinação não se aplica às preferências privadas de fontes.

O formato de backup Protobuf/SQL, IDs das obras, capítulos, histórico, categorias e arquivos não mudam. Leitores externos podem ignorar ou descartar os cosméticos Polaris. A ida/volta pelo banco/interface de leitores externos continua pendente; isso não estabelece garantia universal entre todos os forks.

## Artes

A [coleção](../design/polaris-grimoires/20261111/README.md) mantém os três, quatro e cinco trevos, com a edição de mana luminosa e a de cinco folhas sombria. A névoa retangular do primeiro grimório foi removida por edição com `image_gen.imagegen`. A primeira geração fica arquivada. As margens adaptativas passam de 25% para 22%, ampliando os livros; os quatro recursos somam **414.354 bytes**. A aceitação de máscaras e ícones temáticos em Android recente permanece pendente.

[Validação desta revisão](../integration/grimoire-achievements/20261112/README.md). Fontes/contas reais, login por WebView, aparelhos ARM, fluxo completo de leitura/downloads e aceite de leitores externos permanecem no backlog. Nenhuma nova versão para celulares foi publicada nesta etapa.
