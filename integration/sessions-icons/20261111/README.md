# Sessões HTTP e ícones ilustrados — P20261111.1

Beta.11/código 112 em desenvolvimento, posterior a 7a929ab. A beta.10 pública permanece igual. [Comportamento e limites](../../../docs/SESSOES_E_ICONES_P20261111_1.md) e [originais e proveniência das artes](../../../design/polaris-guardians/20261111/README.md).

## Implementação

Quatro imagens geradas substituem os símbolos geométricos: coruja original, raposa Aurora, dragão Órbita e lobo Constelação. Os recursos Android somam 366.210 bytes. As alternativas liberam com 900/4.500/9.000 pontos de leitura, sem gasto; escolhas anteriores/restauradas e desbloqueios são mantidos. Temas e funções do leitor permanecem disponíveis. O gerenciador verifica a recompensa antes de mudar aliases; a atividade principal e links continuam registrados.

O intermediário HTTP e o cliente de imagens usam um banco de cookies por pacote/assinatura verificados. Cookies persistentes usam AES-GCM com chave do Android Keystore e identidade autenticada; cookies temporários ficam na memória. Não há cópia do CookieManager global, acesso aos cookies de outra extensão, nem exportação de cookies pelo backup da biblioteca. A ação confirmada de limpar sessão revoga clientes antigos e respostas em trânsito. As credenciais configuradas em campos da fonte são mantidas.

A pesquisa de autenticação consultou a documentação oficial de [Profile](https://developer.android.com/reference/androidx/webkit/Profile) e [MULTI_PROFILE](https://developer.android.com/reference/androidx/webkit/WebViewFeature#MULTI_PROFILE). A dependência WebKit já existente oferece uma base candidata, condicionada ao suporte do WebView instalado. O login por perfil de navegador não está implementado nesta etapa.

## Validação

- **872/872 testes JVM passaram**, mantendo os 858 anteriores e acrescentando 14 casos. Cobrem cookies persistentes/temporários, mesclagem, expiração, domínio, caminho, revogação após limpeza, limites em bytes codificados, falha de armazenamento, codec e desbloqueios de ícones.
- **13 controles de overlay/empacotamento passaram.** A aplicação limpa e a variação CRLF conferem os hashes das imagens geradas e da fixture DEX binária. Os 394 caminhos cumulativos, incluindo cinco exclusões de arquivos upstream, correspondem aos fontes compilados.
- **35/35 testes Android passaram em API26/x86_64**, em 242,404 segundos: os 29 anteriores, cinco casos de cookies e um de bloqueio/retenção de recompensas. Exercitam Android Keystore real, asset de sufixos públicos, cifragem autenticada, armazenamento persistente sem cookies temporários, rejeição de cópia entre identidades, revogação dos clientes de imagens e limpeza confirmada pela interface sem apagar outra extensão. Os quatro aliases renderizam suas imagens pelo PackageManager, mantêm um único atalho e preservam a atividade principal/links. A prova registra os hashes dos APKs e do patch antes de executar.
- Nenhuma dependência, modelo OCR ou esquema SQL/Protobuf novo. A consulta anterior de vulnerabilidades não foi repetida. Os manifestos de produção/debug e entradas de dependências são iguais ao checkpoint anterior.

[Comparação JVM](unit-comparison.json), [fontes compilados](compiled-overlay.json), [diferença de escopo](source-delta.json), [artefatos de componentes](artifacts.json) e [hashes das evidências](SHA256SUMS.txt).

## Reprodução e ambiente

Aplicar a pilha de overlays sobre o upstream fixado usando os scripts do projeto. Usar JDK21/SDK37 e executar `:domain:testDebugUnitTest :data:testDebugUnitTest :source-api:testDebugUnitTest :app:testDebugUnitTest :app:assembleDebug :app:assembleDebugAndroidTest`, com os dois init scripts arquivados. O init de runtime seleciona x86_64 e o runner de componentes; não serve para distribuição em celulares. A constante BUILD_TIME do candidato é fixada para reprodução; horários reais de execução ficam nos registros.

Os APKs de componentes ficam fora do Git e seus hashes são registrados antes da instrumentação. A fixture DEX é a mesma do checkpoint P20261110.3. Os originais PNG são preservados separadamente dos recursos WebP do aplicativo. A codificação só redimensiona/comprime a imagem gerada.

O primeiro ensaio JVM corrigiu imports JUnit4 em um módulo configurado para Jupiter. O caso de sufixo público depende do inicializador/asset Android do OkHttp e foi levado à instrumentação real, sem remover a proteção de produção. A suíte final acrescenta ainda a precedência de caminhos específicos.

A VM apresentou ANR do System UI durante boot/instalação; a mensagem foi inspecionada e fechada antes da instrumentação, aguardando foco no Launcher. Nenhuma recuperação de interface ocorreu durante os testes. Não foram limpos dados do app/guest nem desativados SELinux/verificação de APK. [Ambiente](runtime-environment.json).

## Conferência visual

Os quatro [ícones nativos](preview/icons/) preservam faces, livros e estrelas, sem cortes na máscara adaptativa retangular arredondada desta VM. A [seleção de aparência](preview/appearance/appearance-aurora-light.png) mostra quatro ilustrações, Aurora selecionada, Órbita liberada e Constelação bloqueada em 4.500 pontos. A Jornada Boreal atualiza a explicação das recompensas; o exemplo Âmbar usa fonte ampliada. As capturas de configurações mantêm o interruptor visível antes/depois do toque e escondem o valor privado. [Inspeção](ui-review.json). Android recente/ícones temáticos e aparelhos físicos permanecem fora desse aceite.

[Resultado estruturado](TEST_RESULTS.json), [instrumentação](android-final.log) e [proveniência](android-run.json).

## Limites

A prova usa componentes em VM API26/x86_64. Não certifica inicialização completa, desempenho ARM, fontes ou contas reais, browser login/Cloudflare/OAuth, controles personalizados, novels, biblioteca pessoal, fluxo completo leitor/downloads nem ida/volta por banco/interface de Mihon/Tachiyomi. A etapa HTTP não equivale à conclusão da autenticação WebView. Compatibilidade fora da sandbox continua opcional e explícita. Preservar o backup original.
