# OCR e tradução offline: pesquisa e decisões

Consulta em 02/11/2026. Objetivo: melhorar a leitura de manhwa em faixa longa, preservar o funcionamento offline e evitar novos modelos obrigatórios nos aparelhos A12, S8+, S20 FE e A52. Gemini fica fora desta rodada. Nenhuma nova Release foi publicada.

## O que as fontes sustentam

| Fonte | Informação útil | Decisão para o Polaris |
| --- | --- | --- |
| [Google: reconhecimento de texto no Android](https://developers.google.com/ml-kit/vision/text-recognition/v2/android) | O detalhe das letras afeta a precisão; idealmente cada caractere tem pelo menos 16 × 16 pixels. Em geral, caracteres maiores que 24 × 24 não acrescentam precisão. | Preservar os pixels de origem e testar regiões com contexto. Aumentar a janela do emulador não recupera detalhes perdidos no original. |
| [Google: estrutura do Text Recognition v2](https://developers.google.com/ml-kit/vision/text-recognition/v2) | A API fornece blocos, linhas, símbolos e coordenadas. | Usar linhas e coordenadas absolutas para reconciliar a sobreposição entre faixas, sem deduplicar palavras iguais em posições diferentes. |
| [Android: BitmapRegionDecoder](https://developer.android.com/reference/android/graphics/BitmapRegionDecoder) | Permite decodificar regiões sem criar um bitmap com todos os pixels da página. | Experimento por faixas, processadas sequencialmente, sem modelo adicional. |
| [Google: limites da tradução offline](https://developers.google.com/ml-kit/language/translation) | Os modelos são treinados de/para inglês; pares sem inglês usam inglês como intermediário. O Google recomenda avaliar a qualidade por caso de uso. | O resultado em inglês não valida japonês/chinês/coreano → português. Manter casos originais desses idiomas na matriz de teste e preservar glossário e correções por obra. |
| [Tesseract: qualidade da entrada](https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html) | Recorte, bordas, inclinação e binarização influenciam a segmentação; o pré-processamento depende do conteúdo. | Aproveitar os princípios para futuros testes locais; não adicionar Tesseract nem aplicar contraste/binarização em toda arte sem comparação. As recomendações de DPI específicas do Tesseract não são uma exigência do ML Kit. |
| [PaddleOCR: modelos de reconhecimento](https://www.paddleocr.ai/main/en/version3.x/module_usage/text_recognition.html) | A tabela atual lista PP-OCRv6 tiny com 4,4 MB e PP-OCRv5 mobile com 16 MB. Esses valores são do reconhecedor, não de um aplicativo OCR completo. | Candidatos interessantes para comparação futura. Detector, runtime Android, conversão, idiomas, memória e desempenho no A12 ainda precisam ser validados. Não foram baixados ou incorporados novos modelos. |
| [Manga OCR](https://github.com/kha-white/manga-ocr) | Projeto especializado em japonês de mangás, incluindo texto vertical, furigana e texto sobre imagens; depende de Python/PyTorch/Transformers. | Pode servir como referência de comparação no PC para casos japoneses. Não é uma integração pronta para os celulares do beta e não foi adicionado ao APK. |

## Problemas concretos encontrados no código

1. O filtro anterior descartava todo reconhecimento com apenas um caractere. Isso inclui falas como `I` e caracteres CJK completos. O filtro agora elimina apenas texto em branco; os controles posteriores de posicionamento continuam existindo.
2. A classificação anterior de onomatopeias podia remover uma fala curta com letras grandes mesmo dentro de um balão detectado. O novo controle preserva esses balões. A opção de excluir efeitos fora de balões continua funcionando.
3. O caminho padrão do ML Kit entrega a imagem inteira ao reconhecedor. Páginas muito altas merecem comparação por regiões, tanto por precisão quanto por consumo de memória. **Não foi comprovado que esse seja o motivo do defeito relatado.**
4. A análise do fundo usa uma imagem reduzida quando a página tem muitos pixels. Em casos extremos, essa redução pode prejudicar o reconhecimento geométrico dos balões, mesmo com OCR completo. Precisamos medir separadamente OCR, filtros e posicionamento.
5. O renderizador possui um último recurso de encaixe que pode continuar excedendo a área disponível. Não foi alterado para pintar fora do balão ou reduzir indiscriminadamente a fonte. A comparação entre texto salvo e tela continua necessária para investigar o corte.

Também foi verificada a versão do código da biblioteca `vision-common` que já estava no cache: `InputImage.fromFilePath` carrega o bitmap e aplica a orientação EXIF. **Não encontramos evidência de uma redução automática nessa função.** Não atribuímos a perda de linhas a um redimensionamento interno não demonstrado.

## Experimento implementado: ML Kit por faixas

O recurso começa **desligado** e aparece em Tradução → OCR. Nesta revisão é limitado a inglês, JPEG/PNG/WebP, orientação EXIF normal e páginas altas; os demais casos continuam no caminho anterior. Também não atua com DBNet habilitado.

- Regiões sobrepostas de até 2.097.152 pixels, preservando a escala original. Em ARGB isso representa até 8 MiB de pixels por faixa; não é um limite da memória total do aplicativo ou da biblioteca.
- Uma região é reconhecida por vez. Seus pixels são liberados após a tarefa do ML Kit terminar, inclusive se houver cancelamento da fila.
- As linhas recebem o deslocamento vertical da página antes da reconciliação. A preferência é por leituras mais afastadas da borda da faixa.
- A deduplicação considera sobreposição geométrica entre regiões distintas. Repetições legítimas como `Yes` em balões diferentes permanecem.
- Páginas normais mantêm o processamento atual. Há limite de 256 regiões e largura de até 4096 pixels para o experimento.
- Não há um segundo download de imagem, novo modelo, API ou armazenamento permanente das faixas. As imagens são regiões do original local; o arquivo final de tradução mantém o formato existente.

As sobreposições podem aumentar o tempo de processamento. A divisão em linhas também pode afetar a formação de parágrafos; isso precisa ser comparado no capítulo real antes de ativar por padrão. Os testes unitários validam o planejamento e a reconciliação; não medem a precisão do modelo Android.

## Armazenamento e dependências

Foi removida a dependência direta do SDK generativo `google-genai-kotlin`: a busca no código não encontrou chamadas a esse SDK, e o provedor opcional existente usa REST. Isso não altera o modelo ML Kit nem adiciona serviços. Os tamanhos finais dos APKs são registrados nas evidências de compilação; nenhuma redução de memória de execução é presumida a partir da redução do arquivo.

A documentação do Google estima aproximadamente **4 MB por família de escrita e arquitetura** para o OCR embarcado, contra cerca de 260 KB no cliente que baixa modelos pelo Google Play Services. O inglês continua embarcado, como solicitado. Não mudamos os reconhecedores asiáticos para download pelo Google Play nesta rodada: isso muda disponibilidade offline, dependência de serviços Google e o modo de contabilizar armazenamento.

No APK ARM32 da revisão anterior, os arquivos `assets/models/rec/inference.onnx` e `assets/models/det/inference.onnx` somavam aproximadamente **25,2 MiB comprimidos**. Esses pesos do OCR alternativo são uma oportunidade para futura entrega sob demanda; retirá-los agora quebraria esse caminho offline sem uma substituição pronta. Runtime, bibliotecas nativas e formatos de arquivo também precisam entrar nessa conta. O tamanho comprimido no APK não é a memória de execução nem o total instalado.

O custo do arquivo de tradução continua dependendo do número de blocos reconhecidos. Preservar texto antes descartado pode aumentar um pouco esse JSON. Glossário, correções, originais, modelos e cache continuam sendo categorias distintas; não foi criado um cache permanente de imagens processadas.

## Critério para escolher o próximo passo

Para o mesmo trecho e a mesma imagem, comparar modo padrão e modo por faixas: linhas ausentes, repetições, texto preservado, tradução completa, encaixe visual, tempo e memória no aparelho. Quando houver transcrição esperada, medir também erros de caracteres. Os casos japoneses devem incluir texto vertical e furigana; chinês simplificado e tradicional e coreano precisam de casos próprios.

Sem essa comparação, não ativar o experimento por padrão, não trocar o OCR e não prometer qualidade equivalente à tradução de uma scan. O relatório do CMD foi preparado para obter exatamente essas evidências com um ZIP de um trecho escolhido.


### Medição do candidato compilado

Na comparação beta.5 → beta.6, o APK ARM32 passou de **155.998.826 para 153.015.944 bytes**; o ARM64, de **195.796.649 para 192.813.767 bytes**. A redução é de **2.982.882 bytes**, aproximadamente 3 MB, em cada arquitetura, considerando a limpeza de dependências junto às demais alterações desta revisão. A compilação e o comparador de regressões passaram; o tamanho instalado e a memória de execução no celular ainda não foram medidos.
