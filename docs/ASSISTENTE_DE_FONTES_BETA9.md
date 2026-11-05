# Assistente de fontes — beta.9 interna

A revisão P20261104.4 acrescenta o fluxo guiado de preparação de fontes. A beta.9 permanece sem lançamento público.

## Caminho de uso

Ao concluir a configuração inicial, o Polaris oferece **Preparar fontes**. Quem importa um backup pelo guia inicial passa primeiro pela restauração; ao retornar, encontra o assistente. Ele também pode ser aberto em **Navegar → Extensões → ⋮ → Preparar fontes** ou pelo botão da lista de extensões vazia.

1. A introdução explica repositórios e extensões, os riscos de código de terceiros e a opção de importar um backup primeiro. É possível adiar a configuração. A confirmação de ciência não inicia downloads.
2. A pessoa seleciona os repositórios existentes ou confere uma sugestão/link HTTPS. Nome, endereço e certificado são mostrados antes de adicionar. O certificado é conferido novamente ao registrar o repositório. Repositórios restaurados não são selecionados nem autorizados para execução em lote automaticamente.
3. O catálogo é consultado por repositório, com prazo e erro separado. A pessoa pode preparar fontes da biblioteca, dos idiomas escolhidos ou uma seleção manual. Fontes marcadas como adultas exigem opção explícita. Versões incompatíveis, links de download inseguros e pacotes conflitantes são informados e excluídos da fila.
4. A tela informa a quantidade selecionada e o possível consumo de dados/espaço antes do botão de confirmação. O catálogo não fornece tamanho total confiável.
5. A fila usa no máximo dois downloads simultâneos, com progresso por extensão, resumo, cancelamento e repetição somente das falhas/cancelamentos. O arquivo é preparado e validado antes da substituição. “Pronta para usar” exige confirmação de carregamento das fontes esperadas.

## Instalação e confiança

As novas extensões deste fluxo são instaladas dentro do Polaris; a preferência geral de instalador não é modificada. Extensões já instaladas pelo Android são preservadas e continuam gerenciáveis em Extensões. O assistente não transforma esses aplicativos em arquivos privados nem concede confiança manual em lote.

Cada tentativa vincula repositório, certificado, pacote e versão escolhidos. A autorização do repositório é conferida antes do download e novamente antes da instalação. A assinatura criptográfica do APK é verificada com apksig, e os bytes preparados precisam corresponder ao certificado, pacote e versão esperados. A atualização automática dos metadados do repositório não substitui silenciosamente uma chave diferente. A alteração exige revisão explícita.

A fila continua ao sair da tela enquanto o processo do aplicativo existir. Não é um serviço persistente com retomada após reinício: se o Android encerrar o processo, é necessário reabrir o assistente, consultar os catálogos e preparar o que falta. As extensões já preparadas são reconhecidas. Não se implementou download parcial de APKs de extensões nem atualização automática em lote sem confirmação.

## Backups e migração

O assistente não altera o formato ProtoBuf, campos existentes, identificadores de fontes, URLs de obras/capítulos ou chaves de preferências. A seleção da biblioteca usa os identificadores originais das fontes; não tenta ligar obras somente pelo título. Fontes ausentes não provocam exclusão da biblioteca ou do progresso. A seleção de idiomas do assistente respeita preferências já gravadas, sem substituí-las globalmente.

Extensões privadas são específicas da instalação do Polaris; backups de biblioteca não incluem seus APKs. Ao voltar para Mihon/Tachiyomi, as fontes precisam estar disponíveis naquele aplicativo, mantendo os mesmos identificadores. A meta continua sendo a migração nos dois sentidos. A [validação de codec](../integration/backup-interop/20261104/README.md) e os testes do assistente não substituem o aceite de restauração/mescla no banco e na interface dos outros aplicativos.

## Validação

Os resultados finais e seus limites ficam em `integration/source-preparation/20261104/README.md`. Não se presume aprovação de interface, celulares ARM ou provedores SAF a partir de testes JVM ou de componentes isolados no Android.
