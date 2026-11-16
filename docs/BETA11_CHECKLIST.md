# Beta.11 — checklist de consolidação

Base pública: beta.10/código111. Base de engenharia: P20261112.1, commit 6952e5e.
Este checklist acompanha o trabalho autorizado em 13/11. Não é uma declaração de lançamento.

| Frente | Estado |
| --- | --- |
| Jornada, XP, conquistas e grimórios | Implementados no checkpoint anterior |
| Sandbox e login isolado | PAUSADOS pelo usuário; fora do escopo de conclusão desta beta. Executor removido dos fontes compilados; histórico preservado na branch de arquivo (P20261115.2) |
| Biblioteca, fontes reais e backups entre leitores | Criação segura, ordem de categorias e persistência/reexportação em SQLite real verificadas em JVM (P20261115.4); SQLite/interface Android e troca pela UI de leitores externos pendentes |
| Leitura, OCR e tradução nos aparelhos | Pendente, incluindo diagnóstico do A12 |
| Armazenamento | Importação/cache, retomada de cópias completas e revisão de cópias parciais/pastas antigas (P20261115.3) implementados; pico, SAF e validação final pendentes |
| Atualização beta.10 → beta.11 e distribuição não depurável | APK interno gerado com assinatura original; atualização no aparelho e variante não depurável pendentes |

Ordem ativa: armazenamento → backups → leitura → distribuição. A sandbox não bloqueia a consolidação desta beta.

O [arquivamento P20261115.2](ARQUIVAMENTO_SANDBOX_P20261115_2.md) remove o executor do código ativo e preserva o aviso. A [decisão P20261114.4](PAUSA_SANDBOX_E_AVISO_P20261114_4.md) substitui as prioridades históricas abaixo. Instalações passam pelo aviso geral único com duas caixas; assinatura/integridade continuam verificadas.

Fluxo combinado com o usuário: concluir as pendências de implementação e as validações automáticas; seus testes ficam para a consolidação final, seguida da publicação da versão no GitHub. Não solicitar testes pessoais a cada revisão intermediária.

Não repetir funcionalidades já entregues com base nos documentos históricos. Não transformar
resultado de teste de componentes em aprovação da próxima beta inteira.

A [primeira revisão](LOGIN_E_ARMAZENAMENTO_P20261113_1.md) e a [proteção de backups P20261113.2](../integration/backup-safety/20261113/README.md) registram código, testes e limites.
A publicação não foi iniciada; a beta.10 continua sendo a versão pública.

O APK interno P20261113.3 foi gerado com a assinatura original recuperada e verificado como ARM32/ARM64; não é uma Release pública. A atualização em aparelho continua pendente. [Evidência do pacote](../integration/signing-recovery/20261113/README.md).

A continuação P20261113.4 acrescenta [controles numéricos isolados](SANDBOX_CONTROLES_P20261113_4.md), sem gerar outro APK nesta etapa. Validação da candidata não encerra os aceites reais listados acima.

P20261113.4: app e instrumentação compilados; 833 testes do app aprovados (12 novos), mais 85 de domain já aprovados e UP-TO-DATE. Nenhum caso anterior ausente. Três cenários Android aguardam execução em dispositivo. [Evidência](../integration/sandbox-numeric/20261113/README.md).

P20261113.5: [listas dinâmicas síncronas](SANDBOX_DINAMICO_P20261113_5.md), GET/HEAD na preparação e opções reconferidas ao salvar. App/instrumentação compilados, 845 testes do app aprovados (12 novos); seis cenários Android aguardam dispositivo. Sem outro APK nesta etapa.

P20261113.6: [cookies por caminho no login](LOGIN_COOKIES_P20261113_6.md), com cópia restrita ao host e snapshots consistentes. App/instrumentação compilados; 861 testes do app (16 novos) e 63 focados aprovados. Três cenários Android aguardam execução em aparelho/WebView.

Conta do Polaris/login Google/nuvem: desejados, mas **adiados pelo usuário**. Continuar nas demais frentes; preservar o backup local disponível. [Importação repetida e retomada](IMPORTACAO_REPETIDA_P20261113_7.md).

