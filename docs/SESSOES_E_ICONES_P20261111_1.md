# Sessões isoladas e ícones ilustrados — P20261111.1

Beta.11/código112 em desenvolvimento, posterior a 7a929ab. A beta.10 pública permanece inalterada. [Artes e regras cosméticas](../design/polaris-guardians/20261111/README.md) e [evidências desta etapa](../integration/sessions-icons/20261111/README.md).

## Ícones como recompensa

O original e os três alternativos agora usam imagens ilustradas geradas para o Polaris: coruja, raposa boreal, dragão e lobo estelar. Aurora libera com 900 pontos, Órbita com 4.500 e Constelação com 9.000. A seleção não gasta pontos, os desbloqueios são mantidos e a escolha antiga/restaurada é preservada. O original permanece disponível. Temas e funções de leitura não dependem dessa progressão.

A regra é aplicada no gerenciador do Android e na interface, evitando desativar o launcher ao tentar selecionar uma opção bloqueada. A migração conserva os nomes dos aliases e o registro da atividade principal. Os campos de progresso permanecem os mesmos; os ícones liberados usam uma preferência StringSet adicional comum, sem alterar o Protobuf do backup.

## Continuidade da sessão HTTP

O intermediário de rede e os downloads de imagens agora compartilham cookies apenas dentro do pacote e identidade de assinatura verificados. Cookies de sessão sobrevivem à troca do processo de extensão durante a execução do Polaris; cookies explicitamente persistentes pelo servidor são recuperados após reiniciar o processo do app. Cookies temporários não são gravados em disco. Domínio, caminho, Secure, HttpOnly e validade são preservados; caminhos mais específicos precedem o cookie da raiz. Respostas sucessivas mesclam nomes/caminhos, em vez de apagar os outros cookies do host.

O armazenamento privado usa AES-GCM com chave do Android Keystore e a identidade da extensão como dados autenticados. Copiar o conteúdo cifrado para outra identidade não concede uma sessão. Há limites de quantidade, tamanho individual e bytes totais; entradas vencidas são removidas. Se o armazenamento protegido falhar, a sessão em memória continua disponível e a tela informa a limitação.

Isso não importa cookies do navegador nem modifica o CookieManager global. As respostas do broker continuam sem expor Set-Cookie ao worker. Os arquivos protegidos e a chave não integram o backup de biblioteca nem o exportador de preferências de fontes. O formato nativo de obras, capítulos, progresso e configurações continua igual.

## Limpar sessão

A tela da fonte isolada oferece a ação de limpar sua sessão, inclusive quando não há configurações próprias da extensão. A confirmação explica que a limpeza abrange as fontes daquele pacote e preserva outras extensões, navegação, favoritos e capítulos. Clientes antigos são revogados para cookies; uma resposta que já estava em trânsito não pode restaurar a sessão removida. As credenciais configuradas em campos da fonte não são apagadas por essa ação, e um provedor pode autenticar novamente a partir delas. A limpeza é local; não revoga sessões no servidor.

## O que esta etapa não conclui

A persistência HTTP não implementa todo login por navegador, Cloudflare, OAuth ou controles personalizados. Não habilita compatibilidade automaticamente. Fontes que dependem desses fluxos ainda precisam de adaptação ou da opção explícita de compatibilidade, fora da sandbox. Acesso a fontes reais, contas reais, ARM32/ARM64 e ida/volta por banco/interface de outros leitores continuam pendentes.

A pesquisa oficial confirmou `WebViewFeature.MULTI_PROFILE` e `Profile.getCookieManager()` no AndroidX WebKit, já presente no projeto. Essa é a base candidata para perfis de autenticação próprios. O suporte deve ser verificado no WebView instalado, além de validar navegação, rede, sincronização e limpeza; cookies do perfil global não devem ser copiados implicitamente. Este documento não declara esse navegador integrado.

Referências consultadas: [Profile](https://developer.android.com/reference/androidx/webkit/Profile) e [WebViewFeature.MULTI_PROFILE](https://developer.android.com/reference/androidx/webkit/WebViewFeature#MULTI_PROFILE).
