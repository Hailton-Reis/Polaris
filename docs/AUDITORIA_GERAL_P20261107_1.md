# Auditoria geral e personalização — P20261107.1

Revisão de desenvolvimento da beta.11/código 112, posterior ao commit 3b35452. A beta.10 pública permanece inalterada. O horário dos comandos e consultas está em UTC; a data desta revisão segue America/Fortaleza, 7 de novembro de 2026.

A revisão cobre os fluxos solicitados e os seus pontos de entrada: perfil, aparência, manifesto/links/ícones, WebView, extensões e IPC, restauração e preferências, leitura/mesclagem, OCR, tradutores, atualização e dependências. Isso inclui inspeção de código e documentos de planejamento, testes JVM, controles do overlay/empacotamento e instrumentação Android. O relatório final distingue código implementado, prova por componentes e aceite real. Não é uma certificação de todo código nativo, todos os repositórios ou todos os aparelhos.

## Achados tratados

| Achado verificado | Correção | Evidência e alcance |
|---|---|---|
| O perfil somava XP de downloads e o nível podia cair ao apagá-los | XP novo acompanha a maior contagem confirmada de capítulos lidos; snapshot legado preservado uma vez; instalação nova não recebe XP de downloads | Regressões de migração, contagem lógica, remoção/releitura e limites |
| Contagens físicas podiam duplicar edições do mesmo capítulo | Usa identidade lógica dentro de cada obra; capítulos sem identidade numérica de filhos legados permanecem distintos | Casos de PT/EN, duplicatas e capítulos desconhecidos |
| Cada download disparava varredura de biblioteca/downloads | Removidas as duas chamadas do downloader; atualização de perfil fora do caminho crítico do leitor, com eventos agrupados e cache por obra | Inspeção dos pontos de chamada e testes de contagem |
| Nome/XP/título ficavam em SharedPreferences separadas da exportação normal | Migração de nome/título e progresso para preferências normais exportáveis quando a pessoa inclui configurações; avatar/capa permanecem locais e fora do backup | Criador real de preferências e armazenamento Android sintético |
| Avatar/capa tinham cópia ilimitada, stream sem fechamento e remoção antecipada | Limite de 8 MiB, validação de raster/dimensões, arquivo temporário, rename, commit da preferência antes da remoção e conferência canônica dos arquivos próprios | Oversize, stream fechado, falha sem perder arquivo anterior, symlink/escape e PNG no Android |
| Níveis/títulos escuros e textos antigos prejudicavam legibilidade/identidade | Jornada Polaris, títulos localizados com IDs estáveis, cores do tema, nível máximo sem ultrapassar 200 e cartões que acomodam texto maior | Contraste e capturas sintéticas |
| WebView explicitamente desabilitava Safe Browsing | Reativada proteção e bloqueado acesso de páginas web a file/content locais, mantendo navegação remota/JS | Manifesto e configuração de WebView; provedores WebView reais ainda precisam de aceite |
| PFD vindo do processo de extensão era lido como Parcelable por nome de classe | Transporte com creator tipado de ParcelFileDescriptor | Serviço/proxy real e extensão sintética na instrumentação |
| Runner dizia aceitar somente quadrinhos HTTP mas não excluía INovelSource | Exclusão explícita de novels; falha mantém isolamento sem executar reserva no host | Inspeção do contrato; adaptações de novels permanecem pendentes |
| Retornos de trackers podiam chegar sem fluxo ativo e callback vazio podia causar logout | Sessão local por provedor, nonce/state nos fluxos padrão, prazo de 10 minutos, consumo único, limite de URL e preservação da conta em cancelamento | Testes de callback não solicitado, replay, provedor errado, expiração e relógio; sem login real |
| Clientes de tradutores consultavam HTTP/DI antes de validar configuração vazia | Inicialização preguiçosa após validações; não ativa provedor remoto | Testes antigos de erros tipados |
| Testes JSON usavam stubs Android no JVM | org.json real em escopo exclusivamente de teste | Testes de parsing completos e truncados |
| Teste de TTS esperava espaço final apesar do contrato trim | Expectativa corrigida, mantendo verificação do texto e reticências | Teste existente; sem alteração do sanitizador |
| DBNet abandonara OCR ML Kit próprio, aceitava grupos ambíguos/linhas não reconhecidas e retirara limite de densidade | Restaurados sessão ML Kit preguiçosa/lifecycle, propriedade única/completa e limite de limpeza; falha usa OCR de reserva | Os nove casos antigos e demais regressões do detector; execução nativa ARM64 ainda pendente |
| Dois avisos OSV em dependências resolvidas | jsoup 1.23.1 → 1.23.2 e Guava 32.0.0-jre → 33.7.2-android | Consultas anteriores/posteriores e grafo realmente resolvido |
| Defaults de telemetria e manifesto noop incoerentes com opt-in | Defaults desligados e correção do nome AndroidManifest.xml | Configuração de build/manifesto; builds normais já não incluíam telemetria |

