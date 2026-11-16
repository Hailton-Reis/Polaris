# Backups e persistência SQLite — P20261115.4

[Problema, correção e limites](../../../docs/BACKUPS_SQLITE_P20261115_4.md).

A restauração agora conserva a maior última página e o estado lido/marcador ao mesclar capítulos existentes. SQLite em arquivo, esquema, repositórios, transações e criadores de backup de produção são exercitados nos testes novos; as fronteiras Android são simuladas na JVM.

- `red-results.json`: três regressões reproduzidas no código anterior. Dois casos retornavam da página 20 para 4; outro ignorava a página 18 e mantinha 10. Falhas anteriores de configuração/espaço não são usadas como evidência funcional.
- `new-tests.json`: 16 cenários novos aprovados, incluindo reabertura do arquivo, isolamento por fonte, idempotência, categorias, histórico/acompanhamento, rollback SQL/cancelamento, fallback do lote e dois arquivos sintéticos upstream persistidos/reexportados pelo código do produto. Restrição de chave estrangeira real também é conferida.
- `unit-test-results.json` / `unit-comparison.json`: 889 testes do app e 85 de domain executados e aprovados nesta rodada: 974/974, sem falhas/skips; nenhum dos 958 casos anteriores ausente.
- `RESULT.json`: compilação de app/instrumentação, quatro testes de overlay e 16 de empacotamento aprovados. Dois controles com o driver SQLite Android real foram compilados, não executados. `dependencyInsight` não encontrou sqlite-jdbc em `releaseRuntimeClasspath`: o driver adicional é exclusivo dos testes JVM.
- `source-provenance.json`: hashes dos fontes e overlay reproduzível; versões dos drivers de teste. Classes/componentes da sandbox continuam ausentes no JAR de produção e manifesto mesclado.

Os arquivos externos são exemplos sintéticos dos DTOs upstream fixados; a ida e volta utiliza criadores/codec do Polaris após SQLite, sem execução da UI de leitores externos. Preferências Android/interface, aparelhos/SAF e o fluxo completo de distribuição continuam pendentes. Não houve mudança no esquema SQL/Protobuf, novo APK ou Release. Não há logs brutos, ZIPs, ambiente local, chaves/senhas ou backups pessoais nestes resultados.
