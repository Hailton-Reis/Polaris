# Benchmark controlado de OCR — 02/11/2026

## Resultado e decisão

A amostra favorece conservar o Paddle Small como alternativa em inglês e melhorar a preservação da escala em páginas longas. O Tiny reduz os pesos do reconhecedor, mas perdeu acurácia neste controle e não cobre japonês/coreano. O ML Kit continua relevante para a cobertura de idiomas. Não há evidência para trocar universalmente o motor ou ativar um novo padrão de produção apenas com este conjunto.

## Detecção e reconhecimento em recortes conhecidos

Cada motor recebeu os mesmos pixels. O ML Kit foi executado pela API oficial no Android 8 x86_64; os dois Paddle foram executados em ONNX Runtime CPU/Linux, com detector Small e pós-processamento transcrito do SDK Android. Isto avalia a qualidade nestes recortes sintéticos, não o fluxo inteiro do Polaris nem velocidade em ARM.

A tabela conta textos completos exatos após normalização. Os 27 recortes em inglês incluem 8 textos em três fontes (DejaVu Sans, Anime Ace e Balsamiq Sans) e 3 controles. Cada outro idioma tem apenas 3 recortes horizontais em Noto Sans CJK.


| Motor | Inglês | Japonês | Chinês simplificado | Chinês tradicional | Coreano |
| --- | --- | --- | --- | --- | --- |
| ML Kit 16.0.1 (API Android) | 19/27 | 3/3 | 3/3 | 3/3 | 3/3 |
| PaddleOCR v6 Small + detector Small | 26/27 | 3/3 | 3/3 | 3/3 | Sem cobertura desta escrita |
| PaddleOCR v6 Tiny + detector Small | 22/27 | Sem cobertura desta escrita | 3/3 | 2/3 | Sem cobertura desta escrita |

### Inglês: erro de caracteres

| Motor | Erros / caracteres | CER |
| --- | --- | --- |
| ML Kit 16.0.1 (API Android) | 11/527 | 2.09% |
| PaddleOCR v6 Small + detector Small | 1/527 | 0.19% |
| PaddleOCR v6 Tiny + detector Small | 5/527 | 0.95% |

O Small com detector perdeu a letra isolada “I” em DejaVu Sans. O ML Kit também errou textos muito curtos como “NO!” e teve substituições em Anime Ace, como O por 0. Os exemplos completos, incluindo os acertos, estão em comparacao.html. Não foi demonstrado o mecanismo causal desses erros.

### Reconhecedor Paddle isolado, sem detector

Esta etapa separada fornece diretamente o recorte ao reconhecedor. Não deve ser misturada à tabela anterior para declarar um vencedor do sistema completo.

| Motor | Inglês | Japonês | Chinês simplificado | Chinês tradicional | Coreano |
| --- | --- | --- | --- | --- | --- |
| Small: reconhecedor isolado | 24/27 | 3/3 | 3/3 | 3/3 | Sem cobertura desta escrita |
| Tiny: reconhecedor isolado | 21/27 | Sem cobertura desta escrita | 3/3 | 2/3 | Sem cobertura desta escrita |

## Página longa: detecção Paddle

O detector Small embarcado foi executado na imagem original 720 × 20.000 e em 12 faixas de até 2.048 px, sobreposição de 384 px. O pré-processamento limita o maior lado a 960, arredonda dimensões a múltiplos de 32, usa BGR e a normalização do SDK, com limiares 0,3/0,6.

| Entrada | Dimensão de entrada do detector | Linhas de referência encontradas |
| --- | --- | --- |
| Página inteira | 32 × 960 | 0/38 |
| Faixas | 352 × 960 por faixa completa | 38/38 |

Critério: IoU ≥ 0,3 entre regiões aceitas antes do unclip e 38 caixas de texto conhecidas. Esse é um teste de **detecção**, não de tradução nem uma afirmação de 38 leituras corretas. As 60 regiões brutas nas faixas incluem repetições. Este controle não comprova que o capítulo real do usuário seja uma única imagem tão alta: o leitor também pode empilhar imagens menores.

