# Polaris — instalador único para Windows (R001)

**Objetivo:** reproduzir o padrão do orquestrador de um CMD do CameraGuard sem consumir GitHub Actions. **Um único arquivo CMD distribuível**, diagnóstico antes de mutações, logs isolados, ferramentas instaladas apenas sob confirmação explícita e sem tocar em outros projetos.

## Distribuição autossuficiente — apenas um CMD

- Baixe somente [`00_POLARIS_TUDO_EM_UM.cmd`](00_POLARIS_TUDO_EM_UM.cmd) na página GitHub (botão de download do arquivo). **Não é necessário baixar ZIP nem o PowerShell separado para abrir o menu.**
- O CMD carrega uma cópia do PowerShell 5.1 **embutida no próprio arquivo** em um `.ps1` temporário sob a pasta temporária do Windows e remove esse temporário ao concluir.
- `Polaris_Setup.ps1` permanece versionado como **fonte de manutenção**, não como dependência que o usuário precisa colocar ao lado do CMD. `generate_single_cmd.py` sincroniza o conteúdo embutido: `python generate_single_cmd.py`, ou `python generate_single_cmd.py --check`.
- Para somente verificar o PC, use **opção 1**. Para instalar, preparar e compilar, use **opção 6** (com confirmação de instalação, licenças e possíveis privilégios administrativos).
- Se qualquer opção do menu falhar, a falha é registrada e **o processo CMD termina com código diferente de zero**, mesmo que o usuário retorne ao menu e saia depois. Erro de compilação não deve ser confundido com resultado aprovado.
- **Não há garantia de build até executar em Windows real**; o CMD não substitui testes Android em emulador/celular.

## Projetos consultados como referência

| Projeto | Padrão identificado | Aplicação no instalador |
|---|---|---|
| CameraGuard | Um CMD único, helper PowerShell, evidências por sessão, hashes e estados de staging distintos de produção | CMD + PowerShell; log por sessão; falha fechada; nenhuma mudança em câmeras/gravações/banco instalado |
| MADEIRA (projeto distinto do Analista/Analista-AI) | Pipelines Python, controle de versões e validação determinística antes de promoção | Verificador de pré-requisitos e recusa de checkout divergente, nenhuma promoção ou alteração nesse projeto |
| Vai Quem Quer | Testes isolados, modo offline, validação por dispositivo e proibição de mexer em produção sem autorização | Build isolado e sem instalar APK; teste de dispositivo apenas como etapa posterior |
| Polaris | Yomotsu fixado, SQLDelight, Android/Gradle e trilha B01–B05 | Reutiliza `tools/local-android/polaris_local.py` e `scripts/r001/build_issue002.sh` existentes |

O **Projeto Viking** não foi identificado com segurança; não foi incluído como destino ou dependência. Projetos profissionais CAPEX e ForQuest são independentes do ambiente Android e não sofrerão alterações.

## Ações

- **1 — Diagnóstico:** confere Git, Git Bash, Python 3.10+, JDK 21 com javac, Android Studio, Android SDK, command-line tools, plataforma API 37.0, duas versões de Build Tools, dois NDKs, CMake, Platform Tools. Node.js e .NET aparecem como opcionais. Não baixa nem instala.
- **2 — Instalação assistida:** o usuário digita `SIM`; instala somente pacotes faltantes via `winget`. Para as Command-line Tools usa a versão oficial 22.0 para Windows (`commandlinetools-win-15859902_latest.zip`) e valida o SHA-256 publicado em https://developer.android.com/studio antes de extraí-la; aceita licenças interativamente antes de baixar os pacotes SDK exatos. Se faltar `winget`, recusa e orienta instalar `App Installer`.
- **3 — Preparação:** clona o Polaris na branch `r001/multisource-foundation`, verifica `origin` e preserva diretórios existentes. Clona Yomotsu no commit `0fb80c439ef816eeb50674f1b90af39918b176d8`, sem reset.
- **4 — Build:** inicializa JDK/SDK somente no processo local, cria shim Python3 somente sob `PolarisDev`, reutiliza o orquestrador Python existente, que executa baseline, aplica Spike-001 em worktree separado, gera SQLDelight, verifica migração 14 e gera APKs e evidências.
- **5 — Outros projetos:** apenas checa a presença de Python, Node e `dotnet`, sem instalar dependências desses projetos.
- **6 — Tudo do Polaris:** diagnóstico inicial → instalação assistida → novo diagnóstico → preparação → build, após consentimento explícito. Não instala APK nem executa os cenários B01–B05 automaticamente.
- **7 — Ferramentas gerais opcionais:** instala Node.js LTS e SDK .NET 8 se ausentes, com confirmação. O CameraGuard fixa a versão 8.0.425 separadamente; a instalação genérica não substitui esse SDK nem executa código do projeto.

