# Uma obra, várias fontes — desenvolvimento P20261106.2

A beta.10 pública e seus arquivos permanecem intactos. Esta revisão prepara a próxima versão; não há APK ARM distribuído, nova tag ou publicação autorizada neste trabalho.

## Comportamento implementado

Uma entrada da biblioteca mantém sua identidade e armazenamento, mas reúne edições de fontes instaladas. O catálogo favorece português e conserva complementos em inglês, além de edições alternativas para recuperar falhas. Abrir uma obra antiga ou alcançar o fim da sequência dispara a descoberta quando necessária; uma falha de carregamento pode revalidar o catálogo e experimentar outra edição, sem pedir migração manual. A fonte fixada pela pessoa continua tendo prioridade.

O resolvedor consulta metadados públicos do MangaDex para obter nomes alternativos corroborados: o registro `ade0306c-f4b6-4890-9edb-1ddf04df2039`, por exemplo, reúne Upando Sozinho: Ragnarok, Solo Leveling: Ragnarok e Na Honjaman Level Up: Ragnarok. A confirmação também exige autoria compatível e numeração coerente. Sem evidência suficiente, não funde duas obras apenas pela semelhança do nome. Há limites de tempo, concorrência e frequência; não pesquisa todos os sites da internet a cada abertura.

O download usa a origem real do capítulo mesmo quando a fonte da entrada antiga sumiu. O armazenamento continua no lugar original. A tradução automática avalia o idioma dessa edição e uma amostra de OCR distribuída pelo capítulo com identificação de idioma local do ML Kit. Português, texto curto, idioma incerto e conteúdo misto detectado preservam as imagens. Uma amostragem de OCR não prova que todas as linhas da imagem são inglesas.

A preparação de fontes oferece português e inglês como alternativas dentro dos repositórios revisados, sem alterar o filtro de navegação e sem instalar repositórios não autorizados.

## Sandbox experimental integrada

O modo de isolamento por extensão carrega DEX em serviço Android com UID isolado. O processo não recebe o Context, banco, preferências ou arquivos privados do Polaris. O host usa DTOs limitados, PFD somente leitura para o APK e um intermediário HTTP com verificação de origem, endereços, redirecionamentos, volume e concorrência. O código da extensão não é instanciado no host nesse modo. O acesso direto ao arquivo sintético do host e a execução real do Source API são verificados pela instrumentação.

Requisições proibidas podem revogar a sessão e registrar quarentena vinculada ao pacote e hash. O aviso descreve o bloqueio, não afirma que toda falha é prova de malware. Remover o isolamento exige confirmação do modo de compatibilidade. Não existe retorno silencioso à execução fora da sandbox.

O isolamento é optativo e experimental. Extensões que exigem Application, preferências, filtros personalizados, login ou WebView podem ficar incompatíveis. Há um limite independente de tempo no host além do watchdog do processo. Os resultados não constituem garantia absoluta contra vulnerabilidades do Android, consumo abusivo de recursos ou todas as extensões existentes. A execução ARM32/64, dispositivos físicos e versões recentes do Android continua pendente. Plugins de novels têm outro caminho; não ganham isolamento de DEX por esta mudança.

## Backups

Os campos padrão continuam ProtoBuf compatíveis e usam uma única fonte real, URLs nativas de capítulos e histórico, com progresso lógico agregado. Para leitores que só suportam uma fonte por obra, a projeção escolhe a edição utilizável que cobre mais progresso e capítulos; a preferência de idioma desempata. Isso não muda a preferência por português durante a leitura no Polaris.

Um campo memo opcional já existente preserva as demais edições, a identidade original e o histórico do Polaris. A volta ao Polaris recupera esse estado quando o leitor intermediário conserva o campo. Alterações em leitura, favoritos, categorias, notas e outras configurações portáveis são reaplicadas; capítulos novos e histórico adicional da edição exportada também são incorporados. Uma migração explícita feita no outro leitor mantém a nova identidade, descartando o envelope antigo.

Leitores antigos que removem campos desconhecidos ficam apenas com a edição nativa exportada. Não é possível prometer uma ida e volta sem perda de todas as edições mescladas por todos os forks. O aceite real por banco/interface do Mihon e Tachiyomi segue pendente. Nenhuma migração de esquema SQL foi introduzida.

## Validação e limites de aceite

**764 testes JVM: 747 aprovações e as mesmas 17 falhas preexistentes; nenhum caso anterior ausente, novo erro ou teste ignorado.** São 26 casos novos contra a beta.10. Os 13 controles de overlay/empacotamento passaram. **Cinco testes Android passaram em API26 x86_64**, executando o serviço e proxy integrados, a extensão sintética compilada e o identificador de idioma real. [Resultados](TEST_RESULTS.json), [comparação](unit-comparison.json), [instrumentação](android-final.log) e [fontes compilados](compiled-overlay.json). O teste de extensão usa uma implementação compilada do Source API atual em um ZIP DEX; não é uma extensão de terceiros assinada. O APK x86_64 de instrumentação usa host de componentes, não é uma distribuição para celulares nem aceite completo da interface do leitor.

Ainda falta o teste de ponta a ponta com as extensões reais da biblioteca, backup restaurado e páginas originais no A12/S20 FE. Obras já duplicadas como registros separados da biblioteca e resultados duplicados de busca global não são deduplicados por esta etapa. Disponibilidade remota, metadados incompletos, numeração incompatível e falhas de páginas podem impedir a recuperação; não há promessa de encontrar qualquer obra em qualquer situação.

## Reprodução do componente Android

Aplique a pilha de overlays ao upstream fixado pelos scripts do projeto, usando JDK21 e SDK37. Depois de gerar os JARs de `source-api` e `core/common`, o fixture pode ser recompilado sem assinatura ou dados privados:

```sh
python scripts/extensions/build_source_sandbox_fixture.py \
  --android-root /caminho/android-preparado \
  --output /tmp/polaris-source-fixture \
  --sdk /caminho/sdk --java-home /caminho/jdk21 \
  --gradle-home /caminho/gradle --kotlinc /caminho/kotlinc/bin/kotlinc \
  --write-asset
```

O ZIP de DEX tem datas fixas; a proveniência registra hashes do Kotlin, DEX e APK. O fixture tenta ler e alterar apenas um arquivo sintético criado pelo teste e faz uma requisição proibida a loopback para verificar o intermediário. A classe de construtor travado valida o prazo imposto pelo host.

Compile `:app:assembleDebug :app:assembleDebugAndroidTest` com `runtime.init.gradle`, além dos testes JVM. Esse init script é exclusivo da instrumentação x86_64 e do host de componentes. Num emulador API26, instale os dois APKs e execute:

```sh
adb -s SERIAL shell am instrument -w -r \
  -e class eu.kanade.tachiyomi.extension.sandbox.ExtensionSandboxAndroidTest,eu.kanade.tachiyomi.extension.sandbox.AutomaticLanguageAndroidTest \
  app.mihon.tachiyomiat.dev.test/eu.kanade.translation.recognizer.OcrComponentTestRunner
```

O teste deve concluir com `OK (5 tests)`; um exit do comando ADB sozinho não comprova a aprovação. A prova roda com UID normal do aplicativo, com SELinux e verificação Android mantidos. O emulador descartável não contém dados da biblioteca do mantenedor.
