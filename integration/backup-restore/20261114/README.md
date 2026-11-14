# Restauração com categorias — P20261114.1

Continuação da beta.11 no mesmo PR12 em rascunho. Categorias agora terminam antes de iniciar biblioteca/configurações; falha ou cancelamento nessa fase impede as etapas seguintes. Conta/login Google/nuvem permanecem adiados. Sem mudança no formato de backup, SQL, dependências ou APK.

## Validação real

O ensaio anterior à correção executou 11 testes: oito falharam por ordem/cancelamento, três passaram. Inclui categoria padrão/filtros, biblioteca, falha, cancelamento direto e cancelamento externo. A versão final executou **890 testes do app, todos aprovados**, incluindo os 11 novos. Mais 85 de domain anteriormente aprovados ficaram UP-TO-DATE; relatórios finais somam **975/975**, sem falhas ou skips. Comparação contra 964 casos arquivados da .7: nenhum ausente, 11 novos aprovados. A base antiga não foi reexecutada.

App e instrumentação Kotlin compilaram. Quatro testes completos de aplicação/idempotência do overlay e 16 de empacotamento passaram. ADB não tem aparelho ou emulador conectado; não houve execução Android. Os resultados e identidades dos casos estão em JSON legível, sem propriedades do ambiente, proxy, stdout ou traces de máquina. Logs/XML completos são preservados apenas localmente. source-provenance.json vincula fontes, overlay e versão anterior.

## Limites

Os testes exercitam BackupRestorer e PreferenceRestorer reais. A criação/persistência de categorias e obras, banco e serviços Android são fronteiras simuladas. Dois backups sintéticos fixados de Tachiyomi/Mihon passam pelo decoder gzip/Protobuf real até a chamada de restauração da biblioteca e mantêm leitura/marcador/página. Não executam o MangaRestorer em um SQLite real, interface Android ou ida e volta completa em leitores externos.

As outras etapas continuam concorrentes depois das categorias. A restauração inteira não é uma transação única; categorias confirmadas podem permanecer se outra fase falhar. Aceite físico, fontes reais, reconstrução de arquivos de leitura e demais frentes continuam no checklist. O APK interno disponível continua .3 e não contém as revisões posteriores.

[Escopo](../../../docs/RESTAURACAO_CATEGORIAS_P20261114_1.md) · [Checklist](../../../docs/BETA11_CHECKLIST.md).
