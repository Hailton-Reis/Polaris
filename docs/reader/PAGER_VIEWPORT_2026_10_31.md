# Tradução no leitor paginado — 31/10/2026

O usuário identificou uma diferença entre modos de leitura: relatou posicionamento correto em tira longa e deslocado no paginado, enviando capturas dos dois. Ele acredita ter atualizado pelas opções 4 e 9, mas a revisão exata instalada ainda não foi confirmada. O hash de base mostrado anteriormente em Sobre não distingue as revisões do overlay Polaris.

## Correção candidata

O componente de imagem usado no paginado (SSIV, revisão `66e0db195d`) aplica ajustes pendentes de escala e centralização no próprio desenho. O seu `preDraw()` pode modificar a transformação sem emitir os avisos de escala/centro que o overlay escutava. Isso deixa uma possibilidade concreta de a tradução usar uma posição anterior à imagem, particularmente na abertura ou após uma mudança de tamanho. A inspeção do código confirma essa possibilidade; não comprova sozinha a causa de todos os deslocamentos das capturas.

O paginado agora observa a transformação depois de cada desenho da imagem, quando o SSIV já aplicou os ajustes pendentes. Escala e origem são publicadas em um único estado imutável. Não há desenho da tradução antes de existir geometria válida. O deslocamento inclui as posições relativas da imagem e do overlay dentro do contêiner; a calibração entre dimensões de tradução e de imagem continua valendo. O contêiner da tradução ocupa a área do leitor, aplica o deslocamento em pixels e recorta o conteúdo nos limites da área visível.

Também foi corrigida a reexibição indevida do overlay ao carregar a imagem quando a preferência de mostrar traduções está desligada, e os callbacks passam a lidar com visualizações animadas sem conversão forçada para SSIV.

O caminho de tira longa, os dados de OCR/tradução salvos, o ajuste tipográfico, o provedor e a geometria dos balões permanecem como estavam. Não é necessário retraduzir para testar esta renderização. Não há alteração de esquema, migration15 ou habilitação de backupv2.

## Identificação da versão

Sobre passa a começar por **Polaris P20261031.1**, seguido da versão da base e da data/hora de compilação já existente. Esse identificador marca esta revisão do overlay; novas revisões de código devem atualizar a constante `POLARIS_READER_REVISION` em AboutScreen. Recompilar o mesmo código mantém o identificador da revisão e atualiza a data de compilação no build de depuração. Não é um incremento automático do versionCode Android.

## Verificação e limites

Quatro testes de geometria verificam a margem superior de uma página centralizada, metadados de tradução em resolução menor, zoom/deslocamento com coordenadas negativas e rejeição de geometria incompleta/inválida. Eles não simulam a renderização do Android nem certificam visualmente o resultado. Os resultados de compilação, assinatura e comparação completa com a referência estão em `integration/reader-translation-ux/TEST_RESULTS.json`.

A aceitação visual do novo paginado permanece pendente. O relato sobre tira longa é evidência fornecida pelo usuário e não certifica todas as páginas nem identifica com certeza o APK instalado. O teste específico de múltiplas fontes permanece separado.

## Teste após a próxima atualização

1. Usar o mesmo CMD, opção 4 e depois 9, preservando a assinatura local e os dados do AVD. Confirmar **Polaris P20261031.1** em Sobre.
2. Reabrir a mesma página 4 do capítulo 1.3 de Guilty Library no modo paginado, inicialmente sem tocar no zoom. Conferir a limpeza e o texto dentro dos balões.
3. Ampliar, deslocar e voltar ao ajuste inicial. Conferir também a abertura de outra página e, se possível, uma mudança de orientação da tela.
4. Comparar a mesma página em tira longa. Se persistir diferença, registrar os dois modos na mesma página, a identificação em Sobre e a configuração de escala/corte de bordas do leitor.