## Dependências e alcance

A consulta inicial ao OSV encontrou dois avisos entre 382 coordenadas Maven da configuração de execução debug. Após a atualização, 380 coordenadas foram consultadas sem avisos retornados nessa base naquele momento. Os JSONs registram data, versões, IDs e respostas. Bibliotecas de teste, código nativo e APKs de extensão não são certificados por esse resultado.

- **jsoup / GHSA-65r4-943x-97jj / CVE-2026-75140:** consumo quadrático de memória por namespaces XML aninhados. O projeto processa documentos e conteúdo externo; aplicar a versão corrigida é apropriado. Não se executou um ataque contra fontes ou dados reais.
- **Guava / GHSA-xxph-c9ww-hj94:** alocação não controlada em desserialização Java. A busca no código do host não encontrou ObjectInputStream/readObject em app/core/data/domain; isso limita a exposição observada, mas não prova ausência em todas as bibliotecas/extensões. Aplicada a edição Android corrigida.

As integrações opcionais de rastreamento mantêm registros/clientes herdados. O Polaris precisa de revisão/registro próprio de clientes e redirecionamentos antes de aprovar esse conjunto para distribuição estável; identificadores ou segredos de cliente embutidos em aplicativos móveis não equivalem a segredos de conta protegidos. Este relatório não reproduz seus valores. O protocolo Hikka não apresenta state OAuth nesse fluxo: a proteção local exige início explícito e prazo, mas a vinculação completa com o serviço ainda exige uma etapa própria. Os verificadores PKCE/estado existentes dos provedores também precisam de teste com morte de processo e navegador real.

## Personalização entregue nesta revisão

- **Jornada Polaris:** nome/avatar/capa, estatísticas e coleção de títulos. Títulos são a única recompensa; sem moedas, capacidades de leitura pagas por XP ou notificações de troféus em sequência.
- **Ícones de tela inicial:** original + Aurora, Órbita e Constelação. O componente MainActivity continua habilitado para atalhos, backups e links. Ao trocar, o novo alias é ativado antes de desativar os outros; há recuperação de estado e tentativa de retorno ao original em falha. O iniciador do aparelho pode demorar para atualizar; o ícone em outros lugares do Android pode continuar sendo o ícone base do pacote.
- **Temas:** Boreal, Aurora e Âmbar, com claro/escuro e integração ao modo de preto puro. Temas e ícones estão disponíveis independentemente do nível. As preferências existentes continuam válidas.
- **Identidade visível:** perfil, ajuda, aviso de backup, identificação/capturas futuras no Telegram e wakelock do áudio passam a Polaris. Recursos Android antigos sem referências foram removidos. Créditos/licenças, símbolos JNI, namespace, chaves/caminhos legados e classe de navegação de compatibilidade são preservados onde necessários.

As imagens de perfil continuam locais; nomes, título e progresso acompanham o backup quando as configurações correspondentes são incluídas. A progressão usa a maior contagem confirmada: desmarcar/reler ou diminuir a biblioteca não reduz XP nem concede XP repetido até superar a contagem anterior. O snapshot legado preserva a pontuação anterior calculada no momento da primeira migração.

## O que ainda falta desenvolver

