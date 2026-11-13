# Controles numéricos da sandbox — P20261113.4

Continuação da beta.11/código 112. Sem novo APK nesta etapa; o arquivo interno já disponibilizado permanece P20261113.3. Não há lançamento público.

## Implementação

SeekBarPreference padrão é descrito pelo worker e reconstruído como widget próprio no host. A alteração usa o fluxo assíncrono existente, com Int estrito, armazenamento por pacote/assinatura e callbacks no processo isolado. O host grava ao encerrar o ajuste, evitando RPC por movimento da barra. Faixas negativas/fixas são aceitas; amplitude e incremento são limitados, e o cálculo em Long impede overflow. Os setters dos extremos consideram a ordem de clamp do AndroidX.

A extração SandboxPreferenceSchema mantém o contrato dos controles anteriores e centraliza validação, identificação estrutural e política numérica. Limites/opções/tipo alterados invalidam formulário antigo; mudanças de valor/resumo/estado não trocam o identificador. Importação explícita reconhece o novo tipo, preserva Int e valida a faixa antes de escrever o lote; mantém o arquivo nativo original. [Comportamento e limites](../../../docs/SANDBOX_CONTROLES_P20261113_4.md).

## Validação real

- **833 testes do app executados e aprovados**, incluindo 12 novos; nenhum skip. Com os 85 testes de domain já aprovados e UP-TO-DATE, os relatórios somam 918/918. data/source-api permanecem NO-SOURCE. A comparação usa 906 casos arquivados de P20261113.3, sem rerodar aquela base: nenhum desapareceu, 12 novos aprovaram.
- Compilação Kotlin real do app e de instrumentação passaram: :app:compileDebugKotlin e :app:compileDebugAndroidTestKotlin. BUILD SUCCESSFUL em 3min57s, 285 tarefas, 25 executadas. build-result.json registra o comando e o guard de espaço; nenhum disparo, mínimo 591.818.752 bytes livres.
- Quatro testes completos de aplicação/idempotência/CRLF/drift do overlay e 16 do empacotador passaram. O marcador do exportador e da aplicação do overlay acompanha P20261113.4.
- Fixture DEX sintética compilada contra Source API atual e AndroidX. Mantém as classes/casos antigos e acrescenta NumericSource. O gerador aceita --android-jar para uma plataforma instalada em caminho diferente do padrão. A fixture não contém chave de assinatura ou fontes de terceiros.
- Três cenários Android novos foram **compilados, não executados**: persistência Int/callback em UID isolado com rejeição sem mutação, mudança de limite com formulário antigo e importação de valor inválido preservando os arquivos. ADB consultado: nenhum dispositivo/emulador conectado. Isso não é aceite de interface/toque, fonte real, Android recente ou ARM.

android-compile-unit.log contém a execução Gradle; os 160 relatórios XML originais estão em junit-reports.zip. unit-comparison.json, RESULT.json e source-provenance.json relacionam contagens e hashes. fixture/ contém fonte/proveniência; fixture-build.log registra o compilador/D8. overlay.log e packaging.log registram as verificações Python. adb-devices.log registra a consulta real ao ADB.

## Pendências preservadas

Opções carregadas por clique, ações/telas personalizadas, backing types customizados, login real/OAuth/Cloudflare, novels, biblioteca/backups entre leitores, armazenamento/OCR/tradução em aparelhos e atualização beta.10→beta.11 seguem abertos. Não executar código da extensão no host ou habilitar compatibilidade automaticamente para preencher esses itens. [Checklist](../../../docs/BETA11_CHECKLIST.md).
