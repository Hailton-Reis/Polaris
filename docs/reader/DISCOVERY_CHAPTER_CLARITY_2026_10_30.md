# Descoberta de repositórios e versões de capítulos — 30/10/2026

O usuário pediu avanços independentes enquanto trabalha e deixou os testes no emulador Windows para depois. As capturas enviadas continuam sendo da versão antiga. O APK candidato compila, mas ainda não recebeu aceite visual no dispositivo.

## O que foi implementado

- **Descobrir repositórios** em Configurações → Explorar, no menu de Extensões e na barra da tela Repositórios.
- Catálogo inicial com **Project Nox** e **Keiyoushi**, pesquisável por nome, idioma e mantenedor, aceitando acentos e vários termos. A pesquisa é local sobre essas entradas; não procura todos os repositórios da internet.
- **Adicionar repositório** cadastra diretamente pela infraestrutura existente. Não há uma nova confirmação do Polaris. A abertura da tela não cadastra repositórios nem instala extensões.
- Estados de carregamento, adição, já adicionado e falha. Cliques repetidos não iniciam vários cadastros simultâneos. URLs antigas equivalentes são reconhecidas para evitar duplicação das entradas do catálogo.
- Avisos permanentes sobre código de terceiros, limites das assinaturas, sobreposição entre repositórios e termos de uso. As verificações normais do Android e das assinaturas de extensões continuam valendo.
- Títulos de capítulos com até duas linhas; **Grupo/versão** em uma linha própria, com espaço para nomes maiores; identificação da fonte com até duas linhas.
- Ações da obra em duas colunas em telas estreitas ou com fonte ampliada, com menos espaço desperdiçado dentro dos botões. Em largura suficiente, continuam em quatro colunas. Os rótulos têm até duas linhas.
- Contagem de **capítulos/versões**, indicação do filtro no cabeçalho e explicação do filtro de grupos já existente. A busca em outras fontes informa que mantém resultados separados por fonte.

Os rótulos `official`, `unofficial`, `Side Story` e os nomes de grupos vêm da fonte. Números repetidos podem representar edições e extras diferentes. O código de busca examinado abre resultados por fonte; isso não demonstra que todos os dados de uma extensão estejam corretos. Nenhuma entrada foi removida, unificada, renumerada ou escondida automaticamente.

## Verificação técnica

Os dois índices públicos modernos responderam HTTP 200 e tiveram nome/chave de assinatura declarada inspecionados em 30/10/2026. O índice legado da Keiyoushi apontou para a URL moderna equivalente. Os hashes e metadados estão em `integration/reader-translation-ux/REPOSITORY_INDEX_CHECKS_2026_10_30.json`. Isso verifica disponibilidade e metadados naquele momento; não equivale a auditoria de cada extensão ou teste da interface Android.

O candidato inclui testes de pesquisa, aliases, cliques repetidos, falha de cadastro, falha de leitura e nova tentativa. Quando a atualização de extensões lança erro depois do cadastro, o cadastro bem-sucedido permanece. A infraestrutura existente também pode tratar falhas de listagem com seu próprio aviso; não há garantia de que toda falha por repositório seja exposta ao novo controlador.

O resultado completo de compilação, assinatura e comparação com os testes da referência está em `integration/reader-translation-ux/TEST_RESULTS.json`. As falhas antigas são registradas separadamente de regressões. Nenhuma alteração de esquema, migration15 ou habilitação de backupv2 foi feita. O PR de engenharia continua em rascunho.

## Quando o usuário voltar

Atualizar pelo mesmo `00_POLARIS_TUDO_EM_UM.cmd`: opção **4** para gerar a versão atual e **9** para instalar/abrir, preservando a chave de assinatura local. Não substituir o APK local pelo APK de engenharia assinado na nuvem.

1. Abrir Descobrir repositórios; pesquisar por `português`, pelo nome ou pelo mantenedor; cadastrar somente o repositório desejado e conferir sua presença na tela Repositórios.
2. Voltar a Extensões e conferir a listagem. Instalar apenas se precisar de outra fonte para seu próprio uso.
3. Reabrir Solo Leveling na mesma fonte; conferir os botões da obra, os grupos/versões e usar o filtro existente para escolher uma edição. Conferir também a orientação horizontal ou fonte ampliada se conveniente. Não é necessário testar duas fontes para avaliar essas mudanças de interface.
4. Reabrir as páginas já traduzidas de Guilty Library; comparar posição do texto e da limpeza em tamanho normal e com zoom. A correção de enquadramento não exige retraduzir somente para avaliar a renderização.
5. Baixar um capítulo novo de uma fonte identificada como inglesa e observar a tradução automática. A identificação atual usa o idioma declarado pela fonte; não reconhece o idioma do conteúdo de cada capítulo por OCR. Uma opção explícita por obra tem prioridade sobre o padrão global.

O teste com duas fontes permanece pendente apenas para o aceite específico de múltiplas fontes. Não é solicitado ao usuário durante sua ausência.
