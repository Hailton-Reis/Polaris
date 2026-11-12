# OCR por faixas compartilhado — P20261102.4

Candidato interno **0.1.0-beta.7 / versionCode 108**, Android 8+, ARM32/ARMv7 e ARM64. A release pública beta.3 não é substituída por esta revisão.

O [benchmark de 02/11/2026](../integration/ocr-benchmark/20261102/report/RESULTADOS.md) mostrou que preservar escala em regiões sobrepostas recuperou as 38 linhas de um controle sintético muito alto. Esta revisão aplica o mesmo caminho regional ao Paddle Small já embarcado, além do ML Kit. O Tiny não foi integrado e não há novos pesos ou dependências de inferência.

## Comportamento

Em **Tradução → OCR → OCR por faixas em páginas longas (experimental)**, a opção vale para ML Kit e PaddleOCR em inglês. Ela continua desligada por padrão. A chave antiga `mlkit_long_page_strips` é preservada para manter escolhas feitas na beta.6. Com DBNet experimental ligado, o caminho por faixas não é usado.

`OcrStripImage` centraliza leitura de dimensões, formato, orientação e decodificação regional. JPEG/PNG/WebP altos com largura até 4.096 px usam até 256 regiões. Cada região tem até 2.048 px de altura e 2.097.152 pixels, com sobreposição adaptada à largura. Cada bitmap é descartado antes da próxima região; o decodificador é fechado também em falhas ou cancelamento. A tarefa ML Kit pendente termina antes de liberar seus pixels. O Paddle mantém o bloqueio do motor durante a inferência e passa a inicializar os modelos antes de alocar o bitmap de entrada, evitando retê-lo quando a inicialização falha.

**8 MiB é o orçamento de pixels ARGB de cada faixa, não o limite de RAM do app ou do motor.** Modelos, OpenCV/ONNX, buffers do SDK, metadados de linhas e os dados comprimidos que o decodificador mantém consomem memória adicional. A memória física em ARM continua pendente de medição. Como referência matemática, um bitmap ARGB de 720 × 20.000 ocupa aproximadamente 54,9 MiB em pixels; uma faixa de 720 × 2.048 ocupa 5,6 MiB. Esses valores não são uma medição do pico de RAM do processo.

A posição vertical de cada resultado Paddle é convertida para as coordenadas da página completa antes da reconciliação. `OcrStripPlan` preserva cobertura, prefere leituras longe da borda e remove repetições apenas entre regiões diferentes e com sobreposição geométrica suficiente. Falas iguais em posições diferentes permanecem.

Páginas comuns, formatos sem suporte regional e orientação EXIF rotacionada continuam no caminho anterior. Dimensões patológicas que exigem mais de 256 regiões falham antes da decodificação dos pixels. Não há alteração nos idiomas aceitos pelo Paddle: ele permanece restrito a inglês no app.

## Verificação

O novo teste do reconciliador Kotlin recebe saídas brutas do benchmark para ML Kit, Small e Tiny e confere as 38 linhas esperadas, sem repetição. A amostra Tiny valida somente a reconciliação de coordenadas; não integra ou valida esse modelo no Android. Os dados são controles sintéticos autorais e os testes não executam novamente o OCR.

Dois testes instrumentados verificam o decodificador Android: posições e cores regionais, orçamento de pixels, fechamento de streams/decoder em falha e recusa de coordenadas EXIF rotacionadas. A execução e os resultados da compilação são registrados no relatório da revisão; compilação isolada não é prova de execução desses testes.

A conferência visual com capítulos reais, a qualidade da tradução, atualização com preservação da biblioteca e a matriz de desempenho em aparelhos físicos continuam pendentes. Para comparar motores/modos, use o mesmo original e glossário e refaça o OCR pela tradução do capítulo; arquivos já traduzidos não são reprocessados só por mudar a configuração.


## Resultado desta revisão

A montagem dos APKs ARM32 e ARM64 terminou. O comparador registra **547 testes JVM, 513 aprovações e as mesmas 34 falhas preexistentes**, sem novas falhas ou testes ignorados. Os 12 testes de faixas passaram, incluindo os três conjuntos medidos. Os 4 testes de aplicação do overlay, 33 contratos estáticos do instalador, 6 testes do empacotador, 16 do comparador e 7 de integridade da compilação passaram.

Os 2 testes Android do decodificador passaram no AOSP API26 x86_64. O emulador mínimo não possui provedor WebView; a inicialização normal do leitor falhou antes dos testes por esse motivo. Para testar apenas os componentes, foi usado `OcrComponentTestRunner` com `android.app.Application`. O runner normal e a inicialização do APK do leitor foram preservados. Essa execução não valida a abertura completa do app, a UI ou o fluxo de capítulo. O helper optativo `scripts/ocr/ocr_component_tests.init.gradle` permite repetir o mesmo escopo; ele não serve para testes que dependem da Application/DI do Polaris.

Cada APK cresceu **18.988 bytes** em relação à beta.6: ARM32 **153.034.932 bytes**, ARM64 **192.832.755 bytes**. Os assets e bibliotecas nativas comparados são idênticos aos da beta.6. A assinatura confere com a beta.3 já distribuída. Os binários do leitor não foram alterados para usar a Application isolada dos testes.

O [relatório JSON](../integration/document-reader/TEST_RESULTS.json) registra os escopos e os resultados. A entrega permanece privada no Drive; a release pública não foi substituída.


O teste adicional `PaddleOcrV6SmokeTest#officialSmallModelsInitializeDetectAndRecognize` não concluiu dentro do orçamento de 600 segundos no emulador x86_64 sem aceleração. Não foi contado como acerto, falha de reconhecimento ou medição de desempenho ARM. A inferência pelo SDK Android e o caminho regional completo do Paddle continuam pendentes de validação em hardware adequado. O benchmark ONNX CPU/Linux anterior e os testes Kotlin de reconciliação mantêm seus escopos próprios.

Para repetir apenas os componentes do decodificador em uma imagem AOSP mínima, compile o AndroidTest com `-I scripts/ocr/ocr_component_tests.init.gradle` e selecione `eu.kanade.translation.recognizer.OcrStripImageTest` usando o runner `eu.kanade.translation.recognizer.OcrComponentTestRunner`. Testes completos do app precisam da Application normal e de um sistema com WebView. O helper não muda o leitor distribuído.