## Página longa: texto reconhecido

Após reconhecer, as linhas foram ordenadas por y/x; nas faixas, as duplicatas foram removidas por geometria, priorizando a linha mais distante da borda. A saída bruta também foi preservada. Não houve correção manual do texto.

| Motor | Página inteira: erros/caracteres (CER) | Faixas: erros/caracteres (CER) |
| --- | --- | --- |
| ML Kit 16.0.1 (API Android) | 711/711 (100.00%) | 0/711 (0.00%) |
| PaddleOCR v6 Small + detector Small | 708/711 (99.58%) | 0/711 (0.00%) |
| PaddleOCR v6 Tiny + detector Small | 710/711 (99.86%) | 0/711 (0.00%) |

## Cobertura e tamanho dos modelos

O dicionário Small avaliado contém hiragana/katakana, mas nenhum caractere Hangul. O Tiny avaliado não contém hiragana, katakana ou Hangul. A verificação inclui nomes Unicode e variantes de largura, não apenas um intervalo de sílabas. As saídas dessas escritas sem cobertura estão preservadas nos dados brutos, mas não entram em uma classificação de acurácia. O caminho Paddle do aplicativo continua restrito a inglês; os acertos japoneses do modelo isolado não indicam uma funcionalidade liberada no app.

O reconhecedor Small tem 21.159.378 bytes e o Tiny 4.462.639 bytes: economia bruta de aproximadamente 15,9 MiB. O detector Small de 9.880.512 bytes continuaria necessário nesta configuração. Isso não equivale ao tamanho instalado, à diferença de APK comprimido, nem ao consumo de RAM/cache. Nenhum peso novo foi acrescentado ao Polaris neste ensaio.

## Método e limites

- Transcrições conhecidas, de imagens de controle autorais. Não foram fornecidas imagens do capítulo real com falha. Não cobrimos furigana, texto japonês vertical, arte de scans reais, fotos ou todos os casos de baixo contraste.
- CER: distância de Levenshtein após Unicode NFKC, casefold e remoção de espaços. Pontuação permanece. Texto exato usa a mesma normalização. Falhas de execução ficam separadas dos erros de OCR.
- ML Kit Text Recognition 16.0.1: modelos embarcados Latin/Japanese/Chinese/Korean; sem tradução, Gemini ou inferência remota. Aplicativo de benchmark separado do Polaris.
- Paddle: ONNX Runtime 1.21.1, CPU, uma thread, OpenCV 5.0.0.93; reconhecedor RGB, altura 48, preservação de proporção, normalização x/127,5−1, CTC e batch 1. Detector Small igual para os dois reconhecedores.
- O port desktop do detector usa quad, unclip 1,5, limiares 0,3/0,6 e ordenação horizontal nos recortes de uma linha. O Android usa OpenCV 4.5 e pode agrupar batches; este não é o binário Android do Paddle nem uma validação exata do wrapper de produção.
- O Android foi AOSP API26 x86_64 sem KVM. A tentativa inicial em API31 não estabilizou. Um inicializador Jetpack de UI incompatível no harness foi removido; DEX, modelos e recursos ML Kit foram preservados. Nenhuma saída da tentativa que falhou entrou na precisão.
- Tempos brutos pertencem a runtimes diferentes e não permitem ranking de velocidade entre motores ou projeção para ARM32/ARM64. O teste não mede memória de pico; o harness Android mantém a imagem completa em RAM durante as faixas.
- Tradução, filtros de balão, agrupamento e renderização do Polaris não participam desta comparação. As faixas do app continuam experimentais e desligadas por padrão.
- Relatório, imagens, saídas brutas, hashes e código estão no pacote. A release pública e os APKs do produto não foram alterados.
