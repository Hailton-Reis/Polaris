# Retomada de importações completas — P20261115.1

Continuação da beta.11/código 112, na frente de armazenamento. Sandbox inteira pausada; conta/nuvem adiadas. Testes pessoais na consolidação final. Sem novo APK do app ou Release.

## Problema tratado

Uma falha ao renomear a pasta de importação podia deixar os arquivos completos em `.import-UUID`, mesmo após verificação do documento e gravação do marcador final. A nova tentativa ignorava essa pasta e preparava outra cópia; também exigia capacidade para essa cópia adicional. Uma edição no documento deixado para trás não era considerada na nova tentativa.

Agora, ao repetir a inclusão dos mesmos bytes/formato, o importador primeiro reutiliza uma publicação já válida e, se não houver, procura uma cópia interrompida compatível. A busca só enumera a pasta local configurada, sem varrer o celular.

## Critérios de retomada

- Diretório com nome canônico `.import-UUID` versão 4, como os gerados pelo importador.
- Marcador `.polaris-import` com os mesmos hash SHA-256 e formato; versão 1, campos e tamanho são conferidos.
- Exatamente os três arquivos esperados: marcador, `details.json` e `document.<formato>`, sem diretórios ou arquivos extras.
- Releitura do documento com conferência de hash/tamanho reais, mais validação limitada dos metadados de título/autor.
- Um único candidato e nenhum destino concorrente com a mesma identidade.

A pasta completa é renomeada usando o título guardado nos seus metadados. Não há outra cópia do payload feita pelo importador, nem chamada ao check consultivo de espaço destinado a uma nova cópia. Os bytes dos metadados existentes não são reescritos para acompanhar outro título do formulário. Registro/categorias continuam no fluxo já existente; favoritos publicados preservam seu estado como antes.

Após renomear, o destino é resolvido novamente e conferido antes do registro. Se o provedor reporta falha, se há cancelamento ou se a indexação falha, os dados completos preexistentes não são apagados. Uma nova tentativa pode retomar a publicação ainda oculta ou o registro da publicação já visível.

## Preservação e limites

Conteúdo do documento alterado, versão desconhecida com a mesma identidade, metadados inválidos, arquivos extras ou mais de um candidato impedem a retomada automática e ficam preservados para revisão. A convenção de nome/marcador identifica o protocolo; não constitui assinatura criptográfica de propriedade da pasta.

Pastas sem marcador completo, nomes não reconhecidos, arquivos regulares com nome parecido e cópias de outros conteúdos não são movidos nem apagados por esta recuperação. Uma nova importação pode prosseguir separadamente, deixando um resíduo incompleto anterior para revisão. Não é limpeza global, recuperação de qualquer estágio parcial ou reconciliação automática do legado. Esses itens permanecem pendentes.

O temporário inicial e a validação do arquivo escolhido continuam necessários; faltar espaço nesse volume ainda pode impedir a tentativa antes da retomada. O provedor precisa listar, reler e renomear. O custo real de rename depende dele. Não há transação única entre provedor e banco, garantia contra interferência externa ou benchmark ARM/A12. Nenhum esquema SQL, formato de backup ou formato do marcador mudou.

## Verificação

Os testes exercitam DocumentImporter/DocumentImportPublication reais, streams e arquivos locais. Context/UniFile e o limite de registro no banco são simulados; não aprovam um provedor SAF ou uma restauração completa em SQLite. Dois cenários com UniFile nativo foram compilados para a rodada final, sem execução nesta etapa.

[Evidências filtradas](../integration/import-recovery/20261115/README.md) · [Checklist ativo](BETA11_CHECKLIST.md).

A [revisão P20261115.3](REVISAO_IMPORTACOES_P20261115_3.md) torna cópias interrompidas e pastas antigas visíveis no armazenamento. O inventário não lê o payload inteiro nem libera conteúdo com base apenas nos metadados; a retomada descrita aqui continua conferindo o hash real.
