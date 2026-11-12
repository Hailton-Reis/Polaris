# Checks GitHub e candidato beta.9

Revisão de 04/11/2026. O candidato continua em rascunho. Os resultados locais de 635 casos JVM e 16 controles Android não significam que todos os workflows do repositório passaram.

## Domain spikes

A execução [41876359061](https://github.com/Hailton-Reis/Polaris/actions/runs/41876359061) passa pelas verificações Python, SQLite e pelos primeiros ensaios de backup, mas falha em **Compile and test Yomotsu source-aware backup adapter (host-only)**.

O ensaio de `spikes/spike001/backup/yomotsu-candidate/host-tests/YomotsuBackupExporterTest.kt`, criado em 15/10, entrega o pai virtual de fonte 6969 entre os mangás comuns. O contrato atual `BackupPolarisBundle.validateSnapshotCoverage` rejeita esse formato misto:

> A Polaris archive cannot also carry legacy virtual parents in ordinary manga backups

A proteção existe para impedir recriar dois pais durante a restauração. Esse candidato antigo precisa ser atualizado de acordo com o contrato completo de snapshots dos pais, preservando seus metadados; remover a proteção ou simplesmente descartar os pais não é uma correção aceitável. A revisão não altera esse ensaio nem declara aceitação de backup por ele.

`PolarisYomotsuBackupExporter` e `BackupPolarisBundleBuilder` pertencem a esse protótipo de host. Não estão nos diretórios app/domain/data da árvore Android usada para compilar os APKs beta.9 e não são acrescentados pelo overlay compilado. Esta constatação delimita o alcance da falha; não comprova aceitação geral de backup/restauração no aparelho.

## Issue 002 Android build gate

A execução [41876359308](https://github.com/Hailton-Reis/Polaris/actions/runs/41876359308) falha em **Install pinned Android toolchain**:

> sdkmanager: command not found

A falha ocorre antes de compilar o aplicativo ou executar a comparação JVM. O workflow invoca `sdkmanager` pelo PATH sem preparar explicitamente as ferramentas Android. É uma pendência de preparação do runner; este check não fornece uma compilação adicional aprovada para o candidato.

A compilação local usou o SDK e JDK identificados na evidência do candidato, montou os APKs e executou a comparação completa. Esses resultados continuam registrados separadamente, com as 17 falhas JVM preexistentes informadas.

## Upload de anexos

O workflow **Upload reviewed beta assets** é separado. Verifica os hashes de cada parte, recompõe os APKs completos e só anexa os arquivos a um rascunho com identidade e commit correspondentes ao plano revisado. Ele não compila o app, não aprova os checks acima e não publica a versão. Seu resultado fica no registro do rascunho deste diretório.

Permanecem pendentes os checks de CI descritos e a aceitação física de instalação/atualização, dados, leitura, redes, notificações e recursos nos aparelhos ARM32/ARM64.
