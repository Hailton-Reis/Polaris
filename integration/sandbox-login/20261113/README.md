# P20261113.1 — candidata em validação

- 26 testes JVM focados passaram: dez novos de ponte do navegador, dez existentes de CookieBank e seis novos de espaço de importação.
- Quatro testes de aplicação do overlay passaram: aplicação/idempotência, CRLF, recusa de drift e gates de pré-requisito/migração.
- Nove testes de empacotamento passaram.

O ensaio JVM focado compila os arquivos de produção BrowserCookieSession, SandboxNetworkPolicy
e DocumentImportSpace, e extrai sem modificação o núcleo RevocableCookieJar/CookieBank/CookieCodec
do arquivo de armazenamento Android. Usa OkHttp5.4.0, Okio3.18.1, Serialization1.11.0 e JUnit.
Não testa Keystore, WebView, atividade, manifesto, carregamento de fonte ou a aplicação completa.

A compilação Android completa foi tentada e repetida após preparar JDK21, SDK37 e NDK28.2. Ela parou em `:presentation-widget:generateDebugRFile`: Google Maven devolveu HTTP503 para `androidx.appcompat:appcompat-resources:1.6.1`. O acesso público direto ao mesmo POM e aos endereços oficiais alternativos confirmou o erro. Não houve compilação Kotlin completa do app. O ensaio adicional da atividade contra APIs isoladas também ficou sem dependências Lifecycle e não é contabilizado como aprovação. Nenhum resultado Android desta
revisão, aceite em ARM, login em provedor real ou versão para telefone é declarado por estes
testes. Os resultados 880/37 da revisão anterior não são uma execução desta candidata.
