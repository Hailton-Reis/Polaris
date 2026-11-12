# Preferências e filtros isolados — P20261110.3

Beta.11/código 112 em desenvolvimento, posterior a ea7cb05; nenhuma nova publicação para celulares. [Comportamento e limites](../../../docs/SANDBOX_PREFERENCIAS_FILTROS_P20261110_3.md).

## Implementação

- Filtros nativos reconstruídos no host com descrições limitadas; estados aplicados às subclasses originais no worker. Opções antigas/incompatíveis são recusadas.
- Configurações básicas em controles AndroidX do host, carregamento e gravação assíncronos; callbacks executam no UID isolado.
- Preferências separadas por pacote/assinatura, cópia tipada limitada em cada sessão e retorno persistido antes da chamada seguinte. Sem acesso ao armazenamento global do host.
- Importação explícita das configurações antigas/restauradas e exportação com chaves/tipos nativos. Backup com namespace de fonte arbitrário é recusado; IDs nativos legados negativos continuam aceitos.
- Intents, ações de login e telas personalizadas não são executadas na interface do host, nem levam a reserva automática em compatibilidade.

## Evidências

- **858/858 testes JVM passaram**, preservando os 845 casos anteriores, com 13 novos e nenhum skip. Os novos casos exercitam estado aninhado de filtros, subclasses, opções alteradas, rejeição sem mutação parcial, limites, valores tipados e nomes de arquivos permitidos na restauração.
- **13 controles de overlay/empacotamento passaram**. A aplicação limpa também confere os arquivos de suporte e a preservação binária da fixture APK. Os 386 caminhos cumulativos, incluindo cinco exclusões, correspondem aos fontes compilados: 16 caminhos acrescentados ao overlay e 12 alterados nesta etapa.
- A fixture é uma extensão DEX sintética com filtros concretos, preferências, callbacks que gravam inteiro retornando falso e acesso global propositalmente negado. [Fonte](fixture/FixtureSource.kt). O gerador aceita `--source` sem alterar a fixture histórica.

**29/29 testes Android passaram em API26/x86_64**, em 228,536 segundos: os 21 componentes anteriores e oito novos casos de preferências/filtros. Incluem subclasses originais, callbacks em UID isolado, separação por pacote/assinatura, importação explícita e chaves nativas de backup, tipos inválidos, opções alteradas, concorrência sem perda de valores, namespace protegido na restauração e edição assíncrona na tela, com interruptor visível e toque real. A [proveniência](android-run.json) registra os hashes do patch e dos APKs antes de executar; o coletor confere os artefatos finais. O runner é um host de componentes, não o início completo do Polaris nem uma medição de desempenho ARM.

## Reprodução

Aplicar a pilha do projeto ao upstream fixado, usar JDK21/SDK37 e executar `:domain:testDebugUnitTest :data:testDebugUnitTest :source-api:testDebugUnitTest :app:testDebugUnitTest`. Para os APKs de componentes, acrescentar os dois init scripts arquivados e `:app:assembleDebug :app:assembleDebugAndroidTest`. O init de runtime seleciona apenas x86_64 e o runner de componentes; não usá-lo para distribuir celulares.

Para recriar a fixture, executar `scripts/extensions/build_source_sandbox_fixture.py` com `--source integration/sandbox-settings/20261110/fixture/FixtureSource.kt`, os caminhos locais de SDK/JDK/Gradle/Kotlin e uma saída fora dos checkouts. O arquivo de proveniência registra os hashes de fonte, APK e DEX. Não há dependência ou modelo OCR novos, nem alteração do esquema SQL/Protobuf; a consulta anterior de vulnerabilidades não foi repetida.

O primeiro ensaio recusou a classe nova porque um método retornava Boolean em vez de Unit. A assinatura e a preparação explícita da dependência Application do teste de restauração foram corrigidas; o teste de interface também aguarda o desenho ficar ocioso antes da captura. O APK principal permaneceu idêntico nessa correção. Os logs dos ensaios anteriores estão preservados junto da rodada final. O ensaio seguinte reconheceu os 29 casos e expôs seis falhas na configuração das preferências: a dependência do exemplo era definida antes de adicionar o campo, e o executor registrava a tela raiz depois da configuração. A raiz agora é registrada antes da extensão configurar a tela, e a fixture define a dependência depois de anexar o campo, como no fluxo nativo.

Permanecem pendentes fontes reais, controles dinâmicos/personalizados, login/WebView e cookies entre sessões, novels, ARM32/ARM64/Android recente, biblioteca pessoal e ida/volta por banco/interface de leitores externos. Preservar o backup original.

[Resultado estruturado](TEST_RESULTS.json), [comparação JVM](unit-comparison.json), [instrumentação](android-final.log), [hashes dos fontes](compiled-overlay.json) e [hashes das evidências](SHA256SUMS.txt).

A inspeção da primeira captura identificou que a Activity de teste não aplicava o mesmo contexto de tema da tela nativa: o estado existia, mas o interruptor não era desenhado. A fixture foi alinhada ao `SourcePreferencesFragment`; o teste passa a exigir o controle visível, injetar um toque real e conferir tanto o estado exibido quanto o valor persistido, com capturas obrigatórias antes/depois. Essa alteração afeta somente a Activity debug não exportada e o teste Android; os fontes de produção continuam iguais aos da suíte JVM de 858 casos.

## Conferência visual

As capturas obrigatórias mostram o [interruptor ligado](preview/isolated-settings.png) e o [resultado após o toque](preview/isolated-settings-disabled.png). O campo dependente fica desabilitado; o valor privado permanece oculto e a ação personalizada de login continua indisponível. Os rótulos da extensão sintética são em inglês e a interface do host usa português. [Registro da inspeção](ui-review.json).

A última alteração afetou somente a Activity debug não exportada e o teste de instrumentação. Os [hashes comparados](jvm-production-source-equivalence.json) e o [manifesto da suíte JVM](jvm-compiled-overlay.json) confirmam que os demais fontes, incluindo o código de produção, são os mesmos dos 858 testes JVM. A rodada final Android usou os novos APKs e o patch final.
