# Cache de documentos — P20261114.2

Continuação da beta.11/código 112. Conta/login Google/nuvem permanecem adiados. Nenhum APK ou lançamento novo nesta etapa.

## Correção

DocumentFiles usava URI, tamanho e data como identidade do cache mesmo quando o provedor devolvia zero ou valor negativo para tamanho/data. Assim, alterações no documento podiam continuar abrindo a cópia antiga. Uma falha posterior no provedor também podia ficar escondida por esse cache. O caminho atende PDF e o leitor textual de EPUB/DOCX/TXT.

Quando tamanho ou data não são positivos, o app agora relê a origem para um temporário limitado e calcula SHA-256 durante a cópia. O arquivo definitivo usa essa identidade de conteúdo: bytes diferentes não substituem uma cópia já aberta; bytes iguais podem compartilhar o cache entre essas leituras, inclusive de URIs diferentes com metadados incertos. O cache existente é conferido por tamanho e hash antes de reutilizar. Se estiver corrompido, a operação falha sem substituí-lo e exige limpeza do cache.

O orçamento de cache mantém o bloqueio desde a preparação do temporário até a aquisição da referência de uso. A limpeza não pode remover esse temporário nem o arquivo final antes de ficar protegido. Referências simultâneas continuam protegidas até a última ser fechada. Falha de stream e documento vazio removem apenas o temporário próprio. O original escolhido não é modificado.

Com tamanho e data positivos, permanece a reutilização por metadados, sem reler a origem a cada abertura. Na primeira cópia, os bytes precisam corresponder ao tamanho informado e os metadados são reconferidos. Cache incompleto não é substituído enquanto pode estar aberto.

## Custo e limites

A via por conteúdo exige nova leitura e temporário antes de reutilizar, e relê o cache existente para conferência. Não elimina pico de espaço nem garante melhor velocidade; medir A12/ARM permanece necessário. O limite por documento continua 256 MiB. A meta de cache de 256 MiB continua parcial e referências em uso podem excedê-la. Não há nova reserva de espaço para materialização/renderização.

Tamanho/data positivos ainda dependem do provedor. Alteração com tamanho igual e data positiva congelada não é detectada no caminho rápido. Não há garantia de snapshot atômico do provedor nem mecanismo genérico de cancelamento da cópia síncrona. Caches antigos de metadados incertos podem permanecer até a limpeza usual. A revisão não altera deduplicação de importados, biblioteca, posição de leitura, traduções ou formato do backup.

## Verificação

Testes usam o materializador/orçamento reais, streams e arquivos locais; Context e metadados UniFile são simulados. Dois cenários Android com UniFile nativo e cache isolado foram preparados; o cenário de timestamp ausente usa assume se o filesystem não permitir data zero. A compilação desses cenários não representa execução física nem teste SAF real.

[Evidências filtradas](../integration/document-cache/20261114/README.md) · [Checklist](BETA11_CHECKLIST.md).
