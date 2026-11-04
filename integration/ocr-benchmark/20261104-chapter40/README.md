# Ensaio real: Solo Leveling: Ragnarok, capítulo 40

O Paddle Small foi melhor nos recortes difíceis desta amostra em inglês: **9/11 textos exatos e 2 erros em 465 caracteres**, contra **7/11 e 10 erros no ML Kit**. Isso favorece testar o Paddle existente com faixas, mantendo ML Kit como tradutor. Não estabelece um vencedor universal ou uma classificação de velocidade em celulares.

## Material e execução

O usuário usa **MangaCloud EN**, no repositório Awerkori. O acesso automático dessa fonte não ficou disponível. O ensaio utilizou a [edição pública da Asura do capítulo 40](https://asurascans.com/comics/solo-leveling-ragnarok-ab39de10/chapter/40): as cenas coincidem visualmente com as referências, mas a divisão e os arquivos não foram comparados por hash com os originais do MangaCloud.

São **15 imagens**, incluindo créditos e páginas de cerca de 13.000–15.000 px de altura. O MangaCloud mostrava 54 páginas na captura; essa diferença de segmentação importa para o OCR. As faixas atuam na imagem individual, não em toda a rolagem do leitor.

| Execução | Resultado |
| --- | --- |
| Paddle Small, página inteira | 15/15 imagens processadas |
| Paddle Small, faixas sobrepostas | 15/15 imagens processadas |
| ML Kit do produto, página inteira | 15/15 imagens processadas |
| ML Kit do produto, faixas | Uma imagem alta concluída; duas atingiram o limite de 180 s; demais não medidas |
| Comparação de recortes com os mesmos pixels | 11/11 recortes processados pelos dois motores |

O Paddle foi executado com os pesos existentes em ONNX Runtime CPU/Linux e o port de processamento documentado no [ensaio anterior](../20261102/README.md). O ML Kit usou a classe real `MlKitOcrEngine` no Android AOSP API26 x86_64 sem aceleração. Os tempos e runtimes diferem; não servem para dizer qual será mais rápido ou consumirá menos memória em ARM32/ARM64. Os limites de tempo ficam separados dos erros de reconhecimento.

## Precisão dos recortes

As 11 regiões foram transcritas manualmente a partir dos pixels: missão, contador, legendas sobre arte, balões conectados, balão espinhoso, caixa branca e balões brancos de controle. Os recortes mantêm a resolução da fonte. **O CER abaixo é dessas regiões, não do capítulo inteiro.**

| OCR | Textos completos exatos | Erros/caracteres | CER |
| --- | --- | --- | --- |
| Paddle Small existente | 9/11 | 2/465 | 0,43% |
| ML Kit | 7/11 | 10/465 | 2,15% |

| Tipo de região | Paddle: textos exatos | ML Kit: textos exatos |
| --- | --- | --- |
| Missão: título, descrição e contador | 2/3 | 1/3 |
| Texto diretamente sobre arte escura | 2/2 | 0/2 |
| Balões espinhosos conectados | 2/2 | 2/2 |
| Balão espinhoso isolado | 0/1 | 1/1 |
| Caixa branca e balões brancos de controle | 3/3 | 3/3 |

Portanto, o ML Kit também venceu um caso isolado. A amostra é pequena e selecionada pelos defeitos relatados. Outros capítulos, estilos de letra, resoluções e idiomas podem mudar o resultado. O Tiny não foi integrado nem testado neste capítulo; seus resultados anteriores pertencem ao controle sintético.

A normalização usa NFKC, casefold, remoção de espaços e padronização de aspas curvas. Pontuação continua contando. O avaliador rejeita resultados duplicados e mantém ausências/falhas de execução fora do CER. [Métricas Paddle](paddle-region-score.json), [métricas ML Kit](mlkit-region-score.json), [regiões e hashes](region-manifest.json) e [proveniência](provenance.json) permitem conferir o escopo.

## Problemas identificados

- A sobreposição das faixas repetia algumas linhas quando as caixas do mesmo texto tinham alturas diferentes. O replay do capítulo removeu **seis repetições extras** com uma correção restrita a textos iguais e geometria quase contida. Os dois novos casos falharam antes da correção; depois, todos os 16 testes do reconciliador passaram, incluindo os controles de repetições em posições distintas.
- Na missão, a repetição do objetivo já existe no original: título, descrição e contador. Essas seções precisam manter sua organização; remover palavras repetidas globalmente destruiria informação legítima.
- As legendas de estatísticas estão diretamente sobre a arte. Uma cor plana de limpeza cria um retângulo que não existia no original. O reconhecimento pode estar correto e a apresentação ainda exigir melhora na limpeza e no encaixe.
- Nos recortes, os dois OCRs reconheceram por completo o balão cuja primeira linha permanecia em inglês na captura. Isso não prova que o capítulo salvo no celular usou o mesmo processamento: DBNet ligado usa ML Kit como reconhecimento principal, e alterar opções não refaz uma tradução já salva.

## Tradução

A tentativa inicial do tradutor atingiu o limite de 120 s. Uma nova execução separou a preparação do modelo e também atingiu seu limite de 180 s no AOSP de teste. **Não houve resultado de qualidade de tradução para pontuar.** O teste confirma a limitação desse ambiente; não demonstra que o tradutor tenha falhado semanticamente no celular. O próximo ensaio de tradução precisa de um Android com os modelos prontos e deve avaliar contexto, nomes, omissões e repetição separadamente do OCR.

## Configuração para a próxima comparação

Use **OCR PaddleOCR**, **faixas ligadas**, **DBNet desligado**, **tradutor ML Kit no dispositivo**, entrada **inglês**, saída **português (Brasil)**, efeitos sonoros e edição avançada desligados. Depois repita com **OCR ML Kit** e as demais escolhas iguais. Preserve a fonte do leitor e o glossário para comparar.

Na beta.8, desligue também AOT-GAN manualmente. Na beta.9 preparada, a opção foi retirada porque sua preferência não era usada pelo processamento. Faixas e DBNet passam a ser exclusivos; opções sem o requisito de inglês/ARM64 ficam indisponíveis. Restaurar um requisito não liga o experimento automaticamente.

Antes de trocar o OCR, remova **somente a tradução salva**, pelo ícone de tradução → Excluir, e traduza novamente. O original permanece. Retraduzir uma única frase no editor usa o texto já reconhecido.

## Reprodução local

O pacote público contém métricas, coordenadas, hashes e código. As imagens, os resultados textuais completos e as transcrições ficaram na pasta local do ensaio.

O [executador Paddle](../../../scripts/ocr/run_paddle_chapter.py) aceita uma pasta de imagens locais, os modelos existentes e, opcionalmente, um JSON privado de regiões com `id`, `page`, `box` e `text`. Não baixa arquivos ou modelos. Use as dependências do ensaio de 02/11 e um arquivo de saída novo:

```bash
python scripts/ocr/run_paddle_chapter.py --images /local/capitulo --models /local/models --output /local/paddle-chapter.json
python scripts/ocr/run_paddle_chapter.py --images /local/capitulo --models /local/models --regions /local/manual-regions.json --output /local/paddle-regions.json
python scripts/ocr/score_chapter_regions.py --expected /local/manual-regions.json --results /local/paddle-regions.json --output /local/score.json
```

O teste Android opt-in `ChapterBenchmarkTest` lê arquivos locais de `externalFiles/chapter-benchmark`, registra cada caso e usa o runner isolado de componentes. `request.json` recebe `pages: [{page, file}]`, `modes: ["full", "strips"]` e `translate`. Para recortes comuns, basta `modes: ["full"]`. Para preparar/testar somente o tradutor, use as duas listas vazias e `translate: true`; `translation-input.json` recebe uma lista de `{id, text}`. A preparação do modelo tem resultado separado. Não há acesso à biblioteca nem publicação automática dos resultados.

Faltam validação de velocidade/memória em aparelhos ARM, tradução editorial do capítulo completo e revisão do encaixe real com Anime Ace nos dois leitores. Os controles anteriores de renderização permanecem separados desta comparação de OCR.
