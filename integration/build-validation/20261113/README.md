# Compilação e testes — P20261113.3

Candidata beta.11/código112. **Sem APK novo ou lançamento.**

A compilação Android real e 906 testes JVM passaram: app821, domain85; nenhuma falha ou skip. As tarefas de data e source-api terminaram NO-SOURCE, sem casos. Os 880 casos do checkpoint P20261112.1 foram comparados a partir dos relatórios arquivados, sem reexecutar aquela base: nenhum caso desapareceu, 26 casos novos passaram. Isso não equivale a aceite Android/ARM.

## Correções desta revisão

- A importação de cookies não sobrescreve credenciais HTTP atualizadas enquanto o navegador estava aberto. Alterações concorrentes em outra chave sobrevivem; conflito na mesma chave interrompe toda a transferência antes de mutação. Limpar sessão continua revogando clientes antigos. Quatro regressões reproduziram o problema (43 passaram, quatro falharam) e depois os 47 casos focados passaram.
- O login aguarda todos os callbacks de cookies antes de habilitar a transferência; falha de seed encerra a tentativa. Confere o nome do perfil. Leitura/gravação cifrada em disco usa Dispatchers.IO; APIs WebView continuam na thread da interface e cancelamento é propagado.
- AppCompat1.7.1/Core1.19.0 do widget foram alinhados ao catálogo já usado no app. A declaração WebKit1.16.0 foi tornada explícita para compilar a atividade. As três versões já constam do runtime arquivado em integration/personalization-audit/20261107/runtime-dependencies.json.
- Somente UnitTestRuntimeClasspath substitui okhttp-android pelo artefato oficial okhttp-jvm da mesma versão. A implementação Android carrega PublicSuffixDatabase pelos assets e não dispõe de Application nos testes JVM. A primeira execução completa compilou, mas falhou em dois testes novos por esse motivo; a execução definitiva usa a implementação JVM real, sem mock dessa validação. Configurações de produção mantêm OkHttp Android.
- O exportador aceita --previous-manifest e rejeita ID/certificado divergentes. Sem a opção, o manifesto registra NOT_CHECKED; não declara compatibilidade. Treze testes do exportador passaram, incluindo quatro novos de identidade. Quatro testes de aplicação/idempotência/CRLF/drift do overlay passaram.

## Execução e evidências

`android-compile-unit.log` é a execução definitiva de :app:compileDebugKotlin, :app:testDebugUnitTest, :domain:testDebugUnitTest, :data:testDebugUnitTest e :source-api:testDebugUnitTest, com Gradle9.6.1/JDK21/SDK37. BUILD SUCCESSFUL, 273 tarefas. O comando usou --no-daemon --max-workers=2 e -Xmx2g/-XX:MaxMetaspaceSize=768m, pelo wrapper de proxy herdado. As 159 saídas XML originais estão em junit-reports.zip; RESULT.json, unit-comparison.json e source-provenance.json vinculam contagens e fontes.

`cookie-concurrency-red.log`/`cookie-concurrency-green.log` e seus manifests registram o ensaio focado antes/depois. Ele extrai o núcleo CookieBank sem alteração e não testa Keystore/WebView Android. `overlay.log` e `packaging.log` registram os testes Python. SHA256SUMS.txt identifica os bytes dos artefatos desta pasta.

## Bloqueios atuais

A tentativa seguinte de :app:assembleDebug com -Ppolaris.universalArm=true falhou durante processamento das bibliotecas nativas, com o disco de 7.9GiB cheio. O log apk-assembly-failed.log registra :app:stripDebugDebugSymbols e erros de criação de diretórios; não houve APK final. Somente intermediários e caches regeneráveis desta tarefa foram removidos para recuperar espaço.

A chave debug gerada neste ambiente tem certificado diferente da beta.10 pública. signing-check.json contém somente identificadores públicos e a rejeição pelo guard, não material privado. A busca nos metadados do Drive conectado, pastas de originais/releases do Polaris e nomes/histórico/documentação do repositório não localizou a chave original. Isso não prova perda: conversas e arquivos de outra conta não ficam automaticamente acessíveis aqui. A chave não pode ser reconstruída a partir do APK ou certificado público. Não desinstalar para contornar conflito.

Permanecem login real, OAuth/CDN/Cloudflare genérico, controles dinâmicos/novels, biblioteca/backups entre leitores, armazenamento real, OCR/tradução e aceite ARM. O navegador continua uma superfície do host, fora do worker e sem mediação completa de toda a rede do Chromium. Ver docs/BETA11_CHECKLIST.md.
