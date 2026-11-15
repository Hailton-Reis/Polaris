# Ações locais de configurações — P20261114.3

Continuação da beta.11/código 112. Os testes pessoais do usuário ficam para a consolidação final. A publicação da versão no GitHub virá após concluir as pendências de implementação; esta revisão salva código no PR em rascunho, sem outro APK. Conta/login Google/nuvem permanecem adiados.

## Comportamento

O painel isolado passa a oferecer ações locais declaradas por uma Preference padrão, selecionável, com chave e listener explícito, sem Intent/fragment. Exemplos incluem redefinir opções ou limpar valores da própria fonte. Ao tocar, o Polaris pede confirmação; cancelar não solicita a execução. A tela fica bloqueada durante confirmação/execução para evitar submissões duplicadas.

O host envia somente chave/token do descritor. O worker reconstrói a tela, revalida tipo/estado/hierarquia e invoca apenas o listener, uma vez por solicitação, sem performClick ou carregamento de classes da extensão na interface. O callback precisa consumir o clique retornando true de forma síncrona. Campo normal, ação oculta/desabilitada, ancestral indisponível, chave inexistente, descritor antigo, Intent/fragment, controle personalizado ou não selecionável são recusados.

A operação não recebe métodos HTTP no broker, inclusive na abertura desse worker. Leituras GET/HEAD e POST são recusadas antes de uma requisição de rede. As outras operações mantêm suas capacidades anteriores. O snapshot do pedido é comparado no worker e no host: alterações em outra fonte não são aceitas. Isso é verificado em relação ao estado inicial do pedido; a inicialização OPEN conserva o comportamento anterior de registro/defaults e não vira uma transação global.

Se o listener retorna false, lança erro ou viola o escopo, suas alterações não chegam a um resultado bem-sucedido persistido pelo host. Não há repetição automática da ação. Uma nova tentativa exige outra confirmação explícita. Após sucesso, a tela é recarregada; recarregar não repete o listener. Ação não é campo editável e não pode ser disparada por importação de valores de backup.

## Limites

Somente ações locais padrão com contrato síncrono. Não há detecção universal de tarefas em segundo plano iniciadas pela extensão: o host aceita somente o snapshot retornado pela operação, não aguarda tarefas assíncronas e encerra o worker ao final. Não se promete execução exatamente uma vez entre morte de processo e tentativa manual, nem rollback global de inicialização/efeitos já ocorridos.

Intents, telas personalizadas, OAuth/Cloudflare, ações que precisam de HTTP, callbacks assíncronos e novels permanecem pendentes. Um listener padrão cujo corpo tenta usar essas capacidades pode aparecer como ação, mas falha ao executar; não há mudança automática para compatibilidade. Nenhum login real foi aprovado por esta etapa.

## Verificação

Testes JVM exercitam o contrato puro, validação de descritores, chave/hierarquia, escopo, execução única por chamada, retorno falso, erro e capacidade HTTP vazia. A fixture DEX mantém todas as classes anteriores e acrescenta cinco fontes sintéticas para sucesso, retorno falso, HTTP, outra fonte e erro.

Cenários Android de serviço/proxy foram preparados e compilados; sua execução, a confirmação visual e as fontes reais ficam para a rodada final. Não há aceite de runtime Android/ARM nesta revisão. Não há mudança de dependências, SQL ou Protobuf.

[Evidências filtradas](../integration/sandbox-actions/20261114/README.md) · [Checklist](BETA11_CHECKLIST.md).
