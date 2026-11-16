# Listas dinâmicas isoladas — P20261113.5

Desenvolvimento da beta.11/código 112. Configurações de fontes isoladas podem preparar listas simples/múltiplas ao abrir, aguardar o worker e apresentar um diálogo do próprio Polaris. A opção é validada novamente no worker ao salvar; uma mudança nas opções exige reabrir a configuração.

Esta primeira etapa aceita preparação síncrona, com retorno false e sem mudança no snapshot das preferências. Consultas GET/HEAD são permitidas; POST não é oferecido nessa operação. A preparação roda uma vez ao abrir e novamente no worker novo de gravação para reconstruir opções e callbacks, podendo repetir consultas e atualizar cookies HTTP. Não se promete ausência de efeitos remotos para GET/HEAD.

Callbacks que consomem uma ação, alteram preferências na preparação, dependem de preenchimento assíncrono ou abrem interfaces próprias permanecem indisponíveis. Não há carregamento de classes da extensão no host nem troca automática para compatibilidade. A importação legada preserva seleções dinâmicas no arquivo original até que as opções sejam preparadas e escolhidas; backups conservam chaves/tipos.

App e instrumentação compilados, 845 testes do app aprovados (12 novos), quatro testes de overlay e 16 de empacotamento. Seis cenários Android compilados aguardam aparelho/emulador. O conjunto com 85 testes de domain já aprovados soma 930, sem falhas/skips; domain não foi reexecutado. [Evidências detalhadas](../integration/sandbox-dynamic/20261113/README.md).

Não foi gerado outro APK nesta etapa. O arquivo enviado antes continua P20261113.3; este trabalho entrará no próximo snapshot. [Pendências da beta](BETA11_CHECKLIST.md).