| Frente | Estado e próximo trabalho |
|---|---|
| Uma obra em toda a experiência | A união dentro de uma entrada está implementada. Falta deduplicar resultados globais e entradas já separadas de uma biblioteca restaurada, com revisão conservadora de identidade |
| Extensões isoladas | Executor HTTP de quadrinhos é experimental/optativo. Faltam adaptação de preferências/login/filtros, maior cobertura de extensões, isolamento do runtime de novels e avaliação para ativação padrão |
| Novels com várias fontes | O leitor/texto existem. A mesma seleção/mesclagem canônica dos quadrinhos não foi concluída para novels |
| Continuidade de página entre edições | Mantém capítulo, leitura e marcador; não copia índice de página entre paginações diferentes. Correspondência por bytes/hashes/percepção permanece planejada |
| Reuso entre fontes | Cache secundário por conteúdo da página/revisão do pipeline ainda não implementado; cache atual/glossário são preservados |
| Saúde de fontes | Existem amostras e recuperação por falha. Histórico por endpoint, janelas e tentativas adaptativas continuam planejados; não testar agressivamente todos os capítulos em segundo plano |
| Invalidação fina de tradução | Separar revisões de geometria, OCR, glossário, tradução e render para evitar recomputar tudo |
| Documentos | Maior fidelidade de EPUB/DOCX, tabelas, fórmulas e PDFs com camada textual; otimização de materialização/importação e caches fora da meta |
| Tamanho/processamento | Medir heap, pico de armazenamento e custo por etapa nos aparelhos; não há benchmark ARM de desempenho que possa ser inferido de testes JVM/x86 |
| Distribuição | Consolidar variante pública não depurável mantendo ID/assinatura e atualização por cima. Os APKs públicos de teste e este harness debug não equivalem a uma versão estável endurecida |
| Integrações/contas | Registro próprio de clientes, callbacks/PKCE e aceite real dos rastreadores; nenhuma conta foi conectada nesta auditoria |
| Diagnósticos avançados | Explicar seleção/saúde/decisão de tradução sem expor detalhes técnicos no fluxo normal de leitura |

## O que exige validação, não uma promessa de implementação ausente

1. A12/ARM32, ARM64/S20FE e outros Androids: abertura de capítulos, fontes, decoder, OCR, memória, aquecimento e retomada em rede instável. A causa original da falha do A12 permanece não confirmada.
2. Fontes reais: backup antigo, aliases PT/EN, melhor edição com páginas que abrem, complemento e tradução automática, fixação manual e troca durante falha. Os testes sintéticos não aprovam todos os catálogos.
3. Backups: ida/volta real por banco/interface do Mihon/Tachiyomi. Campos nativos/URLs/progresso são testados; leitores que descartam memo não conservam todas as edições. Não existe promessa sem perda por todos os forks.
4. OCR: os controles de 27 recortes e página longa e os ensaios de capítulos registrados não são benchmark de velocidade/memória ARM nem prova universal de um vencedor. Tiny pesquisado não foi integrado. DBNet restaurado requer controle de qualidade em imagens reais; AOT-GAN não deve voltar à interface como recurso funcional sem implementação usada pelo pipeline.
5. Atualizador: houve teste de retomada por HTTP e downloads públicos, mas falta interromper/retomar/instalar no aparelho em condições como a viagem relatada. Atualização diferencial de APK permanece adiada; retomar o APK inteiro é o caminho atual.
6. Aparência: iniciadores Samsung/outros podem atrasar a atualização de aliases; validar ícones temáticos em Android 13+, fonte ampliada, acessibilidade e atualização de instalações existentes.
7. Segurança: WebView e trackers em navegador real, limites/cancelamento de provedores de conteúdo, escopo dos caminhos FileProvider e serviços legados, bibliotecas nativas e repositórios externos. HTTP legado e CAs instaladas pelo usuário continuam permitidos por compatibilidade. Uma extensão em modo de compatibilidade continua executando com as permissões do Polaris.

O servidor pessoal e Gemini continuam fora das prioridades ativas. Não são necessários para esta reformulação nem para leitura básica/tradução offline com os modelos preparados. Repositórios não autorizados não são instalados silenciosamente.

## Evidências

O diretório [de evidências desta revisão](../integration/personalization-audit/20261107/README.md) reúne relatórios, hashes, escopo dos testes e capturas sintéticas. **782/782 casos JVM passaram**, preservando todos os 764 casos anteriores e corrigindo as 17 falhas anteriores, sem skips. Os 13 controles de overlay/empacotamento passaram. **11 testes Android passaram em API26 x86_64**, incluindo serviço/proxy isolado, identificação de idioma, aliases/links, preferências/backup e decoder real. O ensaio de capturas foi repetido e passou após dispensar um diálogo de ANR do System UI surgido na inicialização do emulador; as capturas finais foram inspecionadas sem obstrução, inclusive com fonte ampliada. Os resultados estão em TEST_RESULTS.json. Isso não equivale a aceite físico ARM ou de todos os fluxos reais. Nenhuma nova release é publicada por este relatório.
