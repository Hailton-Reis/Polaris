# Continuidade dos cookies de login — P20261113.6

Desenvolvimento da beta.11/código 112, sem outro APK ou lançamento. O APK interno enviado continua P20261113.3; não inclui as revisões .4/.5/.6.

## Problemas reproduzidos e correção

O navegador recebia só os cookies aplicáveis à URL inicial: sessões existentes em /account ou /api ficavam de fora quando o login começava na raiz. A cópia também conservava Domain do domínio pai, apesar de a tentativa de login selecionar um host. Agora a capacidade do host enumera os caminhos daquele host usando os checks de domínio/host-only/Secure do OkHttp; o browser recebe cópias host-only, preservando valor, caminho, HttpOnly, validade e Secure. A identidade original continua no snapshot para verificação de concorrência e remoção corretas. Não há importação do navegador global.

A cópia é inicializada uma única vez, sem rebase do snapshot HTTP. Colisões de nome/caminho que surgiriam ao restringir domínios são recusadas sem escolher arbitrariamente uma credencial. Capacidade revogada não pode iniciar outra cópia. Outros hosts e clientes posteriores à limpeza seguem separados.

O plano de consulta local ao CookieManager inclui raiz, caminhos dos cookies inicialmente copiados e até 32 páginas navegadas, removendo query/fragmento dos endereços. No máximo 97 URLs; essas consultas não navegam nem fazem pedidos de rede. Ao salvar, ausência só expira cookies que poderiam aparecer em uma das URLs consultadas. Um snapshot parcial da raiz não apaga silenciosamente a sessão /account. Cookies novos em caminhos que nunca foram consultados/inicializados continuam fora: não se trata de enumeração irrestrita da base WebView.

Observações contraditórias de valor/atributos ou domínios que colapsam em uma chave de host abortam a importação antes de escrever. Duplicatas idênticas, inclusive Max-Age, compartilham a primeira validade calculada; atributos equivalentes são aceitos. Os limites existentes de 64 cookies e 32KiB finais continuam, com contagem de observações e volume agregado limitados. Cookies particionados permanecem excluídos. A atividade confere o nome do perfil também antes de ler/gravar a sessão; a limpeza do teste só toca um perfil cujo nome confere.

## Validação

- Quatro novos casos reproduziram erros na implementação anterior: seed de domínio pai, captura contraditória, falta do caminho /account e exclusão indevida por snapshot não relacionado. Resultado vermelho: 47 passaram/quatro falharam. Depois da correção e dos demais casos novos, **63/63 focados passaram**, sem skips. O runner extrai o núcleo CookieBank sem alteração; não executa Keystore/WebView Android.
- Gradle real compilou app e instrumentação: BUILD SUCCESSFUL em 2min36s, 285 tarefas, 11 executadas. **861 testes do app executados e aprovados**, incluindo 16 novos; nenhum skip. Com 85 casos de domain já aprovados e UP-TO-DATE, relatórios somam 946/946. data/source-api NO-SOURCE. Nenhum dos 930 casos arquivados .5 desapareceu; 16 novos aprovaram, sem reexecutar a base antiga.
- Quatro verificações completas de overlay e 16 de empacotamento passaram. O guard não interrompeu o build: mínimo 511.082.496 bytes livres.
- Três cenários Android foram **compilados, não executados**: restauração cifrada de sessão por caminho, revogação de login já copiado e CookieManager real em perfil WebView exclusivo, com /account presente e domínio irmão vazio. O último depende de MULTI_PROFILE/GET_COOKIE_INFO e usa assume se o provedor não oferecer as APIs. ADB sem aparelho/emulador conectado nesta rodada; não registrar esse cenário como executado ou aprovado.

android-compile-unit.log e 161 relatórios XML originais em junit-reports.zip registram a suíte; unit-comparison.json e source-provenance.json vinculam contagens/fontes. Logs/proveniência vermelho/verde, overlay/packaging/ADB e SHA256SUMS estão preservados. Nada aqui contém credenciais reais, keystore ou senha.

## Pendências

Login/challenge com fontes reais e WebView de aparelho, provedores externos/OAuth/Cloudflare e aceites ARM continuam pendentes. O navegador continua superfície do host fora do worker e sua rede não é integralmente mediada pelo broker; esta correção não cria suporte genérico a OAuth nem autorização para outros domínios. Demais frentes no [checklist](../../../docs/BETA11_CHECKLIST.md).
