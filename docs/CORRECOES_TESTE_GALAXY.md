# Correções do teste no Galaxy A

Relatos cobertos pela revisão P20261122.2. O pacote de teste nos aparelhos precisa incluir também a revisão de abertura com centenas de fontes.

| Relato | Correção ou verificação |
| --- | --- |
| Página baixada e traduzida aparece e some | O leitor conserva o visualizador quando a atualização mexe só na capa, capítulos ou outros dados da obra. A abertura de um capítulo local usa o arquivo já baixado e adia a busca remota de capítulos vizinhos. Cancelamentos de renderização deixam de ser tratados como erro de imagem. |
| Categorias e marcações do backup | Exportação e restauração de **Categorias** incluem os nomes e os vínculos com as obras. **Capítulos** preserva progresso, leitura e marcadores. **Histórico** é uma opção separada. O teste cria um arquivo, restaura em outro SQLite com categorias preexistentes e valida as quatro categorias, uma obra em duas categorias e as marcações de capítulo. Cada backup antigo só contém o que foi salvo na época. |
| Extensões antigas do backup | Em **Extensões → ⋮ → Recuperar fontes da biblioteca**, o Polaris testa a fonte original primeiro. Se capítulos ou páginas falharem, busca alternativas compatíveis. A mesma obra favorita conserva a identidade e pode reaproveitar capítulos e capa de outra fonte. A política preserva capa personalizada. |
| Edições repetidas | A biblioteca pode mostrar uma obra em um cartão quando autoria, título ou identidade de catálogo e numeração comprovam a equivalência. Edições recuperadas das fontes antigas entram nessa verificação. As edições nativas, categorias, marcadores, histórico e arquivos permanecem acessíveis. Obras ambíguas continuam visíveis separadamente. |
| Preparar e gerir extensões | **Preparar fontes** está visível na aba **Extensões**. A instalação privada verifica pacote e versão selecionados e confirma o carregamento antes de informar sucesso. Remover uma extensão atualiza o catálogo sem reenviar eventos de exclusão. A aba informa falhas de instalação. |
| Extensões obsoletas | Quando a extensão volta ao catálogo, a marca de obsoleta é retirada. Ausência no repositório pode ocorrer por falha de rede ou catálogo parcial. A remoção fica explícita na aba Extensões para preservar fontes e arquivos que ainda funcionam. |

A validação em aparelho deve instalar o próximo pacote por cima da beta, manter os dados existentes e abrir um capítulo já traduzido em modo avião e com Wi-Fi. A página deve permanecer visível sem precisar rolar. Em seguida, verificar preparo, instalação e atualização privada com versões conhecidas e recuperar uma obra de uma fonte desativada. Comparar categorias e marcações após exportar e restaurar um backup de teste em outro perfil.

A compilação Android e os 1.124 testes automatizados passaram. A suíte inclui nove casos novos e mantém os 1.115 casos da revisão anterior. [Resultado da validação](../integration/weekend-bugfixes/20261122/RESULT.json).
