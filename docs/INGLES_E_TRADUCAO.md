# Inglês e tradução: o que acompanha o aplicativo

## Reconhecer texto

O candidato inclui `com.google.mlkit:text-recognition`, a variante embarcada da biblioteca latina do ML Kit. Por isso, o reconhecimento de texto em inglês nas imagens já acompanha o APK; não depende de baixar primeiro um reconhecedor latino separado.

Reconhecer o que está escrito e traduzir o significado são etapas diferentes.

## Traduzir inglês → português

A integração de tradução usa `com.google.mlkit:translate`. Os recursos necessários são preparados pelo mecanismo oficial `downloadModelIfNeeded` do SDK. Eles não foram empacotados manualmente como arquivos de modelo dentro do APK.

Portanto, uma instalação nova **ainda precisa de uma conexão inicial** para preparar o par. Depois dessa preparação, o ML Kit pode traduzir no aparelho sem conexão, enquanto os recursos necessários estiverem disponíveis.

Não é correto apresentar essa preparação como uma instalação de tradução já completa e totalmente offline no momento de receber o APK.

## O que muda no candidato P20261101.2

A preparação de **inglês → português** passa a ser priorizada automaticamente:

1. No processo principal do app, uma verificação local tenta usar os recursos já existentes, sem solicitar download.
2. Se a verificação funcionar, o par pode ser indicado como pronto mesmo offline; não é necessário aguardar Wi-Fi novamente.
3. Se os recursos faltarem e a preparação automática estiver ativada, o trabalho aguarda conexão sem cobrança e a condição de armazenamento não baixo fornecida pelo Android.
4. O SDK prepara os recursos necessários para o par EN → PT e o app faz uma tradução curta de verificação no aparelho.
5. O estado **Pronto** depende de verificação real no processo atual. Um resultado de trabalho antigo não é usado sozinho como prova de disponibilidade.

O cartão aparece em **Documentos e pesquisa** e nas **Configurações de tradução**. Ele informa preparação, espera, falha ou disponibilidade. O botão **Preparar agora** solicita o uso da conexão atual, inclusive se ela tiver cobrança por dados. Falhas têm tentativas limitadas e podem ser repetidas manualmente.

A preparação automática pode ser desativada. Isso não apaga modelos existentes, não altera a entrada de OCR escolhida, não troca o idioma de saída e não ativa tradução automática por obra.

## Espaço e rede

A referência do Google é de aproximadamente 30 MB por modelo de idioma. O SDK gerencia os recursos exigidos pelo par; não se deve somar artificialmente um novo pacote completo para cada capítulo. O painel de armazenamento lista idiomas baixados e agrega modelos nos dados internos.

A condição de espaço do Android não é uma reserva precisa de bytes para todo o aplicativo. A [revisão crítica de armazenamento](ARMAZENAMENTO.md) continua válida, incluindo o consumo de modelos, cópias e temporários.

A nova capa do repositório é um arquivo da documentação. Ela não é adicionada aos recursos do APK.

## Validação

Os testes de lógica verificam uso de recursos locais sem solicitar download, espera pelo download, execução da verificação, liberação do tradutor, falha, cancelamento e seleção do estado mais recente. Compilação e esses testes não executam o download real do SDK em um celular.

O candidato compilou nas variantes ARM. Os sete testes novos passaram; a comparação completa registrou 471 aprovações e as mesmas 34 falhas da base, sem novas regressões. [Evidência desta revisão](https://github.com/Hailton-Reis/Polaris/blob/3866531931c7705bd238d83467ce40c497343ba5/integration/internal-beta/TEST_RESULTS.json).

Ainda é necessário conferir: instalação limpa, conexão inicial, espera sem rede, preparação manual, desligamento da automação, reaproveitamento após reiniciar e tradução offline após **Pronto**. Modelos removidos ou dados limpos podem exigir uma nova preparação.

## Referências oficiais

- [Reconhecimento de texto no Android: variantes embarcada e dinâmica](https://developers.google.com/ml-kit/vision/text-recognition/v2/android).
- [Tradução no Android: preparar os modelos e traduzir](https://developers.google.com/ml-kit/language/translation/android).
- [Características da tradução no aparelho](https://developers.google.com/ml-kit/language/translation).
- [Contrato de `Translator.translate`: recursos locais e erro quando faltam modelos](https://developers.google.com/android/reference/com/google/mlkit/nl/translate/Translator).
