# Busca por obra — P20261109.1

Revisão de desenvolvimento da beta.11/código 112, posterior a 5a0a8bf. Não altera a beta.10 publicada, main ou seus assets.

## Comportamento

A busca global de quadrinhos inicia em **Todas** as fontes habilitadas. Os filtros por fontes fixadas, idioma habilitado e extensão continuam disponíveis. O resultado padrão apresenta uma grade por obra reconhecida; o botão **Fontes** retorna à visualização por provedor. A pesquisa de migração e a pesquisa de novels mantêm seus fluxos específicos.

O agrupamento exige títulos normalizados/aliases corroborados e autoria compatível. Aliases de português/inglês/coreano vêm dos metadados públicos do catálogo, sem lista de traduções inventadas nem comparação de capa. Homônimos, sequências, qualificadores de novel/parte e identidades conflitantes permanecem separados. Todos os membros precisam concordar entre si; um item com dois autores não pode unir duas obras incompatíveis por transitividade. URLs distintas da mesma fonte precisam de corroboração de catálogo para serem reunidas.

Quando os resultados de uma fonte não incluem autoria e há possibilidade de duplicação, o coordenador consulta somente metadados da obra. Os campos internos Polaris do memo não são enviados ao provedor nessa consulta. A URL/título originalmente encontrados permanecem nativos; metadados devolvidos para outro título não emprestam autoria ao resultado. A confirmação não usa downloads de capítulos. Páginas reais e numeração ainda são conferidas pelo catálogo de fontes ao abrir/atualizar a obra.

Uma consulta ao catálogo pode recuperar aliases em fontes que retornaram vazio. Isso não expande fontes desabilitadas, não repete fontes que falharam/autenticaram com erro, não instala extensões e não percorre páginas de resultados. Ausência de confirmação deixa entradas separadas.

## Biblioteca e autonomia

Uma entrada favorita compatível já existente tem prioridade sobre criar outra entrada pelo resultado unificado, inclusive após restauração. Seu ID, URL, título, flags e notas continuam sendo os originais. Uma fonte fixada pela pessoa continua sendo respeitada. Para obras novas, português brasileiro/português precedem inglês na escolha da entrada; a seleção de capítulos segue a verificação existente de fonte e leitura.

Ao abrir, candidatos reconhecidos são ligados por sourceId/URL em um transform atômico do memo atual. Anotações/glossário, outras chaves, a saúde já registrada e a fonte fixada não são substituídos por um snapshot antigo da busca. Não há IDs locais novos no formato portável dessas ligações. A fonte ainda é validada novamente antes de compor capítulos.

**Esta etapa não consolida entradas antigas que já aparecem duplicadas dentro da biblioteca.** Não desmarca favoritos, move arquivos, muda categorias, soma capítulos físicos ou reescreve leitura/histórico. O reaproveitamento se dá ao abrir pela busca unificada. A visualização explícita por fonte permite abrir uma edição individual. Backups conservam os registros nativos e o mesmo esquema; ida/volta por banco/interface de leitores externos permanece pendente.

Fontes de novels e documentos locais não são reutilizadas como favoritos de quadrinhos. Uma fonte desaparecida cujo tipo de conteúdo não pode ser comprovado permanece separada, salvo identidade de quadrinhos já registrada no cache do Polaris. Um backup que só tenha título, sem autoria/identidade suficiente, não recebe associação arriscada por este fluxo. A recuperação já implementada ao abrir a biblioteca segue independente desta busca.

## Limites de trabalho

- Até 100 resultados iniciais por fonte na busca global de quadrinhos.
- Até uma consulta de identidade, com limite de 5 s.
- Recuperação de aliases em até quatro fontes com resultado vazio, até dois aliases e uma página por alias, com 5 s por requisição.
- Até 16 consultas adicionais de metadados de obras, com 5 s cada; no máximo duas requisições de enriquecimento simultâneas. Cancelamento é propagado.
- Até 16 candidatos novos ligados ao abrir; metadados previamente registrados permanecem intactos. Não há modelo ou dependência nova.
- A consulta de favoritas lê apenas metadados, sem calcular contagens de capítulos. Índices locais de títulos/aliases e assinaturas preparadas evitam comparar repetidamente cada resultado com todos os títulos e normalizar os mesmos dados em cada par.

Falhas de rede/metadados mantêm os resultados nativos utilizáveis. A barra de enriquecimento continua visível enquanto a segunda etapa trabalha. Fontes com erro são indicadas, com detalhes na visualização Fontes. Uma nova tentativa explícita pesquisa novamente; alternar filtros pode reaproveitar sucessos. Atualizações concorrentes de fontes não descartam umas às outras e o pool da busca é encerrado com o ViewModel.

## Próxima etapa da biblioteca

A consolidação de duplicatas restauradas precisa de uma identidade durável e uma operação que preserve em conjunto categorias, histórico, leituras/marcadores, fontes fixadas, glossários e caminhos de downloads já existentes. Não ocultar uma edição enquanto seus dados não estiverem acessíveis pela entrada representativa. Não copiar índices de página entre paginações diferentes. A transação também precisa de recuperação em falha e testes de ida/volta do backup; esconder itens na interface não encerra esse trabalho.

## Reprodutibilidade do código

A exportação do overlay usa o HEAD composto fixado como base, incluindo exclusões já indexadas. A comparação apenas entre index e árvore de trabalho podia omitir essas exclusões. Os controles de aplicação em checkout limpo agora também conferem a presença da busca nova e a ausência de componentes/recursos visuais legados removidos. Essa correção aproxima o patch distribuído dos fontes efetivamente compilados, sem reconstruir ou alterar a beta.10 publicada.

## Validação

Resultados, comparações, limites e captura sintética ficam nas [evidências desta revisão](../integration/unified-search/20261109/README.md). Testes com provedores sintéticos não aprovam todas as extensões, catálogos ou aparelhos ARM. Não há login em conta real ou consulta a capítulo comercial nesta rodada.
