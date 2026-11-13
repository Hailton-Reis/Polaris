# Ajustes numéricos isolados — P20261113.4

Desenvolvimento da beta.11/código 112. Não é lançamento nem substitui automaticamente o APK interno P20261113.3 já disponibilizado.

Extensões HTTP isoladas passam a oferecer SeekBarPreference padrão na tela de configurações. O worker descreve chave, título, mínimo, máximo, incremento, valor e flags do controle; o host cria seu próprio widget AndroidX. Objetos, subclasses e callbacks da extensão permanecem no worker. A gravação passa pelo mesmo fluxo assíncrono e separado por pacote/assinatura. O host envia um inteiro ao soltar a barra, sem abrir uma sessão por cada movimento.

A validação do contrato foi extraída para SandboxPreferenceSchema, sem dependências Android, e é compartilhada pela leitura dos descritores, alteração e importação explícita. Aceita faixas negativas e fixas; exige mínimo≤valor≤máximo, incremento válido e amplitude de no máximo 1.000.000. Calcula a amplitude em Long para rejeitar overflow de Int. Não converte texto, Long, float, booleano ou coleção em inteiro.

O incremento conserva o comportamento AndroidX: controla ajustes pelo teclado, sem proibir valores intermediários produzidos pelo toque. A montagem do widget considera que AndroidX limita cada extremo contra o extremo oposto já configurado, inclusive em faixas inteiramente negativas ou acima do máximo padrão.

Limites, incremento e tipo integram a identificação estrutural da tela. Se a fonte reconstruir opções diferentes, um formulário antigo é recusado antes de callbacks/gravação. Mudança de valor, resumo, disponibilidade ou visibilidade não troca esse identificador; o worker ainda confere o estado atual de habilitação/visibilidade para aceitar uma alteração. Ações personalizadas e intents continuam indisponíveis, sem fallback automático à compatibilidade.

A importação explícita de configurações antigas reconhece os controles numéricos, mantém Int no armazenamento/backup e recusa valores fora da faixa antes de gravar o lote. Não modifica o arquivo nativo original. Callbacks continuam com a semântica existente: false impede a gravação padrão, mas gravações próprias do listener no armazenamento isolado são preservadas.

## Validação e limites

Doze testes JVM cobrem contrato, limites, tipos, overflow, flags, atualização estrutural e campos duplicados/desconhecidos. A fixture sintética foi compilada como DEX com a Source API atual e acrescenta NumericSource, sem contas ou provedores externos. Três cenários de instrumentação cobrem persistência/callback no UID isolado, limites dinâmicos com formulário antigo e importação sem sobrescrever dados inválidos.

O resultado da suíte completa e compilação fica em [evidências](../integration/sandbox-numeric/20261113/README.md). O ADB foi consultado e não encontrou dispositivo/emulador conectado. Não declarar os três cenários Android como executados nem concluir suporte genérico a fontes reais, controles personalizados, carregamento de opções por clique, OAuth/Cloudflare ou novels. [Checklist geral](BETA11_CHECKLIST.md).
