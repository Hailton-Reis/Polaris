# Correções do teste no Galaxy A

A beta.12 de teste (código 113, revisão P20261122.2) reúne as correções abaixo e as melhorias de abertura e busca com centenas de fontes. O APK universal inclui ARM32 e ARM64 e pode atualizar a beta.11 pública mantendo o mesmo aplicativo e certificado.

| Relato | Correção ou verificação |
| --- | --- |
| Página baixada e traduzida aparece e some | O leitor conserva o visualizador quando a atualização mexe só na capa, capítulos ou outros dados da obra. A abertura de um capítulo local usa o arquivo já baixado e adia a busca remota de capítulos vizinhos. Cancelamentos de renderização deixam de ser tratados como erro de imagem. |
| Categorias e marcações do backup | Exportação e restauração de **Categorias** incluem os nomes e os vínculos com as obras. **Capítulos** preserva progresso, leitura e marcadores. **Histórico** é uma opção separada. O teste cria um arquivo, restaura em outro SQLite com categorias preexistentes e valida as quatro categorias, uma obra em duas categorias e as marcações de capítulo. Cada backup antigo só contém o que foi salvo na época. |
| Extensões antigas do backup | Em **Extensões → ⋮ → Recuperar fontes da biblioteca**, o Polaris testa a fonte original primeiro. Se capítulos ou páginas falharem, busca alternativas compatíveis. A mesma obra favorita conserva a identidade e pode reaproveitar capítulos e capa de outra fonte. A política preserva capa personalizada. |
| Edições repetidas | A biblioteca pode mostrar uma obra em um cartão quando autoria, título ou identidade de catálogo e numeração comprovam a equivalência. Edições recuperadas das fontes antigas entram nessa verificação. As edições nativas, categorias, marcadores, histórico e arquivos permanecem acessíveis. Obras ambíguas continuam visíveis separadamente. |
| Preparar e gerir extensões | **Preparar fontes** está visível na aba **Extensões**. A instalação privada verifica pacote e versão selecionados e confirma o carregamento antes de informar sucesso. Remover uma extensão atualiza o catálogo sem reenviar eventos de exclusão. A aba informa falhas de instalação. |
| Extensões obsoletas | Quando a extensão volta ao catálogo, a marca de obsoleta é retirada. Ausência no repositório pode ocorrer por falha de rede ou catálogo parcial. A remoção fica explícita na aba Extensões para preservar fontes e arquivos que ainda funcionam. |

Instale o APK por cima da beta.11 para manter os dados. No A12, confira a abertura do app com as fontes já instaladas. Abra um capítulo traduzido e baixado em modo avião e com Wi-Fi. A página deve permanecer visível sem precisar rolar. Em seguida, verifique o preparo, a instalação e a atualização privada com versões conhecidas e recupere uma obra de uma fonte desativada. Compare categorias e marcações após exportar e restaurar um backup de teste em outro perfil.

A compilação Android e os 1.124 testes automatizados passaram. A suíte inclui nove casos novos e mantém os 1.115 casos da revisão anterior.

O APK de teste foi conferido contra a beta.11 pública. A assinatura confere, o código de versão aumentou de 112 para 113 e o alinhamento ZIP de 16 KiB passou. A confirmação nos Galaxy A segue pendente. [Validação e dados do APK no PR #13](https://github.com/Hailton-Reis/Polaris/pull/13).
