# Restauração e categorias — P20261114.1

Continuação da beta.11/código 112, sem lançamento ou novo APK. Conta/login Google/nuvem continuam adiados. O backup local permanece disponível e seu formato não mudou.

## Problema e correção

O coordenador iniciava categorias, configurações e biblioteca como corrotinas concorrentes. Se a criação das categorias suspendesse no banco, a remarcação das preferências podia consultar uma lista ainda vazia: categoria padrão e filtros ficavam sem o destino correto. O registro das obras também podia consultar categorias antes de elas existirem.

A fase de categorias agora é uma chamada suspensa direta. Ela retorna após a conclusão do CategoriesRestorer e só então as outras etapas são iniciadas. Erro ou cancelamento nessa fase impede o início das etapas seguintes. Não se usa apenas join de um Job filho: cancelamento desse filho pode encerrar normalmente o join e permitir continuação indevida.

As outras etapas conservam seu paralelismo após essa dependência. Se a pessoa desmarca a restauração de categorias, não há importação nem remarcação de IDs de categoria pelas configurações; a biblioteca recebe uma lista de mapeamento vazia, como antes. Não há mudança nas opções da interface, no esquema SQL ou no Protobuf.

## Evidência e limites

Os testes exercitam o coordenador de produção e o mapeador real de preferências com suspensão controlada da criação de categorias. Banco, persistência de obras, notificação e serviços Android são fronteiras simuladas. Dois arquivos sintéticos de interoperabilidade, produzidos por DTOs upstream fixados de Tachiyomi/Mihon, passam pelo decoder gzip/Protobuf real até a chamada de restauração da biblioteca; o estado de leitura entregue é conferido.

Isso não equivale a restaurar um banco Android real nem a testar interface/aparelho ou ida e volta completa em outros leitores. O retorno do CategoriesRestorer depende da semântica transacional já existente. A restauração inteira não vira uma transação única: categorias confirmadas podem permanecer se uma etapa posterior falhar.

[Evidências filtradas](../integration/backup-restore/20261114/README.md) · [Checklist](BETA11_CHECKLIST.md).
