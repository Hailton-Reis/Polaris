# Filtro de conteúdo +18 · P20261117.4

Revisão de desenvolvimento para a próxima versão. A beta.11 instalada permanece com o APK publicado; nenhum APK ou Release novo nesta revisão.

Em **Configurações → Navegar → Conteúdo adulto → Filtrar conteúdo +18 nas buscas**, o filtro fica ligado por padrão e pode ser desligado. Ele oculta fontes identificadas pelas extensões como adultas e obras com marcações explícitas nos gêneros, classificação ou título. Abrange busca geral, busca de novels/migração, navegação de uma fonte e descoberta automática de alternativas. Alterar a opção reinicia as buscas abertas; a navegação da fonte recebe um novo paginador.

O controle antigo **Exibir fontes adultas** continua independente e exige reinício. Ele determina o carregamento das extensões; não substitui o filtro de obras de fontes mistas. Seu padrão e o carregamento foram preservados para manter disponíveis fontes de leituras já salvas.

Nenhuma obra é apagada da biblioteca. A fonte original de uma leitura existente e escolhas de fonte fixa continuam disponíveis; alternativas adultas não são adotadas automaticamente. Mudar o filtro invalida a validade da descoberta, inclusive quando a lista de fontes mistas não muda. Não há alteração do esquema do banco nem criação de agendamento periódico.

A classificação usa apenas dados já disponíveis e o enriquecimento limitado que existia. Não faz consultas extras para classificar, nem acrescenta modelos ou análise de imagens. Marcas como Hentai, Adult, NSFW, Smut, Pornografia e +18 são reconhecidas sem depender de acento/caixa; marcadores explícitos entre colchetes/parênteses ou no sufixo do título também são reconhecidos. Palavras comuns no título, demografia (Seinen/Josei), romance/orientação e Doujinshi, por si sós, não viram classificação +18.

**Limite:** conteúdo sem marcação, marcação incorreta ou descoberta apenas em detalhes tardios pode aparecer. A navegação de fonte filtra os dados disponíveis ao carregar a página; mudança posterior de metadados de um item pode exigir recarregar. Não é um controle parental garantido.

A pergunta sobre quatro ou cinco alternativas em primeiro plano e uma ou duas em segundo plano fica como proposta. A busca geral já usa cinco tarefas; a descoberta automática continua com duas. Não foi acrescentado trabalho periódico em segundo plano.

As evidências automatizadas ficam em [integration/adult-search-filter/20261117](../integration/adult-search-filter/20261117/README.md). Os provedores são simulados; não equivalem a teste de fontes reais ou de interface no aparelho.
