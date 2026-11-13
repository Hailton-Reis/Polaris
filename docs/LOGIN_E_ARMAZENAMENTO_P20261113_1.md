# Login e espaço de importação — P20261113.1

Candidata da beta.11/código112. Desenvolvimento sobre 6952e5e; sem publicação.

## Login inicial de fontes isoladas

Uma atividade interna, não exportada, recebe somente o ID da fonte e resolve o proxy
IsolatedHttpSource já verificado. Não recebe nome de perfil, credenciais ou URL arbitrária
por Intent. A fonte precisa estar fora de quarentena e usar HTTPS.

O navegador exige MULTI_PROFILE, GET_COOKIE_INFO e DELETE_BROWSING_DATA do WebView instalado.
A falta de suporte informa indisponibilidade; não abre o perfil global nem executa a extensão
em compatibilidade. Cada tentativa cria um perfil próprio antes de navegação ou scripts.
O usuário confirma o site e escolhe explicitamente Usar sessão. Voltar/cancelar não grava no
CookieBank. Os pontos de entrada WebView por fonte também encaminham proxies isolados a essa
atividade; a tela de configurações atualiza o estado ao retornar.

A navegação e os pedidos iniciais de recursos são conferidos contra a origem HTTPS selecionada. Essas callbacks não garantem controle de todos os redirecionamentos de subrecursos ou canais internos do Chromium. Arquivos/content URIs,
permissões de câmera/microfone/localização, terceiros, janelas extras e rede de service workers
não são habilitados. Não há ponte JavaScript para objetos do host. O navegador é uma superfície
interativa do host, **fora do worker isolado**; sua rede usa o WebView, não o intermediário HTTP
do worker. Os controles de origem não estabelecem pinagem de DNS nem garantem mediação de todo
canal do Chromium. Não tratar esta candidata como conclusão da sandbox ou suporte genérico a
Cloudflare/OAuth. Provedores que exigem outra origem ou CDN podem não funcionar nesta etapa.

A transferência lê atributos Set-Cookie do perfil escolhido, nunca CookieManager global nem
um Cookie header sem metadados. Preserva validade, Secure, HttpOnly e caminho. Cookies recebidos
ficam restritos ao host escolhido, sem ampliar autorização para sites irmãos. O snapshot cobre
a raiz e até 31 páginas visitadas; não enumera cookies de caminhos não visitados. Cookies
particionados não são convertidos em credenciais não particionadas. Campos e volumes são
limitados antes da gravação. Uma sessão limpa revoga também o cliente de uma janela de login
aberta. A limpeza não pode ser desfeita por uma resposta atrasada.

Ao fechar, o perfil recebe limpeza de cookies/dados de navegação e destruição da WebView.
A limpeza de perfil é assíncrona conforme o provedor. Perfis remanescentes de encerramento
abrupto são removidos na próxima tentativa, sem tocar no perfil padrão ou em outro login ativo.
Durante a tentativa os dados usam o armazenamento normal do WebView; só os cookies transferidos
seguem o armazenamento cifrado já existente. Não há promessa de apagamento físico imediato.
Falha antes de anexar o perfil nunca autoriza limpar o perfil padrão.

## Espaço de importação

A cópia temporária verifica o espaço do cache antes de cada bloco e mantém uma margem de
8 MiB, além do limite de 256 MiB por documento. Conserva o cancelamento e a limpeza temporária.
Para biblioteca baseada em arquivo, verifica também espaço para a segunda cópia no volume de
destino. Isso é uma verificação consultiva, não reserva: outro processo pode consumir espaço.
Provedores SAF podem não revelar capacidade; suas falhas de escrita continuam sendo tratadas
pelo fluxo existente. O original selecionado não é removido.

Deduplicação, reconciliação após publicação incompleta, otimização de materialização, medidas
de pico e aceite com provedores Android reais continuam pendentes.

## Validação

Ver [registro de evidências](../integration/sandbox-login/20261113/README.md).
Nenhum APK de telefone foi publicado. O [checklist da beta](BETA11_CHECKLIST.md) mantém as
outras frentes abertas.

## Continuação P20261113.2

A [revisão de backups](../integration/backup-safety/20261113/README.md) corrige o reconhecimento de nomes com datas impossíveis e amplia o ensaio JVM para 43 casos. O aviso de login passa a descrever o limite dos cookies transferidos, sem prometer mediação de toda a rede do WebView. O build Android continua bloqueado por HTTP503.