## Convenções e segurança

- Local padrão: `%USERPROFILE%\PolarisDev`.
- `PolarisLocal\Yomotsu-pinned` e `PolarisLocal\evidence\issue002-*` são áreas separadas.
- Logs são salvos em `PolarisDev\relatorios\polaris-YYYYMMDD-HHMMSS-<id>.log` e `.json` (diagnóstico estruturado).
- Preserva `JAVA_HOME` e `ANDROID_HOME` permanentes do usuário: configura-os somente no processo de execução para evitar quebrar CameraGuard/Analista e outras IDEs.
- Não executa `git reset --hard`, não faz `git clean`, não altera pastas preexistentes de terceiros, não toca em imagens, gravações, bancos SQLite de usuário ou instalação no Android.
- A ferramenta não faz upgrade indiscriminado de softwares já instalados.
- Requer rede para instalações iniciais e Gradle; **não usa os minutos do GitHub Actions**.
- Por segurança, o comando `check` apenas cria arquivo de log local; não modifica instalações.
- Se o download oficial Google divergir do SHA-256 publicado ou a licença for rejeitada, a operação é interrompida. A versão 22.0 de Command-line Tools permanece fixada até uma atualização deliberada de URL e hash.
- A etapa B01–B05 com fontes reais e leitura de capítulos só pode ser declarada concluída depois de testes manuais/instrumentados em um Android real/emulador.

## Compatibilidade conhecida

Foi preparado para **Windows PowerShell 5.1**, que normalmente acompanha Windows 10/11. A versão exata e a disponibilidade dos pacotes winget dependem do sistema e da rede do operador. O SDK do Yomotsu exige a plataforma publicada como `platforms;android-37.0` para API 37, Build Tools 36.0.0 e 37.0.0, NDKs 29.0.14206865 e 28.2.13676358, CMake 3.22.1 e JDK 21.

**Validação deste pacote:** testes estáticos locais do conteúdo e dos invariantes de segurança. A interface gráfica/CMD, instalação winget, sdkmanager, compilação Android, APK e testes de dispositivo **não** foram executados em Windows neste ambiente. Os resultados do diagnóstico do PC são a próxima evidência obrigatória.

## Correção de compatibilidade Android 17 — 22/10/2026

- O pacote oficial do SDK correspondente à API 37 é `platforms;android-37.0`, e não `platforms;android-37`. O instalador utiliza o ID exato e `--channel=3` para permitir a descoberta das versões publicadas, sem atualizar pacotes indiscriminadamente.
- O pós-instalação verifica **todos** os diretórios exatos e seus `source.properties`. Uma falha de download ou aviso com retorno 0 não libera a compilação.
- O verificador Python local também exige `platforms/android-37.0`.
- O Yomotsu fixado define `compileSdk=37` na Gradle DSL. O novo pacote pode revelar uma incompatibilidade Gradle/AGP no build real; isso será tratado conforme evidências concretas, sem modificar ou sobrescrever o checkout base de referência.
- Evidência fornecida pelo operador: Command-line Tools instaladas, 8/8 licenças aceitas, falha no antigo identificador `platforms;android-37` antes do build.


## FIX6 — Sincronização Git e transcrição de execução (23/10/2026)

