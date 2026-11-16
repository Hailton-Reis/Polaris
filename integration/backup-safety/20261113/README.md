# Backups — P20261113.2

Candidata da beta.11/código112, continuação do rascunho PR12. Não publica APK nem altera a beta.10.

A retenção reconhecia como gerados pelo app nomes com datas impossíveis (por exemplo, 30 de fevereiro). Uma cópia legível com esse nome podia entrar na lista de exclusão automática. O teste anterior à correção reproduziu duas falhas: aceitação do nome e seleção para exclusão.

BackupRetention agora exige data/hora reais, com parsing estrito e validação de calendário independente do fuso atual. Nomes históricos por minuto e nomes atuais com segundos/milissegundos/UUID permanecem válidos. Arquivos estranhos, incompletos ou não verificados continuam preservados. Não houve alteração de Protobuf, SQL, dados ou arquivos de usuário nesta rodada.

## Validação executada

- **43/43 testes JVM focados, nenhum skip:** 26 anteriores de sessão/importação; nove existentes de escrita, leitura de conferência, gzip truncado/corrompido, falhas e cancelamento; dois existentes de namespaces de fontes; seis novos de retenção.
- Antes da correção: 41 passaram e dois falharam. Depois: 43 passaram.
- Quatro testes de aplicação do overlay e nove de empacotamento passaram.
- O runner compila as classes de produção e testes reais. O núcleo CookieBank/Codec é extraído sem modificação do arquivo Android. Não simula aprovação de interface/banco.

O comando reproduzível é scripts/extensions/test_sandbox_session_host.py com checkout aplicado, bibliotecas do compilador e as dependências documentadas. Os hashes dos arquivos compilados estão em provenance.json; RESULT.json resume o alcance.

## O que continua aberto

A tentativa de compilação completa voltou a falhar no Google Maven (HTTP503 de appcompat-resources:1.6.1). Um acesso inicial por curl retornou200, mas a tentativa Gradle e as verificações subsequentes voltaram a503. Isso não é compilação aprovada. Não há novo APK, ensaio Android desta candidata, aceite ARM nem ida/volta por interface/banco de leitores externos.

A revisão também corrige o aviso de login para falar dos cookies transferidos. As callbacks de WebView não garantem mediação de todos os redirecionamentos/canais de rede. O login continua experimental, pendente de validação Android e de fontes reais.
