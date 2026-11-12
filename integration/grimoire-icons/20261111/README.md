# Primeiro ensaio de grimórios — P20261111.2

Registro histórico do ensaio inicial: seis testes JVM e cinco Android passaram, mas a inspeção revelou névoa retangular no ícone original e motivou ajuste de escala. A versão refinada e as conquistas adicionais são verificadas na [revisão P20261112.1](../../grimoire-achievements/20261112/README.md). Os hashes e números abaixo correspondem ao primeiro ensaio, não ao candidato final.

Beta.11/código112 em desenvolvimento, posterior a fdc768e. A beta.10 pública permanece inalterada. [Artes e marcos](../../../design/polaris-grimoires/20261111/README.md), [comportamento e limites](../../../docs/ICONES_GRIMORIOS_P20261111_2.md).

## Escopo

Quatro imagens geradas substituem a coleção de guardiões: Grimório Polaris, trevo de três folhas, quatro folhas amado pela mana e cinco folhas com visual sombrio. As capas têm textura e detalhes pintados; as folhas centrais foram contadas visualmente. Os recursos de 512×512 somam 443.012 bytes.

Nomes e fundos acompanham a nova coleção. Os aliases/chaves de seleção e desbloqueio, marcos de 900/4.500/9.000 pontos, lógica de recompensa, assinatura, identificador, manifestos, biblioteca, cookies, extensões, OCR/tradução e esquemas SQL/Protobuf são preservados. A escolha antiga continua na mesma posição. Dez caminhos do overlay mudam; os outros 384, incluindo cinco exclusões já existentes, permanecem iguais. [Diferença de escopo](source-delta.json).

## Verificação

- Compilação dos APKs de componentes aprovada. [Log](assemble.log) e [hashes](artifacts.json).
- **6/6 testes JVM específicos passaram**, sem falhas/skips: os quatro casos existentes de recompensas e dois de troca/recuperação dos aliases. [Resultados](focused-JVM.json).
- **13 controles de overlay/empacotamento passaram**, incluindo aplicação limpa e CRLF. Os originais gerados e os recursos da aplicação têm os hashes conferidos.
- O APK contém as quatro imagens atuais com bytes/hashes iguais aos recursos gerados, comprovados por [inspeção do ZIP](packaged-artwork.json).
- **5/5 testes Android passaram no primeiro ensaio.** [Proveniência](initial-art-review/android-run.json), [log](initial-art-review/android-final.log) e [capturas iniciais](initial-art-review/). A inspeção não aprovou a névoa do ícone original; a correção segue na revisão posterior.

Os 872 testes JVM e 35 Android da [revisão anterior](../../sessions-icons/20261111/README.md) não foram repetidos integralmente nesta alteração visual; seus registros permanecem como linha de base. Esta etapa usa os testes existentes direcionados aos ícones e à aparência. Não acrescenta novos modelos, dependências ou esquema de backup.

## Reprodução e ambiente

Aplicar os overlays do projeto sobre o upstream fixado, com JDK21/SDK37. Usar os init scripts arquivados para `:app:assembleDebug :app:assembleDebugAndroidTest`; depois executar `:app:testDebugUnitTest --tests '*LauncherIcon*'`. O init de runtime seleciona x86_64 e o runner de componentes, sem servir para distribuição em celulares. Os testes Android selecionam `LauncherIconAndroidTest` e `PersonalizationPreviewAndroidTest` pelo `am instrument` do runner `eu.kanade.translation.recognizer.OcrComponentTestRunner`.

Os APKs ficam fora do Git. Seus hashes e o hash do patch são registrados antes da instrumentação. Os originais gerados são preservados separadamente das cópias WebP usadas pelo app. BUILD_TIME é fixado para reprodução; horários reais são registrados nas evidências.

## Limites

Esta é uma conferência de componentes em VM API26/x86_64. Não certifica inicialização completa, desempenho ARM, máscaras ou ícones temáticos em Android recente, fontes/contas reais nem todo o próximo beta. Login WebView, aceite físico, fluxo leitor/downloads e ida/volta por banco/interface de leitores externos seguem pendentes. Nenhuma nova versão para celulares foi publicada nesta etapa.
