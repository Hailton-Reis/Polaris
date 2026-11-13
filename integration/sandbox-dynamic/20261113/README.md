# Opções dinâmicas de configurações — P20261113.5

Continuação da beta.11/código 112, sem novo APK ou lançamento. O APK interno disponibilizado permanece P20261113.3 e não contém as revisões .4/.5.

## Fluxo implementado

ListPreference e MultiSelectListPreference padrão com OnPreferenceClickListener passam a oferecer preparação síncrona de opções no processo isolado. O host recebe somente descrições/valores limitados e abre seu próprio AlertDialog simples/múltiplo. Não chama performClick nem recebe objetos, listeners, views ou intents da extensão. O resto da tela fica indisponível enquanto prepara/exibe/salva; cancelar descarta a escolha e recarrega as configurações.

O callback precisa retornar false (não consumir uma ação personalizada) e conservar o snapshot das preferências de todas as fontes do worker. Há conferência no worker e, na resposta de preparação, no host. O broker recebe uma capacidade GET/HEAD tanto na preparação quanto na gravação preparada, inclusive durante a abertura do worker. POST válido nesse escopo é recusado como operação indisponível, sem o fluxo de quarentena por violação de endereço/método global. Operações normais mantêm GET/HEAD/POST e as políticas existentes de URLs, DNS, cookies, limites e prazos.

Cada chamada usa um worker novo. Ao salvar, a preparação é reexecutada nesse novo worker antes do listener de alteração, reconstituindo opções e closures da fonte. O esquema-base e o esquema preparado são conferidos; somente uma chave preparada pode ser alterada. Opções que mudaram invalidam o formulário antes da gravação. Isso pode repetir consultas GET/HEAD e atualizar cookies HTTP normalmente; não significa ausência universal de efeitos no servidor. Não há worker preso aguardando uma escolha na interface nem ampliação de privilégios HTTP.

Campos dinâmicos não entram na importação automática do lote legado: sem preparar suas opções, não há seleção validada. O arquivo nativo original é preservado; a pessoa abre a lista e escolhe um valor. Chaves/tipos de backup não mudam. Ações próprias, Intent/fragment, callback que retorna true, preparação que escreve preferências, carregamento assíncrono e POST nessa operação continuam indisponíveis, sem compatibilidade automática. Callbacks de alteração locais conservam a semântica anterior.

## Evidência executada

- App e instrumentação Kotlin compilados. BUILD SUCCESSFUL em 2min19s, 285 tarefas, 11 executadas; guard de disco não disparou, mínimo 527.380.480 bytes livres.
- **845 testes do app executados e aprovados**, incluindo 12 novos, sem skips. Com 85 casos de domain UP-TO-DATE já aprovados, os relatórios somam 930/930. data/source-api NO-SOURCE. Comparação com 918 casos arquivados .4: nenhum faltante, 12 novos aprovados, sem rerodar a base.
- Os novos testes exercitam listas simples/múltiplas, grupos ocultos/desabilitados, alvos desconhecidos/duplicados, flags, snapshot de preferências e capacidades HTTP com POST normal preservado.
- Quatro testes completos do overlay e 16 do empacotador passaram. A fixture DEX sintética mantém as classes anteriores e acrescenta preparação com closures, callback consumidor, escrita indevida e tentativa de POST. Fonte e hashes em fixture/; log de compilação/D8 preservado.
- **Seis cenários Android compilados, não executados**: escolha com listener reconstruído em UID isolado, múltipla seleção inválida, opções alteradas entre abrir/salvar, callback consumidor/escritor, POST sem quarentena e preservação de seleção legada. ADB não encontrou dispositivo/emulador conectado. Não há prova atual de toque/interface ou fontes reais.

android-compile-unit.log, 161 XML originais em junit-reports.zip, unit-comparison.json e source-provenance.json vinculam fontes, contagens e limites. RESULT.json e SHA256SUMS.txt identificam os artefatos. Não há chave de assinatura, senha ou dados de leitor neste registro.

## Pendências

Aceite com fontes reais/ARM, callbacks assíncronos e ações/telas customizadas, login/OAuth/Cloudflare, novels, biblioteca/backups entre leitores, armazenamento/OCR/tradução, atualização no aparelho e distribuição não depurável continuam no [checklist](../../../docs/BETA11_CHECKLIST.md). A preparação desta etapa é um subconjunto explícito dos controles dinâmicos, não compatibilidade genérica de extensões.