- Ao preparar e compilar, o CMD verifica a pasta `%USERPROFILE%\PolarisDev\Polaris`. Se já existir, valida a branch, o repositório de origem e a ausência de modificações locais. Em seguida consulta a branch GitHub com `git fetch` e só avança por `git merge --ff-only FETCH_HEAD` quando o commit local é ancestral do remoto. Se houver divergência ou modificações (inclusive arquivos não versionados), interrompe sem `git reset`, `git clean` ou `git rebase`.
- Além do `.json` e do `.log` do instalador, tenta criar `polaris-<sessão>.transcript.txt` para registrar as saídas de `winget`, `sdkmanager`, `git` e ferramentas de compilação exibidas no console. Caso a transcrição não seja compatível com o host, avisa o operador e mantém os relatórios existentes.
- O arquivo de transcrição pode registrar caminhos de usuário e informações do ambiente. Revise antes de compartilhar.
- Continuam pendentes a conclusão real da instalação do SDK e o build de APK em Windows; nenhuma validação de Android foi presumida.

## FIX7 — Build repetivel e APKs auditaveis (23/10/2026)

- O checkout `%USERPROFILE%\PolarisDev\PolarisLocal\Yomotsu-pinned` fica como **fonte imutavel**, sempre no commit `0fb80c439ef816eeb50674f1b90af39918b176d8` e sem alteracoes.
- Cada nova tentativa de build cria dois Git worktrees isolados na nova pasta de evidencias: `baseline-yomotsu` e `patched-yomotsu`. Apenas nessas copias sao gravadas imagens de branding, artefatos Gradle e o patch Spike-001.
- O script nao cria as pastas sobre evidencias preexistentes e recusa alterar um checkout pinado que ja esteja sujo. Isso evita a falha de uma segunda execucao provocada por arquivos de branding deixados no original.
- Em caso de sucesso, o relatorio `apks/SHA256SUMS.txt` registra o SHA-256 de cada APK baseline e Spike-001; a checagem final exige o Yomotsu pinado limpo.
- **Atencao:** se o Yomotsu original ja foi modificado por uma execucao antiga, o configurador interrompe para proteger esses arquivos. A nova rotina nao apaga nem corrige silenciosamente essa situacao.
- Esta correcao reside no repositorio GitHub e e sincronizada automaticamente pelo **CMD FIX6** ao preparar o Polaris, quando a copia local nao possui alteracoes ou commits divergentes.
- Os testes de contrato e de isolamento usam ambiente Python/Git local e **nao** comprovam APK ou comportamento de fontes Android em celular/emulador.


## FIX8 — checkout local modificado, sem perder arquivos (23/10/2026)

- Uma execução real do Windows retornou `Checkout Polaris tem alteracoes locais; sincronizacao bloqueada` ao selecionar 4. O bloqueio da FIX6 protegia os arquivos do usuario, mas impedia o primeiro APK.
- A FIX8 **mantém a pasta original do usuario intocada**, exibe e registra seu `git status --porcelain` e, quando existem alteracoes locais no checkout principal `PolarisDev\\Polaris`, cria uma **nova cópia limpa, isolada, em `PolarisDev\\PolarisBuildCopies\\checkout-<data>-<id>`** com `git clone` da branch oficial.
- O clone novo é validado quanto a branch, origin, SHA de commit e ausência de alterações antes de usar os scripts. Não usa `git reset`, `git clean`, `git stash` ou `git rebase` na pasta original. Se o clone falhar, o build para sem destruir nenhum arquivo.
- O processo define `PYTHONDONTWRITEBYTECODE=1` apenas para a sessão para evitar criar novas pastas `__pycache__` de testes Python.
- Quando o checkout principal estiver limpo, a atualização por fast-forward da FIX6 continua valendo. Clones isolados são preservados como evidência e podem ocupar espaço; não há limpeza automática.
- A FIX8 está incorporada no **mesmo arquivo CMD** e precisa sincronizar do Drive antes de executar a opção 4. O primeiro build Gradle e o teste real de Windows com checkout modificado continuam pendentes.

## EMULADOR A01 / A02 — Android Studio (23/10/2026)

