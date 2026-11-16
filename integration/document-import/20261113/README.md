# Importações repetidas e registro interrompido — P20261113.7

Desenvolvimento da beta.11/código 112. Conta própria/login Google/nuvem ficam adiados por pedido do usuário; esta rodada avança o armazenamento local. Backup, SQL e formato Protobuf não foram alterados. Sem novo APK; o arquivo disponibilizado continua P20261113.3.

## Implementação real

DocumentImporter agora calcula SHA-256 durante a cópia temporária limitada, conserva a validação do formato e usa DocumentImportPublication para criar/reusar a publicação. O coordenador serializa importações do app, enumera nomes somente na pasta local configurada e confere um marcador próprio, formato, tamanho real e hash completo. O prefixo de pasta permanece legível; título diferente não causa cópia nova se o conteúdo/formato é o mesmo. Não agrupa arquivos diferentes só pelo nome.

Nova cópia exige staging novo/vazio, destino vazio e releitura de payload/metadados antes da publicação. Após rename, o destino é resolvido novamente e os bytes são conferidos. A fonte original não é removida. Se já existe publicação válida, não se exige espaço para outra cópia no destino. O temporário e as releituras continuam necessários.

Uma falha no banco/categorias não apaga a publicação válida. Repetir a inclusão pode concluir o registro usando a mesma pasta. DocumentLibraryRegistration consulta a URL local existente antes de criar: favorito retorna com mesmo ID sem trocar título/categorias/data/progresso; linha parcial é retomada, preservando identidade e data anterior. Novo favorito só é confirmado após organização. Opções de reimportação não sobrescrevem a organização de um favorito já existente.

O marcador é `.polaris-import`, sem extensão JSON. O LocalSource original escolhe um JSON de metadados e pode convertê-lo em ComicInfo.xml, apagando aquele JSON; usar outro JSON como marcador seria incompatível. A reutilização conserva essa conversão, títulos/capas extras e alterações manuais. Payload alterado, marcador desconhecido ou candidatos ambíguos são recusados sem substituição.

## Validação executada

Três testes com o importador real e streams reais, adaptando apenas UniFile/registro, reproduziram a lógica anterior: mesmo conteúdo retornava outro ID/cópia; falha no registro seguida de tentativa criava outra pasta; leitura corrompida do provedor não era conferida. O vermelho falhou nesses três asserts esperados, não por falha de ambiente. Logs e XML originais preservados localmente; o repositório recebe apenas resultados filtrados.

A suíte definitiva executou **879 testes do app, todos aprovados**, incluindo 18 novos: 14 da publicação/importador e quatro da política de registro. Com 85 testes de domain já aprovados e UP-TO-DATE, os relatórios somam 964/964 sem falhas/skips. data/source-api NO-SOURCE. Comparação com 946 casos arquivados .6 não encontrou ausentes; 18 novos passaram. A base antiga não foi reexecutada.

Os casos cobrem duplicação, retomada, concorrência, bytes diferentes de mesmo nome, rename ocorrido com resposta falsa, corrupção/edição preservada, metadados/capa, falta de espaço para segunda cópia, cancelamento/limpeza, tamanho desconhecido, marcador desconhecido, ComicInfo e listagem indisponível. O primeiro build revelou que UniFile.listFiles é nullable; a correção recusa listagem indisponível em vez de tratá-la como vazio, com regressão específica. initial-compile.log resume esse erro já resolvido.

Gradle definitivo compilou app e instrumentação: BUILD SUCCESSFUL em 4min41s, 285 tarefas, 11 executadas. Guard sem disparo, mínimo 480.497.664 bytes livres. Quatro testes completos de overlay e 16 do empacotador passaram. Dois cenários Android com UniFile nativo foram compilados, **não executados**; ADB sem aparelho/emulador conectado. Nenhuma declaração de aceite SAF real, ARM ou desempenho.

android-compile-unit.log contém somente os resultados das tarefas solicitadas. Os casos de 163 relatórios em unit-test-results.json, unit-comparison.json e source-provenance.json vinculam resultados/fontes. red.log/red-test-results.xml registram os resultados e asserts do ensaio anterior, sem configuração do ambiente ou traces locais. RESULT.json e SHA256SUMS.txt identificam os artefatos. Logs completos, ZIP e XML originais ficam locais; o JSON público lista apenas nomes/classes e resultado dos casos: propriedades, saída de ambiente, proxy, hostname e caminhos de máquina foram removidos da evidência pública.

## Limites e pendências

A detecção vale para publicações novas com marcador no diretório atual e mesmo formato. Não varre bytes de pastas legadas nem mescla duplicatas antigas/arquivos renomeados manualmente ao banco. A reconciliação após restaurar metadados sem os arquivos e entre leitores continua pendente. Não há recuperação automática de todos os stagings deixados por morte do processo. Se um provedor reportar falha de rename sem destino visível, a cópia completa pode permanecer oculta para revisão; não é apagada por suposição.

A API do provedor não oferece transação única de filesystem+banco nem impede agentes externos. Verificações adicionais leem/hasham o arquivo várias vezes; medições de I/O, pico e fluidez no A12/ARM continuam necessárias. [Escopo de produto](../../../docs/IMPORTACAO_REPETIDA_P20261113_7.md) e [checklist](../../../docs/BETA11_CHECKLIST.md).
