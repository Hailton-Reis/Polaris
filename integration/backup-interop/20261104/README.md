# Interoperabilidade de backup — primeira validação pelo codec

Esta rodada usa o decodificador e os modelos reais do Polaris com arquivos sintéticos produzidos por serializadores compilados separadamente a partir de declarações de dois snapshots upstream:

| Referência | Commit fixado | Situação avaliada |
| --- | --- | --- |
| Tachiyomi v0.15.3, preservado no histórico do Mihon | `49991d38d97e21746dcc9e5f2c177bccb94c93b3` | Campos comuns; arquivo bruto e gzip; reexportação lida pelo codec de referência |
| Mihon, snapshot de desenvolvimento identificado pelo commit | `8794e89a866a3de578c02cefac1e609bcff5f092` | Campos comuns, notas, memo e repositórios; arquivo bruto e gzip; reexportação lida pelo codec de referência |

Não são backups de bibliotecas pessoais nem arquivos exportados pela interface dos aplicativos instalados. O teste compila seus DTOs de serialização com o plugin e runtime reais Kotlin/ProtoBuf. As funções Android/banco são removidas somente dos modelos de referência; construtores, campos, números ProtoBuf, valores padrão e nomes originais das classes de preferências são preservados. A hierarquia selada de preferências permanece intacta. Os arquivos upstream são guardados com [proveniência e hashes](provenance.json), sob a licença Apache 2.0 do projeto de origem; consulte também a licença na raiz deste repositório.

## Verificações

Os seis casos `BackupInteropTest` exercitam o `BackupDecoder` real do aplicativo; somente Context/ContentResolver/Uri são substituídos para fornecer os bytes sintéticos, sem precisar instalar extensões. Os testes usam os modelos e serializadores reais do Polaris, incluindo o mapeamento de obra/capítulo para os modelos de domínio.

São conferidos: identificador de fonte de 64 bits, URL e título com acentos, autoria, categorias por ordem, favorito, configurações do leitor, capítulo lido, marcador, última página, histórico/duração, acompanhamento e os seis tipos de preferências. O caso Mihon também verifica notas, memo, configuração de repositório e chave de assinatura. A identidade da categoria no Mihon é adicional: as associações de obras deste formato usam a ordem, não esse ID.

Duas leituras independentes verificam que cada arquivo reexportado pelo serializador do Polaris continua legível pelo codec correspondente e conserva os valores comuns. A igualdade é semântica, com valores padrão explícitos: protobufs equivalentes podem omitir ou gravar um padrão sem alterar os dados. O gerador reproduziu byte a byte os quatro arquivos de exemplo usados pelos testes. Veja [hashes](fixture-hashes.json) e [resultados](TEST_RESULTS.json).

## Limites identificados

- O Mihon desse snapshot contém `BackupManga.nextUpdate`, campo113 de agendamento, que o Polaris atual não representa. Ele é ignorado na importação e não é preservado na reexportação. A comparação de campos comuns o trata separadamente; não há alegação de preservação de todos os campos de qualquer fork.
- Os exemplos Tachiyomi usam os campos canônicos de histórico/fontes da v0.15.3. Os antigos campos `brokenHistory`/`backupBrokenSources` com numeração interna0 não são exercitados. Não há aprovação para backups anteriores que dependam deles, JSON legado ou todos os forks.
- A referência atual do Mihon foi compilada com Kotlin2.4.21 e kotlinx.serialization1.11.0, assim como o ensaio de referência Tachiyomi. Isso verifica a estrutura de serialização fixada; não reproduz a versão histórica de todo o aplicativo/runtime Android.
- Os testes ainda não executam restauração em banco SQLDelight, mescla de biblioteca existente, UI dos aplicativos, instalação de fontes privadas nem arquivos reais de capítulos. Não validam reinstalação automática de extensões ou disponibilização de fontes removidas.
- O protótipo de backup de pais virtuais não foi ativado. Seus checks antigos de CI permanecem uma pendência separada.

Não houve mudança no formato ou no código de produção do backup, nem nova compilação/publicação dos APKs. O overlay recebeu apenas testes e quatro arquivos sintéticos. A beta.9 permanece em rascunho com seus APKs anteriores.

## Reprodução

Gere os arquivos de referência usando um JDK, Kotlin e os jars de kotlinx.serialization core/json/protobuf:

```sh
python scripts/backup/reference_codec.py --output /tmp/polaris-backup-reference --kotlinc /caminho/kotlinc/bin/kotlinc --java /caminho/jdk/bin/java --serialization-dir /caminho/serialization
```

A ferramenta verifica os hashes dos fontes fixados antes de extrair os DTOs e compilá-los. Os quatro arquivos esperados estão incluídos pelo overlay em `app/src/test/resources/backup-interop`. Seus hashes devem coincidir com `fixture-hashes.json`.

No checkout Android preparado com o overlay, execute `:app:testDebugUnitTest --tests eu.kanade.tachiyomi.data.backup.BackupInteropTest`. Para guardar os arquivos que o Polaris reexportar, um init script Gradle pode definir a propriedade de teste:

```groovy
allprojects {
    tasks.withType(org.gradle.api.tasks.testing.Test).configureEach {
        systemProperty('polaris.backup.exchange', '/tmp/polaris-backup-exchange')
    }
}
```

Depois, confira os arquivos com os leitores independentes já compilados:

```sh
python scripts/backup/reference_codec.py --output /tmp/polaris-backup-reference --kotlinc /caminho/kotlinc/bin/kotlinc --java /caminho/jdk/bin/java --serialization-dir /caminho/serialization --verify-exchange /tmp/polaris-backup-exchange
```

O contrato para o fluxo de preparação de fontes continua em [Compatibilidade de backups e fontes](../../../docs/COMPATIBILIDADE_BACKUPS_E_FONTES.md). O aceite completo inclui restauração no banco e, depois, preparação das fontes sem modificar registros restaurados.
