# Revisão da biblioteca — P20261110.2


Beta.11/código 112 em desenvolvimento, posterior a 324f170. A beta.10 pública, main, tag e arquivos permanecem inalterados. [Achados, correções e limites](../../../docs/REVISAO_BIBLIOTECA_P20261110_2.md).

## Correções verificadas

- Numeração revalidada nas consultas, fluxos, apresentação da biblioteca, ações de obra e escolha da raiz do leitor; a transação também lê os capítulos atuais antes de gravar a associação.
- Faixas adjacentes exigem a mesma temporada, volume e parte. O consolidador, a transação e as consultas de associação usam o mesmo critério de catálogo suportado.
- Separar ou permitir associação inclui a entrada solicitada mesmo fora dos favoritos, mantendo a escolha de não adicioná-la à biblioteca.
- Memos da obra e perfis de numeração são preparados por edição, evitando repetir esse trabalho para cada capítulo ou par de fontes.

## Evidências

- **845/845 testes JVM passaram**, com os 837 casos anteriores preservados, oito novos e nenhum skip. [Comparação](unit-comparison.json), [JUnit](junit).
- Os novos casos cobrem mudanças de numeração sem alteração de metadados/quantidade de linhas, fluxo que separa e recupera o grupo, filtros de scanlators, preservação de entradas visíveis, temporadas/volumes/partes diferentes, ID de catálogo não suportado, aliases com faixas complementares e duas edições de 10 mil capítulos. O teste grande confere os 20 mil IDs nativos, donos de armazenamento e 10 mil capítulos lógicos; não mede desempenho no A12.
- **21/21 casos Android passaram em API26/x86_64:** os 17 componentes anteriores e quatro novos casos com esquema SQLite e repositórios de produção. A gravação rejeita uma numeração alterada por SQL após o planejamento, com os metadados da obra ainda iguais. Outro caso confirma separação/recuperação com leitura parcial preservada. Os dois restantes verificam permitir/separar com a entrada principal fora dos favoritos. [Instrumentação](android-final.log).
- **13 controles de overlay/empacotamento passaram**, incluindo aplicação limpa, idempotência, deriva, CRLF e presença do novo critério compartilhado. Os 370 caminhos cumulativos, incluindo cinco exclusões, correspondem aos fontes compilados; nesta revisão há um arquivo novo e dez alterados. [Hashes dos fontes](compiled-overlay.json), [delta](source-delta.json).
- A [proveniência da rodada Android](android-run.json) registra os hashes dos dois APKs e do patch antes de executar os testes. O coletor exige que correspondam aos artefatos finais. Os APKs são debug/x86_64 para componentes, não pacotes para celular.
- O emulador apresentou ANR do System UI no boot, antes dos testes; Close App reiniciou a interface. Processos de fundo da instalação anterior foram encerrados antes da instrumentação. Dados, verificação de APK e SELinux foram preservados, sem mudar código para contornar essa condição. [Registro do ambiente](runtime-environment.json).

Não há dependência, modelo OCR ou alteração de esquema SQL/backup novos. A consulta anterior de vulnerabilidades não foi repetida nesta etapa. [Resultado estruturado](TEST_RESULTS.json), [hashes das evidências](SHA256SUMS.txt).

## Reprodução e limites

Aplique a pilha de overlays ao upstream fixado com os scripts do projeto. Use JDK21/SDK37 e rode `:domain:testDebugUnitTest :data:testDebugUnitTest :source-api:testDebugUnitTest :app:testDebugUnitTest`. Para os APKs de componentes, acrescente os init scripts arquivados e `:app:assembleDebug :app:assembleDebugAndroidTest`. O init de runtime seleciona apenas x86_64 e o host de componentes; não o utilize para distribuir celulares.

O componente de banco inclui agora nove testes e pode ser executado depois de instalar os APKs:

```sh
adb -s SERIAL shell am instrument -w -r \
  -e class eu.kanade.tachiyomi.polaris.LibraryConsolidationAndroidTest \
  app.mihon.tachiyomiat.dev.test/eu.kanade.translation.recognizer.OcrComponentTestRunner
```

Essa seleção deve concluir com `OK (9 tests)`. A rodada arquivada inclui os demais componentes e termina com `OK (21 tests)`; exit0 do ADB sozinho não comprova aprovação.

As sequências são sintéticas, com armazenamento real do Android. Permanecem pendentes o fluxo completo com backup pessoal e provedores reais, navegação/ações na interface, arquivos reais de downloads, ida/volta em leitores externos, desempenho em ARM e custo do caminho com filtro. A comparação de metadados não reconhece toda renumeração arbitrária quando os rótulos ainda parecem compatíveis. A redução de trabalho repetido no código não certifica fluidez em dispositivos modestos, e esta revisão não conclui a sandbox ampla.
