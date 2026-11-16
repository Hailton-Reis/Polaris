# Retomada de importações completas — P20261115.1

Frente ativa: armazenamento. Sandbox inteira continua pausada; conta/nuvem adiadas. Ao repetir a inclusão dos mesmos bytes/formato, DocumentImportPublication reutiliza primeiro uma publicação válida ou retoma um diretório interrompido reconhecido, sem outra cópia do payload feita pelo importador. Não modifica nem apaga o arquivo original.

## Contrato

A retomada só aceita um diretório .import-UUIDv4 canônico, marcador completo da versão 1 com identidade/formato correspondentes e exatamente os três arquivos do protocolo: marcador, details.json e document.ext. Releitura confere hash/tamanho reais; metadados de título/autor são validados e preservados. O nome final usa o título guardado na cópia. Destino é conferido novamente antes/depois do rename; falha de rename, cancelamento ou registro não apaga dados preexistentes. O check consultivo de capacidade para outra cópia no destino não é chamado nessa via. O temporário de entrada continua necessário.

Mais de um candidato, conteúdo alterado, versão desconhecida correspondente, dados inválidos ou extras impedem movimento automático. Não há exclusão de resíduos nem reconstrução global do banco. Pastas incompletas/sem selo, nomes não reconhecidos e arquivos comuns são preservados; outra importação pode prosseguir separadamente, mantendo esses resíduos para revisão. Não há prova criptográfica de propriedade da pasta nem transação atômica de provedor+banco.

## Validação

O vermelho executou três testes com importador e streams reais e reproduziu três falhas do código anterior: mais de uma pasta após repetir rename interrompido; requisito de capacidade para outra cópia; nova publicação apesar de documento editado na cópia interrompida. Não foram falhas de ambiente.

Gradle final BUILD SUCCESSFUL em 2min30s. **945 testes do app executados e aprovados**, incluindo 14 novos; mais 85 casos de domain antes aprovados ficaram UP-TO-DATE. Relatórios somam **1030/1030**, sem falhas/skips JVM. Comparação contra 1016 casos arquivados da .4: nenhum ausente e 14 novos aprovados; a base não foi reexecutada.

Os novos casos exercitam retomada sem nova escrita de payload, capacidade do destino, dados/metadados preservados, conflito, versões desconhecidas, extras, sem marcador/renomeados, cancelamento, rename ocorrido com resposta falsa, falha posterior de indexação, metadados inválidos e arquivo comum com nome parecido. DocumentImporter/DocumentImportPublication e os streams/arquivos são reais; Context/UniFile e a fronteira de registro em banco são simulados.

App e instrumentação Kotlin compilaram. Dois cenários Android com UniFile nativo foram compilados: recuperação sem nova cópia e recusa de candidatos ambíguos. **Não foram executados.** Quatro testes completos do overlay e 16 de empacotamento passaram. Isso não aprova SAF remoto, SQLite/interface, benchmark A12/ARM ou garante que rename do provedor não faça trabalho extra internamente.

## Próximos itens

Gestão segura de resíduos parciais/legado, pico de espaço e validação final continuam pendentes. Não há mudanças de dependências, SQL, Protobuf ou formato do marcador. Sem novo APK do app ou Release; o interno P20261113.3 continua anterior às revisões novas. Testes pessoais ficam para consolidação final, conforme pedido do usuário.

Evidência pública é JSON legível com identidades/resultados/asserts/hashes e documentação, sem logs brutos/ZIP/proxy/traces locais. [Escopo](../../../docs/RECUPERACAO_IMPORTACOES_P20261115_1.md) · [Quatro prioridades](../../../docs/BETA11_CHECKLIST.md).
