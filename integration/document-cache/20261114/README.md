# Cache de documentos com metadados ausentes — P20261114.2

Continuação da beta.11 no mesmo PR12 em rascunho. DocumentFiles usa conteúdo quando tamanho ou data não são positivos. Releitura evita retornar bytes antigos da mesma URI; conteúdo igual pode compartilhar uma cópia de cache. Metadados positivos conservam o caminho rápido. Cópias abertas não são substituídas e o lock do orçamento protege o temporário até o pin final.

## Validação

O materializador anterior executou cinco testes: quatro falharam por retorno de conteúdo antigo ou ocultação de erro do provedor; o controle do caminho rápido passou. Na versão final, **904 testes do app passaram**, incluindo 14 novos. Mais 85 casos de domain anteriormente aprovados ficaram UP-TO-DATE. Relatórios somam **989/989**, sem falhas/skips. Comparação contra 975 casos arquivados da .1: nenhum ausente e 14 novos aprovados; a base não foi reexecutada.

Os 14 casos usam DocumentFiles e DocumentCacheBudget reais, streams/arquivos locais, com Context e metadados UniFile simulados. Cobrem metadados ausentes, alterações com mesmo tamanho/data, provedor ilegível, caminho rápido, reuso entre URIs, stream parcial, vazio, tamanho incoerente, mudança durante cópia, corrupção de cache, referências simultâneas, limpeza concorrente e limite declarado. O controle concorrente usa gates e confirma que trim não conclui até o final ser protegido.

Core/archive, app e instrumentação Kotlin compilaram: BUILD SUCCESSFUL em 1min55s. Quatro testes completos do overlay e 16 de empacotamento passaram. Dois cenários Android com UniFile nativo e cache isolado foram compilados, **não executados**; o de timestamp zero usa assume quando não suportado. ADB sem aparelho/emulador. A evidência pública contém apenas resultados/identidades/asserts/hashes legíveis, sem configurações de ambiente, stdout ou traces locais.

## Limites

Metadados ausentes exigem leitura e temporário, mais conferência de um cache existente; não há benchmark ARM/A12 nem economia de pico comprovada. A meta de 256 MiB continua parcial, com referências em uso protegidas. Não há nova reserva de espaço para materialização/renderização ou cancelamento genérico da cópia síncrona. Tamanho/data positivos ainda são confiados: edições de mesmo tamanho com timestamp positivo congelado não são detectadas no caminho rápido. Cache corrompido é recusado sem sobrescrever e precisa de limpeza. Não há novo esquema, formato de backup, mudança de biblioteca/traduções ou importação automática de legado.

Conta/login Google/nuvem permanecem adiados. Sem novo APK; o interno disponível continua .3, sem as revisões posteriores. Não é aceite de SAF/Android real ou de desempenho. [Escopo](../../../docs/CACHE_DOCUMENTOS_P20261114_2.md) · [Checklist](../../../docs/BETA11_CHECKLIST.md).