- O **mesmo CMD** inclui a opcao **8 — EMULAR Yomotsu original (A01)** e **9 — EMULAR Polaris Spike-001 (A02)**, ambas com confirmacao explicita e somente para dispositivo virtual dedicado `Polaris_R001_API35_x64`.
- O driver `tools/local-android/polaris_emulator.py` e baixado pelo checkout oficial automaticamente via `Ensure-PolarisCheckout`, sem segundo CMD nem download manual. Utiliza Android 15 (API 35), sistema `google_apis;x86_64`, **Android Emulator** e ferramentas oficiais do Android SDK. O SDK de compilacao API 37.0 continua intocado.
- Requer computador Windows x64 com virtualizacao de CPU e **Windows Hypervisor Platform (WHPX)** habilitada. Se faltarem, imprime diagnostico; **nao** altera BIOS nem recursos do Windows e nao reinicia o PC. Android ARM64 requer preparacao via Device Manager, nao instala a imagem x86_64 incorreta.
- O Android Studio Device Manager mostra o AVD criado pelo comando `avdmanager`, com dados em `%USERPROFILE%\\PolarisDev\\emulador`. Se um AVD com o mesmo nome ja existir sem marcador de propriedade, o script **recusa sobrescrever**. Nao usa `-wipe-data`, `adb uninstall`, device serial generico ou aparelho fisico.
- O driver seleciona somente builds com `build-status.txt` aprovado, exatamente um APK original e um Spike-001 e `apks/SHA256SUMS.txt` com hashes conferidos. Conecta-se exclusivamente ao serial `emulator-XXXX` cujo nome AVD retorna exatamente `Polaris_R001_API35_x64`.
- Opcao **8**: prepara AVD, verifica aceleracao de hardware, instala e tenta abrir o **APK original**. Observe visualmente a tela e salve a comprovacao de A01; a entrega do comando de abertura **nao** prova renderizacao real. A opcao **9** so deve ser executada **depois** da conferencia de A01; instala a versao Spike-001 sobre a baseline **no banco exclusivo do emulador** e solicita a abertura para teste A02.
- Evidencias: `%USERPROFILE%\\PolarisDev\\relatorios\\emulador-<fase>-<sessao>\\result.json` marcado `INSTALLED_AND_LAUNCH_REQUESTED_NOT_VISUALLY_VERIFIED` e logs de inicializacao do emulador em `PolarisDev\\emulador`. Os testes A01/A02 e B01–B05 exigem confirmacao visual e uso de fontes reais; **nenhum PASS automatico de leitor**.
- A opcao 6 permanece so diagnostico/instalacao/build, sem dispositivos. O PR #1 continua Draft e backup v2 permanece bloqueado.
- Fonte de seguranca: Android Developers, guias `avdmanager`, `emulator -accel-check` e Windows WHPX.


## Comparacao lado a lado e persistencia — 25/10/2026

- Nova **opcao 10** do CMD: inicia dois emuladores Android 15 API35 x86_64 independentes, `Polaris_R001_Yomotsu_API35_x64` e `Polaris_R001_Spike001_API35_x64`. O usuario pode posicionar as duas janelas lado a lado usando Win+seta esquerda/direita. O programa nao modifica a posicao de outras janelas.
- **Opcao 8** abre somente o AVD original; **opcao 9** abre somente o AVD Polaris; ambas mantem as bibliotecas e preferencias distintas. Nao se substituem mais no mesmo AVD.
- Dados de aplicativos, configuracoes, extensoes instaladas, leituras e bibliotecas ficam nos discos virtuais separados `%USERPROFILE%\PolarisDev\emulador\avd\<AVD>.avd` e persistem depois de fechar normalmente. Sem `-wipe-data`, `-read-only` ou limpeza automatica. Ao reinstalar APK com `adb install -r`, os dados sao preservados se a assinatura for compativel; se nao for, falha sem desinstalar.
- Os repositorios e credenciais **nao sao sincronizados automaticamente entre AVDs**: configure individualmente dentro dos aplicativos. Uma planilha JSON de comparacao vazia e salva no relatorio para registro de B01–B05 sem inventar resultados. Manter configuracoes no disco virtual nao significa backup externo; fazer copia somente com AVD fechado e proteja eventuais credenciais.
- **FIX do seletor APK:** upstream Yomotsu `app/build.gradle.kts` define splits ABI armeabi-v7a, arm64-v8a, x86, x86_64, universal. A versao anterior do driver exigia `len(apks)==1` e retornava 'Nao encontrei build completo' mesmo quando Gradle havia terminado com sucesso. Agora ele confere SHA256 de **todos** os APKs do manifesto e seleciona exatamente o x86_64 (ou o universal como fallback deterministico). Nenhum rebuild e exigido.
- AVD de comparacao pode demandar RAM alta (recomendavel pelo menos 16 GB); VM acceleration WHPX/VT-x ou AMD-V precisa estar habilitada. Um pedido de abertura do aplicativo nao prova funcionalidade real, por isso resultados A01, A02 e B01–B05 continuam PENDENTES ate execucao e verificacao visual do usuario.
- Os 16 testes Python locais validaram selecao por arquitetura, manifesto, isolamento, dados persistentes, alvo ADB e relatorio sem resultados inventados. Emulacao real no Windows ainda nao validada.


