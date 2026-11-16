# Backups, progresso e persistência SQLite — P20261115.4

Continuação da beta.11/código 112, sem novo APK ou Release. Sandbox permanece arquivada/retirada do código compilado; conta/nuvem continuam adiadas.

## Problema reproduzido

O restaurador preservava o estado lido e o marcador, mas podia reduzir a última página. Três testes com o banco SQLite real e o código anterior reproduziram:

- Capítulo local ainda não concluído na página 20 + backup antigo na página 4: ficava na página 4.
- Capítulo local na página 20 + backup que o marcava como concluído na página 4: também ficava na página 4.
- Capítulo local concluído na página 10 + backup com página 18: mantinha a página 10 e ignorava o avanço.

A mesclagem agora conserva a maior `lastPageRead` entre banco e backup, além do OU já pretendido para lido e marcador. Uma restauração não reduz esses estados em um capítulo existente. Novos capítulos continuam recebendo o estado do arquivo; a busca permanece por obra e fonte nativas, preservando identidades distintas.

Não há mudança de SQL, migração, Protobuf ou formato do backup. A correção está no `MangaRestorer`, dentro das transações já existentes.

## Persistência verificada

A suíte acrescenta um banco temporário em arquivo, criado pelo `Database.Schema` de produção e acessado pelos repositórios/interatores reais. O driver SQLDelight JDBC 2.3.2 e SQLite JDBC 3.51.3.0 ficam em `testImplementation`; não são dependências do aplicativo distribuído. Chaves estrangeiras são ativadas e uma tentativa de inserir capítulo órfão precisa falhar por restrição real.

Os controles exercitam progresso crescente, página zero, marcador/conclusão, separação por fonte, restauração repetida, categorias remapeadas, histórico sem somar novamente a mesma duração, acompanhamento, fechamento/reabertura do arquivo, rollback por erro SQL tardio, rollback por cancelamento e fallback do lote para obras válidas após rollback.

Dois arquivos sintéticos de Tachiyomi/Mihon, produzidos com os DTOs upstream fixados anteriormente, passam pelo decoder real, coordenador/categorias/biblioteca em SQLite, fechamento/reabertura, `MangaBackupCreator`/`CategoriesBackupCreator`, gzip/Protobuf e decoder real novamente. São conferidos identidade da fonte, obra, capítulo lido, marcador, página, associação por categoria atual, histórico, acompanhamento, notas e memo. Isso avança além dos testes anteriores que simulavam a persistência da biblioteca.

## Limites

SQLite desktop/JDBC não substitui a execução em Android com o driver do aplicativo. Dois controles Android usam `BundledSQLiteDriver`/`AndroidxSqliteDriver` com banco temporário de nome aleatório: mesclagem/reabertura e rollback por falha SQL tardia. Eles são compilados para a rodada final; não há execução em aparelho nesta etapa.

Contexto, notificações, tarefas Android e algumas fronteiras do coordenador continuam simulados nos testes JVM. As preferências Android, a interface e a troca pela interface de leitores externos ainda precisam da validação final. O teste de reexportação usa o codec real do Polaris; não afirma uma ida e volta completa pela UI de Tachiyomi/Mihon nem igualdade de IDs, versões e campos locais de agendamento após persistir.

## Resultado da rodada

Compilação final aprovada em 2min42s. Foram executados e aprovados 889 testes do app e 85 de domain: 974/974, incluindo os 16 casos novos. Nenhum dos 958 casos anteriores ficou ausente. Quatro testes de aplicação/idempotência/CRLF/drift do overlay e 16 de empacotamento passaram. Os dois controles Android foram compilados, não executados; a consulta de dependências release não encontrou sqlite-jdbc. As classes/componentes da sandbox continuam ausentes do JAR de produção e do manifesto mesclado.

[Resultados filtrados e hashes](../integration/backup-sqlite/20261115/README.md) · [Checklist ativo](BETA11_CHECKLIST.md).