P20261113.7: importador e registro verificados por 18 casos novos. App/instrumentação compilados; 879 testes do app aprovados, mais 85 anteriores de domain. Quatro testes de overlay e 16 de empacotamento aprovados. Dois cenários Android aguardam execução; não encerra aceite SAF/ARM nem recuperação de staging abandonado.

P20261114.1: [restauração de categorias](RESTAURACAO_CATEGORIAS_P20261114_1.md) concluída antes de configurações/biblioteca; cancelamento impede continuação. 890 testes do app aprovados (11 novos), mais 85 anteriores de domain. App/instrumentação compilados, overlay4/empacotamento16 aprovados. Sem aceite físico ou de banco real e sem outro APK.

P20261114.2: [cache de documentos](CACHE_DOCUMENTOS_P20261114_2.md) por conteúdo quando tamanho/data estão ausentes, com proteção de cópias em uso. 904 testes do app aprovados (14 novos), mais 85 anteriores de domain; core/app/instrumentação compilados, quatro testes de overlay e 16 de empacotamento aprovados. Dois cenários Android aguardam execução; sem novo APK ou benchmark ARM.

P20261114.3: [ações locais padrão](SANDBOX_ACOES_LOCAIS_P20261114_3.md) com confirmação, execução no worker e sem HTTP. 919 testes do app aprovados (15 novos), mais 85 anteriores de domain; app/instrumentação compilados, quatro testes de overlay e 16 de empacotamento aprovados. Seis cenários Android compilados ficam para a consolidação final. Sem novo APK do app ou Release.

P20261114.4: sandbox pausada e desabilitada; aviso único local com duas caixas, fora dos backups. 931 testes do app aprovados (12 novos), mais 85 anteriores de domain; app/instrumentação compilados e componentes desabilitados conferidos no manifesto mesclado. Quatro testes de overlay e 16 de empacotamento aprovados. Código experimental preservado; sem novo APK ou Release. Foco nas quatro frentes ativas.

P20261115.1: [retomada de cópias completas](RECUPERACAO_IMPORTACOES_P20261115_1.md) após publicação interrompida, com conferência de conteúdo/metadados e sem nova cópia do payload pelo importador. 945 testes do app aprovados (14 novos), mais 85 anteriores de domain; app/instrumentação compilados, quatro testes de overlay e 16 de empacotamento aprovados. Resíduos parciais/legado permanecem pendentes; sem novo APK ou Release.

P20261115.2: [sandbox arquivada e retirada dos fontes compilados](ARQUIVAMENTO_SANDBOX_P20261115_2.md), incluindo componentes e ramificações de integração. Aviso e revisão de seleções/quarentenas antigas mantidos. 851 testes do app aprovados e 85 anteriores de domain; 94 casos exclusivos do executor arquivados, nenhum outro ausente. App/instrumentação compilados, classes/manifestos inspecionados, overlay4/empacotamento16 aprovados. Sem novo APK/Release ou medição do tamanho.

P20261115.3: [revisão de importações](REVISAO_IMPORTACOES_P20261115_3.md) na tela de armazenamento, com inventário limitado e somente leitura. Cópias interrompidas/pastas antigas ficam visíveis; falhas/limites/tamanhos desconhecidos são indicados. Não há limpeza automática de cópias locais, e retomada continua exigindo a conferência completa pelo importador. Resultados e limites na evidência da revisão.

Validação P20261115.3: BUILD SUCCESSFUL 2min09s; 873 testes do app aprovados (22 novos), mais 85 anteriores de domain/UP-TO-DATE. Total 958 nos relatórios, sem falhas/skips ou casos anteriores ausentes. App/instrumentação compilados, overlay4/empacotamento16 aprovados; dois cenários Android novos compilados e ainda não executados. A sandbox continua ausente do JAR/manifesto atual. Sem novo APK/Release.

P20261115.4: [backups com SQLite real e progresso sem regressão](BACKUPS_SQLITE_P20261115_4.md). Três falhas anteriores reproduzidas; 16 casos novos aprovados, com esquema/repositórios/transações reais em JVM. Compilação de app/instrumentação aprovada; 889 testes do app e 85 de domain executados/aprovados (974), nenhum caso anterior ausente. Overlay4/empacotamento16 aprovados, dois controles Android novos compilados. Driver JDBC exclusivo de testes confirmado fora do runtime release. Sem novo APK/Release; Android/interface e troca pela UI de outros leitores permanecem pendentes.