## Testes automaticos SEM CONFIGURAR FONTES — 25/10/2026

Nova **opcao 11** do mesmo CMD: testes de observacao dos dois AVDs abertos, SEM adicionar repositorios, completar onboarding, alterar preferencias ou reiniciar o aplicativo. Ela exige a confirmacao do usuario, recupera o script `tools/local-android/polaris_smoke.py` via checkout Polaris no GitHub, confere a identidade exata dos AVDs e inspeciona ADB `getprop`, `pm path`, `pidof`, `dumpsys window`, `dumpsys activity activities`, e apenas eventos `AndroidRuntime:E` recentes. Captura PNG local com `adb exec-out screencap -p`. Nenhum `adb install`, `pm clear`, `input tap`, `force-stop`, `logcat -c` ou alteracao de dados do emulador.

O relatorio fica em `%USERPROFILE%\PolarisDev\relatorios\smoke-A01-A02-<data>-<id>\`, como `report.html` (duas capturas lado a lado), `report.json`, `baseline.png`, `spike001.png`. As capturas podem registrar informacoes privadas e **NAO sao enviadas automaticamente ao Drive ou GitHub**. Um crash encontrado em historico `logcat` e so aviso, nao prova crash atual; a inspecao de primeiro plano nao prova todas as funcionalidades do leitor. Vereditos referem-se apenas ao diagnostico, nunca a PASS dos testes B01-B05.

Uso: abrir os dois emuladores com a opcao 10, deixar ambos na tela inicial, executar **11**. A opcao 11 NAO recompila APK, NAO instala APK, NAO reconfigura fontes. O estado do assistente de boas-vindas e preservado para que o usuario complete depois. Nao usar Wipe Data quando configurar fontes.

Fonte oficial para ADB e screencap: https://developer.android.com/tools/adb


## Revisão de tradução — 02/11/2026

O CMD atualizado inclui **12** (comparação automática de original/tradução e registro salvo do capítulo aberto em faixa longa), **13** (1080 × 1920, 420 dpi) e **14** (restaurar a tela anterior). Essas opções atuam somente no emulador Polaris criado pelo assistente. Compile o build de diagnóstico pela opção 4 e instale pela 9 antes de usar a coleta. Abra e traduza o capítulo primeiro; a coleta não inicia tradução nem envia arquivos. O relatório e o ZIP de um quadro escolhido ficam em `PolarisDev/relatorios`.

A coleta começa na posição atual e tem limite de 60 quadros; não certifica a qualidade ou cobertura integral do capítulo. Consulte [o procedimento e suas limitações](../../docs/REVISAO_TRADUCAO_FAIXA_LONGA.md). Não há nova Release publicada nesta revisão.


### Full HD automático e foco no ML Kit

As opções **9** e **10** agora preparam o emulador Polaris em 1080 × 1920 / 420 dpi automaticamente antes de abrir o leitor. A instância existente é reutilizada; não é necessário usar a opção 13. Essa opção permanece para reaplicar o ajuste manualmente. A 14 restaura os overrides salvos; uma nova abertura pelo CMD prepara novamente o padrão Full HD. O AVD original Yomotsu não é modificado por esse ajuste. A resolução da partida usa `-skin 1080x1920`; a densidade é aplicada por ADB após o boot porque `-dpi-device` é obsoleto e ignorado pelo emulador atual.

Gemini fica fora da rodada atual. O teste de OCR e tradução offline não exige API. Consulte a [pesquisa sobre OCR/ML Kit](../../docs/PESQUISA_OCR_MLKIT_2026_11_02.md).
