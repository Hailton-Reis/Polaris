# Cookies por caminho no login — P20261113.6

Continuação da beta.11/código 112. O login passa a levar ao perfil exclusivo também os cookies já existentes em caminhos como /account, mesmo abrindo na raiz. Cookies de domínio pai são copiados somente para o host escolhido, com atributos preservados. Colisões impedem a cópia sem substituir silenciosamente uma credencial.

A gravação consulta localmente os caminhos iniciais, raiz e até 32 páginas, sem query/fragmento e sem pedidos de rede. Uma observação parcial não apaga cookies de caminhos não consultados; uma observação contraditória aborta antes de gravar. Snapshot HTTP congelado, revogação e proteção contra atualização concorrente continuam. São até 97 consultas locais, 64 cookies e 32KiB finais; cookies novos em caminhos nunca observados continuam sem enumeração.

App/instrumentação compilados; 861 testes do app passaram (16 novos), 63 focados, quatro de overlay e 16 de empacotamento. Domain mantém 85 resultados anteriores UP-TO-DATE, total 946 sem falhas/skips. Três cenários Android compilados aguardam execução; o teste de perfil exige APIs WebView atuais. [Evidências](../integration/login-cookies/20261113/README.md).

Isso não conclui login em fontes reais, OAuth/Cloudflare ou validação em aparelho. O navegador segue fora do worker, sem mediação completa de toda a rede. Não há outro APK nesta rodada; o arquivo já enviado permanece P20261113.3. [Checklist](BETA11_CHECKLIST.md).
