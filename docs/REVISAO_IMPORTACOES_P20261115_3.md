# Revisão de importações — P20261115.3

A tela **Configurações → Dados e armazenamento → Armazenamento do Polaris** passa a mostrar cópias interrompidas e pastas com o formato antigo de importação. A seção é expansível, informa nomes, tamanhos conhecidos e a necessidade de revisão. A limpeza do cache continua separada das cópias locais.

## O que a revisão informa

- **Cópia aguardando conferência do conteúdo:** pasta temporária atual com exatamente os três arquivos esperados, marcador v1 e metadados válidos; tamanho positivo informado pelo provedor precisa coincidir. A revisão lê apenas os metadados limitados, sem abrir o documento completo nem calcular seu hash. Portanto, não certifica os bytes nem a recuperabilidade. A importação repetida continua fazendo a conferência real antes de reutilizar/publicar a cópia.
- **Cópia incompleta:** pasta temporária atual ainda sem marcador final, contendo somente arquivos esperados ou vazia. Permanece preservada.
- **Formato antigo:** nome temporário `.import-XXXXXXXX-XXX`, ou pasta publicada no antigo padrão `título-XXXXXXXX-XXX` com `document.ext` e `details.json`/`ComicInfo.xml`. Esses sinais ajudam a localizar arquivos; não provam propriedade, abandono ou ausência de uso pela biblioteca.
- **Arquivos precisam de revisão:** nomes inesperados com prefixo `.import-`, marcador inválido/desconhecido, extras, diretórios internos, tamanho divergente ou acesso indisponível. Nada é alterado.

A revisão não é uma varredura universal de todos os documentos antigos: procura esses padrões de importação. Pastas normais de mangás não são classificadas como resíduos. Os resultados orientam a conferência manual no gerenciador de arquivos. Não há botão de exclusão nem descarte automático baseado em idade, nome ou falta de marcador. Para tentar retomar uma cópia completa compatível, incluir novamente o mesmo original em Documentos; a recuperação P20261115.1 permanece responsável pela verificação completa.

## Limites e preservação

A revisão compartilha o mutex de publicação: aguarda a importação ativa terminar e evita observar uma cópia intermediária criada pelo próprio app. Cancelamento é propagado e libera o mutex. O inventário usa somente leituras; não chama criação, escrita, rename, delete nem registro na biblioteca.

Há limites de 2000 entradas da pasta local, 100 resultados, 64 filhos por candidato, cinco segundos de orçamento cooperativo e leituras máximas de 4 KiB para marcador/16 KiB para detalhes. Subpastas não são percorridas. O provedor pode bloquear uma chamada individual; esses limites não constituem timeout capaz de interromper uma operação nativa bloqueada.

Listagem nula/erro, limite atingido ou tamanho não positivo informado pelo provedor gera indicação de revisão/tamanho incompleto. Arquivos extras, dados não reconhecidos e diretórios internos ficam intactos. Somatórios saturam antes de overflow. Uma falha em um candidato preserva a visibilidade dos demais. Nomes e metadados não autorizam exclusão nem atestam origem.

## Validação

[Evidência filtrada](../integration/import-review/20261115/README.md): testes JVM com arquivos/streams reais e adaptador UniFile, incluindo leituras proibidas de payload, erros de provedor, cancelamento, limites, metadados inválidos, preservação e serialização com publicação real até o registro simulado. Dois cenários Android com UniFile nativo são compilados para a rodada final, sem execução em aparelho nesta etapa.

Compilação final aprovada em 2min09s; 873 testes do app aprovados (22 novos), mais 85 anteriores de domain/UP-TO-DATE. Nenhum dos 936 casos anteriores ficou ausente. Quatro testes de overlay e 16 de empacotamento aprovados.

Não foi gerado APK nem publicada Release. SAF remoto, interface/aparelhos e pico de armazenamento ainda exigem validação final; esta revisão não encerra toda a frente de armazenamento. Sandbox continua arquivada/retirada; conta/nuvem continuam adiadas.
