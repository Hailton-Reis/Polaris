# Limpeza de recortes OCR — P20261117.2

17/11/2026, America/Fortaleza. Desenvolvimento para a próxima versão; sem novo APK ou Release. A beta.11 pública permanece P20261116.1/código 112.

## Problema e correção

O motor Paddle preparava os recortes de um lote antes de entrar no `try/finally` responsável por liberá-los. Se um recorte seguinte falhasse, os anteriores ficavam sem chamada explícita de `Mat.release()`. Uma falha ao consultar dimensões também deixava sem liberação o recorte recém-retornado. O fechamento da imagem original já existia, mas não abrangia esses objetos separados. Isso é um problema de liberação determinística; não foi medido um vazamento permanente ou OOM no aparelho.

`OCREngine` passa a preparar o lote dentro da proteção e registrar cada recorte retornado antes de consultar suas dimensões. Uma lista de recursos pertence ao lote; outra continua contendo somente imagens válidas para reconhecimento. O fechamento do lote libera todos os recortes recebidos em sucesso ou falha. Vazios não entram na inferência e são liberados no fechamento do mesmo lote. Lotes anteriores permanecem fechados; o erro original continua propagado nos casos testados.

A alteração não cria cópias de imagens, modelos ou tarefas. Ordenação, agrupamento por proporção, geometria, limite de confiança e remapeamento dos resultados permanecem com a lógica anterior. A modificação local do SDK está documentada em `ppocr-sdk/MODELS.md`, preservando licença e formatação de origem. O comentário do formatador agora aponta essa documentação, em vez de afirmar identidade byte a byte do SDK modificado.

## Prova e limites

Dois casos reproduziram o comportamento anterior com `OCREngine.run(bitmap)` real: falha num recorte posterior e falha ao consultar dimensões. Ambos chegaram à asserção de liberação ausente, depois de conferir identidade do erro, fechamento da página e ausência de reconhecimento. O arquivo de produção estava idêntico ao checkpoint anterior durante essa reprodução, sem parâmetro de roteamento ou implementação alternativa.

O teste executa a construção/orquestração real do motor, ordenação, agrupamento, índices, filtro e limpeza. Carregamento de modelos, detecção, corte, reconhecimento e objetos `Mat` são simulados nas fronteiras. Assim, comprova chamadas de liberação, sem executar JNI, inferência ou alocação nativa. A dependência OpenCV foi acrescentada somente ao classpath de testes do app, pois a dependência interna do SDK não expunha esses tipos na compilação do teste; ela já faz parte do runtime de produção.

Uma primeira compilação do teste identificou essa ausência no classpath e foi corrigida antes da reprodução válida. Não foi contada como falha de comportamento. As duas falhas válidas e a configuração inicial ficam registradas separadamente.

Após a correção, os sete casos novos passaram: as duas falhas anteriores, erro no reconhecedor, sucesso com lotes por proporção e saída em ordem de leitura, vazios/baixa confiança sem trocar a caixa do texto aceito, falha em lote posterior e página sem detecções. Quinze controles focados aprovados, incluindo os existentes de agrupamento, inicialização e mapeamento.

Validação final `BUILD SUCCESSFUL` em 2min34s: **939 testes do app beta executados/aprovados**, mais **85 de domain release anteriormente aprovados e UP-TO-DATE**, total de 1.024 relatórios sem falhas/skips ou casos anteriores ausentes contra os 1.017 da base P20261117.1. Quatro testes de overlay, 27 de empacotamento e 21 do comparador aprovados. Não houve nova instrumentação, APK ou execução em aparelho.

O escopo cobre recortes **devolvidos ao motor**. Não estabelece a limpeza de temporários internos de uma operação de corte que falha antes de retornar, nem altera o comportamento quando a própria liberação nativa falha. Temporários de corte/conversão ainda merecem auditoria. Não houve medição de RAM/pico, qualidade de OCR ou execução em aparelhos. As aceitações JNI/ARM32/ARM64/Android de 16 KiB da [integração OpenCV](OPENCV_P20261117_1.md) continuam pendentes.

Sandbox e conta Google/nuvem seguem adiadas. [Evidências filtradas](../integration/ocr-crop-ownership/20261117/README.md). Antes de distribuir, aumentar versão/código acima de beta.11/112 e validar o novo pacote.
