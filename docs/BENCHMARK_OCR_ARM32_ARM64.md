# Comparação de OCR e compatibilidade ARM32/ARM64

A meta do Polaris é atender aparelhos de diferentes marcas e capacidades com **Android 8.0 ou superior**, em **ARM32/ARMv7 (`armeabi-v7a`) e ARM64 (`arm64-v8a`)**. Os dois APKs da beta.7 foram compilados, verificados e assinados com o mesmo certificado. A arquitetura do Android instalado, além da versão do sistema, define qual pacote pode ser instalado. Compilar para uma ABI não comprova funcionamento em todo aparelho: a aceitação em dispositivos físicos continua pendente.

O A12 é um possível aparelho de teste, não o requisito que define o produto. A matriz deve cobrir aparelhos de entrada, intermediários, antigos e recentes, com diferentes quantidades de RAM e versões do Android, incluindo as duas ABIs. Nenhuma dessas categorias é marcada como aprovada sem execução real.

## O que estamos comparando

| Componente | Função | Situação |
| --- | --- | --- |
| ML Kit Text Recognition | Lê letras das imagens: OCR | Atual padrão do Polaris |
| ML Kit Translation | Traduz o texto reconhecido | Tradutor offline mantido na comparação |
| OCR por faixas | ML Kit ou Paddle com entrada dividida em regiões sobrepostas | Experimental, desligado por padrão, inglês (beta.7) |
| PaddleOCR existente no app | Outra família de reconhecimento de texto | Caminho atual limitado a inglês; não é o Tiny pesquisado |
| PP-OCRv6 tiny pesquisado | Outro modelo da família PaddleOCR | Ainda não integrado nem validado no Android |

O Tiny não é uma versão do ML Kit nem substitui o tradutor. Para comparar a experiência de OCR, manter o tradutor ML Kit, o idioma de destino e o glossário constantes e trocar apenas o caminho de reconhecimento. O mesmo original deve ser usado em todos os testes.

## Protocolo do benchmark

1. Separar uma amostra com transcrição esperada: diálogo em balões, texto fora de balões, frases com última linha perto da borda, letras grandes, repetição legítima de palavras e páginas longas. Manter casos distintos por idioma e orientação; o controle sintético incluído não substitui capítulos reais.
2. Comparar primeiro o texto reconhecido e preservado: palavras erradas, omissões, linhas incompletas e duplicações. Depois avaliar a tradução e o encaixe na tela separadamente.
3. Medir tempo, memória e tamanho dos recursos por aparelho/ABI. Separar preparação/download inicial, primeira execução com modelos prontos e execuções seguintes. O custo de um modelo isolado não é o custo de todo o sistema.
4. Repetir os mesmos casos em ARM32 e ARM64, preservando os originais e congelando as configurações e o glossário. Remover apenas o arquivo de tradução que precisa de uma nova leitura da imagem; retraduzir uma frase usa o OCR já salvo.
5. Registrar resultados por idioma, tipo de página e categoria de aparelho. Pode haver um melhor padrão e uma alternativa útil; não presumir um vencedor universal.

O coletor atual exporta texto salvo **após os filtros**. Seus resultados medem o caminho completo de reconhecimento e processamento, não a precisão isolada do motor. Não chamar uma retenção pelo filtro de posicionamento de erro do OCR se o texto estiver presente no registro. Para um benchmark isolado do motor, será necessária uma coleta de resultados brutos antes dos filtros, com o mesmo pré-processamento.

## Ensaio controlado já executado

O [ensaio de 02/11/2026](../integration/ocr-benchmark/20261102/report/RESULTADOS.md) executou a API ML Kit real em Android 8 x86_64 e os modelos oficiais Small/Tiny em ONNX Runtime CPU/Linux. Nos 27 recortes de inglês, o pipeline Small acertou 26 textos completos, Tiny 22 e ML Kit 19. Em uma página sintética de 20.000 px, os três recuperaram as 38 linhas ao usar faixas; a página inteira perdeu quase todo ou todo o texto.

O Tiny avaliado não cobre japonês/coreano e não foi incorporado ao app. As imagens, as saídas brutas e o código estão no pacote. Esses resultados avaliam controles de qualidade, não velocidade/memória ARM ou o capítulo real com falha. Não é necessário que o usuário execute esse ensaio já concluído. A comparação completa em aparelhos continua dependendo de adaptação e validação por ABI.

## Primeiro teste do usuário

Agora basta uma verificação curta da beta.7: instalar o pacote da ABI correspondente como atualização, confirmar a versão em Sobre e abrir o mesmo capítulo em que houve falhas. Começar com **ML Kit e OCR por faixas desligado**, observando leitura, alinhamento e falas curtas. Não é necessário configurar Gemini ou API nem executar todo o benchmark agora.

O teste comparativo completo **em aparelhos Android ARM** entre ML Kit e o Tiny só começa depois que o Tiny estiver adaptado e validado para ambas as ABIs. Se compararmos o Paddle já existente antes disso, os resultados devem identificá-lo como o modelo existente, sem atribuí-los ao Tiny.
