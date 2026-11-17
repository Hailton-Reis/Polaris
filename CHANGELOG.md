# Histórico de versões do Polaris

Este arquivo registra a evolução real do código. **Revisões de desenvolvimento não são lançamentos públicos.** As datas abaixo usam America/Fortaleza, exceto quando houver indicação de UTC. O histórico de distribuição fica em [Releases](https://github.com/Hailton-Reis/Polaris/releases).

## Desenvolvimento · P20261117.5 — 17/11/2026

**Estado:** fontes mistas preservadas e aviso de conteúdo sensível para a próxima versão; sem novo APK/Release.

- Filtro +18 continua ligado por padrão, agora por obra: tags, classificação e marcadores no título. Removido o bloqueio de fontes inteiras pela marcação da extensão, permitindo resultados comuns de fontes mistas.
- Desligar pede confirmação **Estou ciente, liberar**; cancelar mantém o filtro. Religar é imediato. Biblioteca e escolhas independentes de fontes preservadas; conteúdo sem marcação pode escapar.
- Sete controles da política anterior foram substituídos por sete de filtragem por obra, sem aumento do total. 86 controles focados e validação completa aprovados: 977 app executados + 87 domain anteriores/UP-TO-DATE = 1.064 casos. Nenhuma falha/skip ou ausência inesperada; as sete substituições estão listadas nas evidências.
- Overlay4/empacotamento27/comparador21 aprovados. Aviso compilado/revisado no código, sem execução da interface no aparelho. Sem análise de imagens ou alteração da concorrência/agendamento.

[Comportamento e aviso](docs/FONTES_MISTAS_P20261117_5.md) · [Evidências](integration/adult-items/20261117/README.md).

## Desenvolvimento · P20261117.4 — 17/11/2026

**Estado:** filtro +18 para a próxima versão; sem novo APK ou Release.

- Filtro ligado por padrão e reversível em Navegar → Conteúdo adulto. Oculta fontes adultas e obras marcadas nas buscas geral/novels/migração, navegação de fonte e alternativas automáticas, inclusive após enriquecimento válido.
- Mudança da opção reinicia buscas e invalida a descoberta. Biblioteca e leitura original/fixa preservadas. Conteúdo sem marcação ou identificado tardiamente pode aparecer; sem análise de imagens ou consultas extras para classificar.
- Três falhas anteriores reproduzidas e 25 casos novos. Validação completa: 977 app executados/aprovados + 87 domain anteriores/UP-TO-DATE = 1.064 casos; overlay4/empacotamento27/comparador21 aprovados. Provedores simulados, interface compilada sem execução no aparelho.
- Mais alternativas em primeiro plano e atualização periódica em segundo plano ficam como propostas. Concorrência atual preservada: cinco tarefas na busca geral e duas nas alternativas automáticas.

[Configuração e limites](docs/FILTRO_ADULTO_P20261117_4.md) · [Evidências](integration/adult-search-filter/20261117/README.md).

## Desenvolvimento · P20261117.3 — 17/11/2026

**Estado:** descoberta entre fontes mais eficiente para a próxima versão; sem novo APK ou Release.

- Atualização de catálogos confirmados e checagem de imagens passam a integrar operações paralelas limitadas a duas alternativas entre obras. Fila de resultados pronta limitada a dois; fonte original preservada fora dessa fila.
- Catálogo confirmado já atualizado não provoca pesquisa repetida na mesma fonte. Busca que esgota orçamento fica incompleta e elegível após um minuto; conclusão normal conserva 24 horas. Painel de fontes avisa sobre a tentativa incompleta.
- Quatro falhas anteriores reproduzidas. Tempos simulados de 3→2 segundos para três catálogos e 4→2 para quatro checagens; não são medições de fonte real/aparelho.
- Quinze casos novos; 952 app executados/aprovados e 87 domain anteriores/UP-TO-DATE: 1.039 casos sem regressões. Compilação final 2min19s; overlay4/empacotamento27/comparador21 aprovados. Critérios de associação, numeração, idiomas, origem dos dados e fonte fixa preservados; amostras reutilizadas mantêm sua validade original.

[Comportamento e limites](docs/BUSCA_FONTES_P20261117_3.md) · [Evidências](integration/source-discovery/20261117/README.md).

## Desenvolvimento · P20261117.2 — 17/11/2026

**Estado:** limpeza de recortes Paddle para a próxima versão; sem novo APK ou Release.

- Recortes passam a pertencer ao lote antes da consulta de dimensões, dentro do fechamento que também cobre a preparação. Falha num recorte seguinte ou na consulta não deixa os já retornados sem liberação explícita; vazios ficam fora do reconhecimento.
- Duas falhas anteriores reproduzidas no motor real com fronteiras nativas simuladas. Sete casos novos e 15 controles focados aprovados, incluindo ordem/índices, confiança, vazios, erro de reconhecimento e falha em lote posterior.
- Modelos e algoritmos permanecem com a lógica anterior; alteração local de vida útil documentada no SDK. Não mede RAM nem cobre temporários internos de uma operação que falha antes de devolver o recorte.
- Compilação/validação final aprovada em 2min34s; 939 testes do app executados/aprovados e 85 anteriores de domain/UP-TO-DATE: 1.024 casos sem regressões. Overlay4/empacotamento27/comparador21 aprovados.

[Correção e limites](docs/LIMPEZA_RECORTE_OCR_P20261117_2.md) · [Evidências](integration/ocr-crop-ownership/20261117/README.md).

## Desenvolvimento · P20261117.1 — 17/11/2026

**Estado:** OpenCV oficial integrado/compilado para a próxima versão; sem novo APK ou Release.

- Substituído o pin QuickBird por `org.opencv:opencv:4.12.0`, pelo catálogo realmente consumido no SDK. AAR resolvido coincide com o artefato oficial pesquisado; API mínima do app continua 26.
- Saída nativa real conferida: 31 arquivos ARM32/ARM64, quatro OpenCV/C++ idênticos ao AAR e 27 restantes inalterados. Todas as ARM64 têm PT_LOAD de pelo menos 16 KiB e offsets/endereços congruentes; 204 importações C++ por ABI conferidas sem ausentes. Dois controles negativos recusados.
- SDK/app/mesclagem compilados; 932 testes do app executados/aprovados e 85 anteriores de domain/UP-TO-DATE: 1.017 casos sem regressões. Overlay4/empacotamento27/comparador21 aprovados.
- Conjunto nativo cresce 3.213.164 bytes brutos. Tamanho/alinhamento ZIP do futuro APK, JNI/OCR/qualidade e RAM nos aparelhos seguem pendentes.

[Integração e limites](docs/OPENCV_P20261117_1.md) · [Evidências](integration/opencv-integration/20261117/README.md).

## Desenvolvimento · P20261116.3 — 16/11/2026

**Estado:** correções para a próxima versão; sem novo APK ou Release.

- Decodificação raw/gzip limitada a 1/8 do heap máximo da VM, até 64 MiB de conteúdo descomprimido; cancelamento e fechamento/CRC preservados. O limite pode recusar backups legítimos maiores e não garante ausência de OOM.
- Validação inicial da restauração movida para IO, com carregamento, ação bloqueada enquanto pendente e mensagem específica para excesso.
- Criação automática recusa snapshot acima do orçamento antes de criar/podar arquivos ou mudar a data; exportação manual continua disponível. Snapshot/serialização ainda podem ter pico de memória.
- Três falhas reproduzidas; 38 controles focados aprovados, 21 casos novos. 932 testes do app executados/aprovados e 85 anteriores de domain/UP-TO-DATE: 1.017 relatórios sem regressões. Overlay4/empacotamento27/comparador21 aprovados.
- OpenCV oficial 4.12.0 inspecionado: ARM32/ARM64, minSdk21, PT_LOAD ARM64 de pelo menos 16 KiB e 59 referências Java presentes. Troca não integrada nem executada em aparelho; diferença bruta dos quatro binários ARM de +3.213.164 bytes, sem medir APK novo.

[Escopo e limitações](docs/LEITURA_BACKUPS_P20261116_3.md) · [Evidências](integration/backup-read-budget/20261116/README.md).

## Desenvolvimento · P20261116.2 — 16/11/2026

**Estado:** auditoria após a beta.11 pública; correções para uma próxima versão. Sem novo APK ou Release.

- Tamanho do manifesto passa pelas telas e pelo WorkManager até o downloader. Respostas inconsistentes/excessivas, cache e parciais respeitam o total antes da promoção; SHA-256 permanece exigido no fluxo oficial.
- Trechos HTTP 206 completos continuam no offset seguinte até completar o arquivo; truncamentos preservam a retomada.
- Três falhas reproduzidas antes da correção; 37 controles focados aprovados, dez novos. 911 testes do app beta e 85 de domain release executados/aprovados, total 996, sem casos anteriores ausentes. 4 testes de overlay, 27 de empacotamento e 21 do comparador aprovados.
- Inspeção do APK público identifica duas bibliotecas ARM64 com PT_LOAD abaixo de 16 KB; compatibilidade em sistema 16 KB permanece a verificar. Bibliotecas nativas ocupam 192.286.636 bytes, 74,1% do APK.
- Decoder de backups sem limite explícito de descompressão registrado para próxima correção. Quatro coordenadas Maven consultadas no OSV, sem avisos retornados; não é certificação do código nativo ou do grafo inteiro.

[Achados e próximos passos](docs/AUDITORIA_POS_BETA11_P20261116_2.md) · [Evidências](integration/post-beta11-audit/20261116/README.md).

## Desenvolvimento · P20261116.1 — 16/11/2026

**Estado:** APK interno beta.11/código 112 gerado e verificado; sem Release pública.

- Variante `beta` conserva o ID `.dev` e certificado da beta.10, com depuração, testOnly e profiling por shell desativados. R8/remoção de recursos permanecem desativados para preservar o carregamento dinâmico já exercitado. Sobre identifica o canal Beta.
- APK universal ARM32/ARM64 de 259.481.310 bytes; manifesto, identidade, revisão, marca e bibliotecas conferidos. Oito DEX/68.658 classes sem sandbox, harnesses ou bibliotecas JVM de teste; worker OCR Dbnet preservado. O pacote anterior foi preservado e recusado pelos novos verificadores.
- Compilação final aprovada em 3min42s; 901 testes do app beta executados/aprovados, mais 85 de domain release aprovados antes da retomada e UP-TO-DATE no final. Total 986 sem falhas/skips ou casos anteriores ausentes; 4 testes de overlay, 27 de empacotamento e 21 do comparador aprovados. A primeira montagem parou por limite de disco após os testes; a retomada usou os mesmos fontes.
- Exportador exige manifesto anterior e código crescente. Comparador seleciona as tarefas reais beta/release e recusa relatórios selecionados ausentes. Guias do pacote agora descrevem a beta.11 e a sandbox pausada/retirada.
- Atualização e dados no aparelho, SAF/SQLite/interface de backups, leitores externos e qualidade/pico de memória no A12/ARM permanecem pendentes. Conta/nuvem e sandbox continuam adiadas.

[Escopo](docs/DISTRIBUICAO_BETA_P20261116_1.md) · [Evidências filtradas](integration/distribution/20261116/README.md).

## Desenvolvimento · P20261115.5 — 15/11/2026

**Estado:** continuação da beta.11/código 112, na frente de leitura/OCR/tradução. Sem novo APK ou Release.

- Cancelar o await podia liberar/trocar o motor de OCR ou fechar um cliente enquanto a Task do SDK ainda estava pendente. A proteção compartilhada aguarda o processamento iniciado terminar e reconfere o chamador antes de entregar o resultado.
- OCR de página inteira/faixas e tradução de quadrinhos/documentos usam o limite; cancelamento não é tratado como motivo para outra inferência. Checkpoints protegem também o percurso/aplicação de cache. Downloads de modelos continuam canceláveis; não há modelos/dependências/processos/opções novos.
- Três falhas reproduzidas com Tasks reais/coordenador de produção e motor de controle. Compilação aprovada; 901 testes do app aprovados (12 novos), mais 85 anteriores de domain/UP-TO-DATE. Nenhum caso anterior ausente. Overlay4/empacotamento16 aprovados; dois controles Android compilados, não executados.
- Não foi executada inferência/modelo nessa validação. Diagnóstico A12/ARM, qualidade e medições de memória/desempenho continuam pendentes. A proteção não acrescenta timeout capaz de interromper uma Task nativa que não conclua.

[Escopo](docs/CANCELAMENTO_MLKIT_P20261115_5.md) · [Evidências filtradas](integration/mlkit-cancellation/20261115/README.md).

## Desenvolvimento · P20261115.4 — 15/11/2026

**Estado:** continuação da beta.11/código 112, na frente de backups. Sem novo APK ou Release.

- Restaurar um backup antigo podia reduzir a última página de um capítulo em leitura ou ignorar uma página posterior quando o capítulo local já estava concluído. A mesclagem passa a manter a maior página e preservar lido/marcador.
- Três regressões reproduzidas com SQLite real antes da correção. Novos controles usam esquema, repositórios, transações e criadores de produção em banco temporário em arquivo, incluindo reabertura, idempotência, histórico/acompanhamento, rollback e reexportação de dois exemplos sintéticos upstream.
- Compilação do app/instrumentação aprovada; 889 testes do app e 85 de domain executados e aprovados: 974, incluindo 16 novos. Nenhum caso anterior ausente; overlay4/empacotamento16 aprovados. Dois controles Android compilados, ainda não executados.
- Driver adicional exclusivo dos testes JVM; sqlite-jdbc ausente de releaseRuntimeClasspath. Esquema SQL/Protobuf inalterados. SQLite/interface Android, aparelhos e troca pela UI de leitores externos seguem para a validação final.

[Escopo](docs/BACKUPS_SQLITE_P20261115_4.md) · [Evidências filtradas](integration/backup-sqlite/20261115/README.md).

## Desenvolvimento · P20261115.3 — 15/11/2026

**Estado:** continuação da beta.11/código 112, na frente de armazenamento. Sandbox arquivada/retirada; conta/nuvem adiadas; sem novo APK ou Release.

- Tela de armazenamento mostra cópias interrompidas e pastas no formato antigo de importação, com nomes, tamanhos conhecidos, situações de revisão e orientação para repetir o original quando houver cópia completa compatível.
- Inventário somente leitura, sincronizado com a publicação. Limites, falhas de acesso e tamanhos desconhecidos aparecem como resultado parcial. A classificação por metadados não substitui a conferência completa do conteúdo feita pelo importador.
- Pastas incompletas, antigas ou desconhecidas ficam preservadas. Nenhuma exclusão, movimentação ou limpeza automática de cópias locais foi acrescentada. Validação e limites na evidência; aceites finais de SAF/interface/aparelhos e pico continuam pendentes.

- Compilação do app/instrumentação aprovada; 873 testes do app aprovados (22 novos), mais 85 anteriores de domain. Nenhum caso anterior ausente. Quatro testes de overlay e 16 de empacotamento aprovados; dois cenários Android novos compilados para a rodada final.

[Escopo](docs/REVISAO_IMPORTACOES_P20261115_3.md) · [Evidências filtradas](integration/import-review/20261115/README.md).

## Desenvolvimento · P20261115.2 — 15/11/2026

**Estado:** sandbox arquivada e removida dos fontes compilados da beta.11/código 112. Sem novo APK ou Release.

- Executor, IPC, serviço/tela, preferências/cookies isolados, componentes de apoio e ramificações de integração retirados. Nenhuma flag reativa o executor. A branch de arquivo conserva o checkpoint anterior.
- Aviso único com as duas caixas mantido; seleções/quarentenas antigas preservadas para migração e revisão. O texto de revisão não promete mais execução isolada. OCR, assinatura/integridade e dados privados existentes preservados.
- Compilação do app/instrumentação aprovada e ausência de classes/componentes conferida nos JARs/manifestos. 851 testes do app aprovados, mais 85 anteriores de domain; os 94 testes exclusivos da sandbox foram arquivados com o executor, e todos os demais casos anteriores permanecem. Quatro testes de overlay e 16 de empacotamento aprovados. Redução do APK ainda não medida.

[Arquivamento e escopo](docs/ARQUIVAMENTO_SANDBOX_P20261115_2.md) · [Evidência filtrada](integration/sandbox-removal/20261115/README.md).

## Desenvolvimento · P20261115.1 — 15/11/2026

**Estado:** continuação da beta.11/código 112, na frente de armazenamento. Sandbox pausada; conta/nuvem adiadas; sem novo APK ou Release.

- Repetir uma inclusão pode retomar a cópia completa ainda em pasta temporária, após conferir protocolo, bytes e metadados, sem outra cópia do payload pelo importador. Título/metadados guardados são preservados.
- Falhas de rename/indexação e cancelamento conservam dados preexistentes. Pastas ambíguas, conteúdo divergente ou arquivos extras ficam para revisão; resíduos parciais e legado não são apagados automaticamente.
- Três falhas reproduzidas antes da correção; 945 testes do app aprovados (14 novos), mais 85 anteriores de domain. App/instrumentação compilados; quatro testes de overlay e 16 de empacotamento aprovados. Dois cenários Android compilados para a rodada final.

[Escopo](docs/RECUPERACAO_IMPORTACOES_P20261115_1.md) · [Evidências filtradas](integration/import-recovery/20261115/README.md).

## Desenvolvimento · P20261114.4 — 14/11/2026

**Estado:** mudança de escopo da beta.11/código 112. Sandbox pausada pelo usuário; quatro frentes ativas: armazenamento, backups, leitura e distribuição. Conta/login Google/nuvem adiados.

- Código experimental preservado, ativação/serviço/tela desabilitados. Seleções antigas aguardam revisão antes da mudança para execução normal.
- Aviso geral único antes de instalações/atualizações no app, com as caixas obrigatórias “Estou ciente” e “Terei cuidado, relaxa”. Aceite local, não exportado/restaurado em backup. Abrange lotes e novels; assinatura/integridade/revisão de repositórios continuam independentes.
- 931 testes do app aprovados (12 novos), mais 85 anteriores de domain; nenhum ausente na comparação. App/instrumentação compilados, manifesto mesclado inspecionado, quatro testes de overlay e 16 de empacotamento aprovados. Dois cenários Android novos compilados; três classes de testes da sandbox explicitamente pausadas.
- Desativação não é medição de redução do APK. Sem novo pacote do app ou Release; testes pessoais na consolidação final.

[Decisão e comportamento](docs/PAUSA_SANDBOX_E_AVISO_P20261114_4.md) · [Evidências filtradas](integration/extension-risk-notice/20261114/README.md).

## Desenvolvimento · P20261114.3 — 14/11/2026

**Estado:** continuação da beta.11/código 112. Testes pessoais na consolidação final, conforme pedido; sem novo APK do app ou Release. Conta/login Google/nuvem permanecem adiados.

- Botões locais de Preference padrão passam a pedir confirmação e executar listener síncrono no worker, sem HTTP. Estado/hierarquia/token são reconferidos e alterações fora da fonte são recusadas. Falha/false não confirma alterações; não há repetição automática.
- Campos e backups não disparam ações. Intents, telas personalizadas, callbacks assíncronos, OAuth e novels continuam pendentes.
- 919 testes do app aprovados (15 novos), mais 85 anteriores de domain; nenhum ausente na comparação. App e instrumentação compilados, quatro testes de overlay e 16 de empacotamento aprovados. Fixture DEX ampliada e seis cenários Android compilados para a rodada final.

[Escopo](docs/SANDBOX_ACOES_LOCAIS_P20261114_3.md) · [Resultados filtrados](integration/sandbox-actions/20261114/README.md).

## Desenvolvimento · P20261114.2 — 14/11/2026

**Estado:** continuação da beta.11/código 112, sem novo APK ou lançamento. Conta/login Google/nuvem permanecem adiados.

- Cache de documentos sem tamanho/data positivos passa a identificar o conteúdo pelos bytes, evitando devolver uma cópia antiga da mesma URI ou ocultar falha do provedor. Conteúdo igual pode reutilizar o cache sem substituir cópias abertas.
- Preparação fica protegida da limpeza até o pin do arquivo final. Caminho rápido por metadados positivos continua disponível; tamanho e metadados são reconferidos na primeira cópia.
- Quatro regressões reproduzidas antes da correção; 904 testes do app aprovados (14 novos), mais 85 anteriores de domain. Core/app/instrumentação compilados; quatro testes de overlay e 16 de empacotamento aprovados. Dois cenários Android compilados aguardam execução.
- Releitura/temporário adicionais exigem medição no A12/ARM; não há promessa de desempenho, pico menor ou detecção de metadados positivos incorretos.

[Escopo](docs/CACHE_DOCUMENTOS_P20261114_2.md) · [Resultados filtrados](integration/document-cache/20261114/README.md).

## Desenvolvimento · P20261114.1 — 14/11/2026

**Estado:** continuação da beta.11/código 112, sem novo APK ou lançamento. Conta/login Google/nuvem permanecem adiados.

- Restauração aguarda categorias antes de remapear configurações e registrar obras; erro ou cancelamento nessa fase impede as seguintes. As demais etapas continuam concorrentes depois dessa dependência.
- Oito regressões reproduzidas antes da correção. Na versão final, 890 testes do app passaram (11 novos); mais 85 de domain já aprovados/UP-TO-DATE, sem ausentes na comparação. App e instrumentação compilados, quatro testes de overlay e 16 de empacotamento aprovados.
- Backups sintéticos Tachiyomi/Mihon foram decodificados até a fronteira de persistência, que é simulada nos testes. Sem mudança em SQL ou formato de backup; banco Android real, interface/aparelhos e ida/volta em leitores externos permanecem pendentes.

[Escopo](docs/RESTAURACAO_CATEGORIAS_P20261114_1.md) · [Resultados filtrados](integration/backup-restore/20261114/README.md).

## Desenvolvimento · P20261113.7 — 13/11/2026

**Estado:** candidata beta.11/código 112, sem novo APK ou lançamento. Conta/login Google/nuvem adiados pelo usuário.

- Novas importações idênticas reutilizam a publicação verificada; nome igual com bytes diferentes continua separado. O prefixo de pasta é legível e o marcador não interfere nos metadados nativos.
- Falha no registro da biblioteca pode ser retomada sem outra cópia. Favoritos existentes conservam identidade, organização e progresso; cópias editadas não são sobrescritas.
- Três falhas reproduzidas antes da correção; 879 testes do app passaram (18 novos), mais 85 de domain já aprovados/UP-TO-DATE. App e instrumentação compilados, quatro testes de overlay e 16 de empacotamento aprovados. Dois cenários Android aguardam dispositivo.

[Escopo e limites](docs/IMPORTACAO_REPETIDA_P20261113_7.md) · [Evidências](integration/document-import/20261113/README.md).

## Desenvolvimento · P20261113.6 — 13/11/2026

**Estado:** continuação da beta.11/código 112, sem outro APK ou lançamento.

- Login copia também cookies existentes em /account e outros caminhos para o perfil exclusivo, restringindo domínios ao host escolhido. Colisões são recusadas.
- Consultas locais cobrem os caminhos iniciais e páginas navegadas. Snapshots parciais não apagam sessões não observadas; capturas contraditórias não gravam. Limites e revogação mantidos.
- Quatro falhas reproduzidas antes da correção; 63 focados e 861 testes do app aprovados (16 novos), além de quatro de overlay e 16 de empacotamento. App/instrumentação compilados; três cenários Android aguardam aparelho. Com domain UP-TO-DATE, relatórios somam 946 sem falhas/skips.

[Escopo e limites](docs/LOGIN_COOKIES_P20261113_6.md) · [Evidência](integration/login-cookies/20261113/README.md).

## Desenvolvimento · P20261113.5 — 13/11/2026

**Estado:** continuação da beta.11/código 112; sem novo APK ou lançamento.

- Listas simples e múltiplas preparam opções síncronas no worker e abrem diálogos próprios do host. A gravação reconstrói opções/listeners em worker novo e rejeita formulários desatualizados.
- Preparação limita HTTP a GET/HEAD e exige snapshot de preferências inalterado. Ações consumidoras, callbacks assíncronos, escrita na preparação e interfaces personalizadas permanecem pendentes.
- App e instrumentação compilados; 845 testes do app aprovados (12 novos), quatro de overlay e 16 de empacotamento. Seis cenários Android compilados, aguardando dispositivo. Com domain UP-TO-DATE, relatórios somam 930 sem falhas/skips.

[Escopo e limites](docs/SANDBOX_DINAMICO_P20261113_5.md) · [Evidência](integration/sandbox-dynamic/20261113/README.md).

## Desenvolvimento · P20261113.4 — 13/11/2026

**Estado:** continuação da beta.11/código 112, sem lançamento. O APK interno anterior permanece P20261113.3.

- Controles SeekBarPreference em configurações de fontes isoladas, com gravação assíncrona e callbacks no worker. Aceitam faixas negativas/fixas e conservam o incremento de teclado do AndroidX.
- Contrato de tela compartilhado entre validação, edição e importação explícita: tipos estritos, limites com proteção de overflow e rejeição de formulário antigo quando opções mudam.
- 833 testes do app passaram, incluindo 12 novos; relatórios com domain somam 918 sem falhas/skips. Compilação real do app e de instrumentação aprovada, quatro testes de overlay e 16 de empacotamento aprovados.
- Fixture sintética ampliada e três cenários Android compilados. Sem dispositivo/emulador conectado para executá-los.

[Comportamento e limites](docs/SANDBOX_CONTROLES_P20261113_4.md) · [Evidências](integration/sandbox-numeric/20261113/README.md).

## Continuação · P20261113.3 — recuperação da assinatura — 13/11/2026

- Keystore original recuperado por transporte criptografado; certificado exportado diretamente confere com a beta.10. Configuração local privada e ignorada pelo Git; nenhum material secreto publicado.
- APK interno universal ARM32/ARM64 gerado e verificado com a assinatura original da beta.10 (272.970.356 bytes). Sem lançamento público ou aceite de atualização no aparelho.
- Empacotamento exclui intermediários de emulador e o verificador de marca distingue os ícones de conquistas dos atributos da application. Três regressões reproduzidas, 16 testes de empacotamento e quatro de overlay aprovados.

[Recuperação e validação](integration/signing-recovery/20261113/README.md).

## Desenvolvimento · P20261113.3 — 13/11/2026

**Estado:** candidata beta.11/código 112, sem lançamento. Compilação Android e 906/906 testes JVM passaram; APK bloqueado por espaço e assinatura original não localizada.

- Transferência de cookies preserva atualizações HTTP concorrentes e rejeita conflitos de forma atômica. Login aguarda a preparação de cookies, confere o perfil e move armazenamento cifrado para IO.
- Dependências do widget alinhadas às versões já usadas pelo app e WebKit declarado diretamente. Testes locais usam o transporte JVM oficial do OkHttp; produção mantém Android.
- Exportador verifica identidade/assinatura contra manifesto anterior quando solicitado; quatro regressões novas e 47 testes focados passaram, além de quatro de overlay e 13 de empacotamento.
- Nenhum dos 880 casos históricos desapareceu;26 casos novos passaram. Sem aceite de aparelho ou APK concluído. A chave criada neste ambiente difere da assinatura da beta.10; não distribuir como atualização.

[Evidências e bloqueios](integration/build-validation/20261113/README.md).

## Desenvolvimento · P20261113.2 — 13/11/2026

**Estado:** candidata da beta.11/código 112; sem publicação. Compilação Android continua bloqueada por Google Maven HTTP503.

- A limpeza automática preserva arquivos cujos nomes contêm datas impossíveis. Nomes antigos e atuais com datas válidas continuam aceitos.
- 43 testes JVM focados passaram: 26 anteriores, nove existentes de integridade da escrita, dois de namespaces de fontes e seis novos de retenção. Dois casos reproduziram a falha antes da correção.
- O aviso de login descreve o escopo dos cookies, sem prometer mediação completa da rede do WebView.

[Evidências e limites](integration/backup-safety/20261113/README.md).

## Desenvolvimento · P20261113.1 — 13/11/2026

**Estado:** candidata da beta.11/código 112, sem lançamento; compilação Android bloqueada no download de dependências Google (HTTP503). A beta.10 pública permanece igual.

- Primeira integração de login HTTPS para fontes isoladas, com perfil WebView separado, confirmação e transferência limitada de cookies. Sem fallback ao navegador global. OAuth externo/Cloudflare genérico e aceite real continuam pendentes.
- Verificação consultiva de espaço durante a importação e antes da cópia para biblioteca em volume local, preservando original e cancelamento.
- 26 testes JVM focados, quatro verificações de aplicação do overlay e nove de empacotamento passaram. Isso não aprova a atividade Android nem todo o aplicativo.

[Escopo e limites](docs/LOGIN_E_ARMAZENAMENTO_P20261113_1.md) · [Checklist da beta.11](docs/BETA11_CHECKLIST.md).

## Desenvolvimento · P20261112.1 — 12/11/2026

**Estado:** revisão da beta.11/código 112, sem lançamento. A beta.10 pública permanece intacta.

- Doze conquistas em quatro caminhos alternativos: pontos de leitura, obras na biblioteca, obras iniciadas e obras concluídas lidas. Uma condição basta para liberar cada grimório.
- Progresso e disponibilidade na Jornada e na Aparência; marcos permanentes e restauração de cosméticos sem revogar conquistas locais por um backup mais antigo.
- Contagem sobre a biblioteca lógica sem consultas extras às fontes; publicação em andamento não é conclusão. Formato de backup existente preservado.
- Refinamento das artes: recorte transparente do grimório inicial e livros maiores nos atalhos. Recursos somam 414.354 bytes.

[Critérios e limites](docs/CONQUISTAS_GRIMORIOS_P20261112_1.md), [evidências](integration/grimoire-achievements/20261112/README.md).

## Desenvolvimento · P20261111.2 — 11/11/2026

**Estado:** revisão da beta.11/código 112, sem lançamento. A beta.10 pública permanece intacta.

- Nova coleção de quatro ícones ilustrados: Grimório Polaris, trevo de três folhas, quatro folhas amado pela mana e cinco folhas com visual sombrio.
- Nomes e fundos acompanham as artes; aliases, seleção salva, desbloqueios e marcos de 900/4.500/9.000 pontos são preservados.
- Originais gerados e hashes arquivados. Recursos Android somam 443.012 bytes; sem dependências, modelos ou esquemas novos.

[Artes e regras](design/polaris-grimoires/20261111/README.md), [implementação e limites](docs/ICONES_GRIMORIOS_P20261111_2.md).

## Desenvolvimento · P20261111.1 — 11/11/2026

**Estado:** revisão da beta.11/código 112, sem lançamento. A beta.10 pública permanece intacta.

- Substitui os quatro ícones geométricos por ilustrações de coruja, raposa boreal, dragão e lobo estelar. O original fica disponível; alternativas liberam por pontos de leitura, sem gasto e preservando escolhas anteriores.
- Mantém cookies HTTP separados por pacote/assinatura, compartilhados pelo intermediário de rede e pelas imagens. Cookies persistentes usam cifragem autenticada do Android Keystore; temporários permanecem na memória.
- Acrescenta limpeza confirmada da sessão da extensão, revogando clientes antigos e respostas atrasadas. Não importa o navegador global nem inclui cookies no backup da biblioteca.
- Mantém as preferências básicas e filtros isolados da revisão P20261110.3. Login por WebView, controles personalizados, fontes reais, aceite ARM e ida/volta em leitores externos continuam pendentes.

[Comportamento e limites](docs/SESSOES_E_ICONES_P20261111_1.md), [artes](design/polaris-guardians/20261111/README.md) e [validação](integration/sessions-icons/20261111/README.md).

## Desenvolvimento · P20261110.2 — 10/11/2026

**Estado:** revisão da beta.11/código 112, sem lançamento. A beta.10 pública permanece intacta.

- Revalida os capítulos nativos de associações existentes nas consultas e antes de gravar o vínculo. Incompatibilidades deixam as edições visíveis separadamente, com recuperação automática quando voltam a ser compatíveis.
- Exige a mesma temporada, volume e parte para complementar faixas adjacentes; usa critérios compartilhados de catálogo e numeração.
- Corrige separar/permitir novamente quando a obra principal está fora dos favoritos, preservando a escolha de mantê-la fora da biblioteca.
- Prepara metadados e perfis de numeração uma vez por edição, reduzindo trabalho repetido por capítulo.

[Revisão, evidências e limites](docs/REVISAO_BIBLIOTECA_P20261110_2.md). Não há promessa de identificar toda renumeração nem de desempenho já aprovado nos aparelhos.

## Desenvolvimento · P20261110.1 — 10/11/2026

**Estado:** revisão da beta.11/código 112, sem lançamento. A beta.10 pública permanece intacta.

- Associação conservadora das edições favoritas já existentes e apresentação de uma entrada com capítulos complementares, categorias e progresso lógico.
- Preservação dos registros nativos, IDs, histórico, notas, glossários, rastreadores, pastas de download e formato de backup.
- Acesso às edições vinculadas, separação reversível e respeito à escolha de não associar automaticamente.
- Encaminhamento do leitor, downloads e traduções para a edição original; restauração e atualização limitadas ao registro da fonte.

[Comportamento, evidências e limites](docs/BIBLIOTECA_UNIFICADA_P20261110_1.md). Aceite com provedores reais, downloads e aparelhos ARM ainda pendente.

## 0.1.0-beta.10 · P20261106.1 — 06/11/2026

**Estado:** pré-lançamento público para testes; versionCode 111; Android 8+, um APK universal ARM32/ARM64 de 261.130.442 bytes, com a assinatura anterior.

- Recursos comuns compartilhados no APK; Android seleciona as bibliotecas nativas compatíveis na instalação.
- Lista de capítulos principal salva antes da descoberta de alternativas. Recuperação de fontes após restauração, inclusive obras antigas/concluídas, com amostragem de páginas/imagens e preferência por português entre fontes habilitadas e verificadas.
- Tentativas de outra edição confirmada quando a lista de páginas falha; fonte fixa, modo somente baixados e progresso preservados.
- Menor concorrência/cache em processos com memória limitada e diagnóstico de ABI/processo no Sobre.
- Inspeção preventiva, quarentena e aprovação por versão exata; confiança interna não importada de backups. A sandbox completa ainda não está integrada.

738 testes JVM: 721 aprovações e as mesmas 17 falhas preexistentes. 31 casos novos, 13 controles de empacotamento/overlay e seis controles Android isolados passaram. Sem aceite completo em celulares; falha do A12 ainda sem causa confirmada. A exportação de capítulos mesclados para Mihon/Tachiyomi precisa de normalização e teste real: **preserve o backup original**.

[Baixar beta.10](https://github.com/Hailton-Reis/Polaris/releases/tag/v0.1.0-beta.10) · [Notas e limites](docs/versoes/0.1.0-beta.10.md).

## 0.1.0-beta.9 · P20261104.4 — 05/11/2026 (UTC)

**Estado:** pré-lançamento público para testes; versionCode 110; Android 8+, ARM32 e ARM64. Publicado com aceitação física, assistente completo e migração real em banco ainda pendentes.

- Assistente para revisar repositórios e preparar extensões internas em lote, com escolha por biblioteca/idiomas, progresso, cancelamento e repetição das falhas.
- Verificação criptográfica, identidade/certificado vinculados à seleção e proteção contra troca silenciosa de chave de repositório.
- Correções de cedilha Anime Ace, encaixe, caixas escuras e deduplicação das bordas do OCR por faixas.
- Opções dependentes coerentes de OCR e download de atualização recuperável com SHA-256.
- Formato de backup e identificadores preservados; seis testes de codec e duas leituras independentes passaram. Sem garantia para todos os forks; o campo Mihon `nextUpdate` não é preservado.

707 testes JVM: 690 aprovações e as mesmas 17 falhas preexistentes, sem regressões novas. 16 controles Android de tipografia e quatro de segurança passaram em componentes isolados. Isso não aprova o aplicativo completo em celulares. APKs: 199.132.104 bytes ARM64 e 159.334.281 bytes ARM32, com a assinatura da beta.8.

[Baixar beta.9](https://github.com/Hailton-Reis/Polaris/releases/tag/v0.1.0-beta.9) · [Notas, benchmark e limites](docs/versoes/0.1.0-beta.9.md).

## 0.1.0-beta.8 · P20261103.1 — 03/11/2026

**Estado:** pré-lançamento público para testes; versionCode 109; Android 8+, ARM32 e ARM64. Instalação/atualização e consumo em aparelhos físicos continuam pendentes de aceite.

- Uma sequência lógica agrupa Official/Unofficial, preservando progresso e arquivos. Partes, decimais, volumes, temporadas e extras identificados permanecem separados.
- Escolha automática entre catálogos de fontes compatíveis e fonte fixa por obra.
- Retomada, leitor, próximos downloads, atualizações e contagens adotam a mesma identidade de capítulo.
- Cache e traduções separados por edição; escopo do glossário mantido por obra.
- Dedicatória escondida no Sobre e correções de identidade, leitura e OCR acumuladas desde a beta.3.

589 testes JVM: 555 aprovações e as mesmas 34 falhas preexistentes, sem regressões novas. Todos os 42 testes novos passaram. APKs com a mesma assinatura da beta.3 distribuída; acréscimo de 1,60 MiB por APK versus beta.7, sem modelo novo. Descoberta foi testada com provedores simulados; fontes reais e aparelhos permanecem em validação.

[Baixar beta.8](https://github.com/Hailton-Reis/Polaris/releases/tag/v0.1.0-beta.8) · [Notas e validação](docs/versoes/0.1.0-beta.8.md).

## Revisões internas beta.5, beta.6 e beta.7 — 02/11/2026

Estas revisões não foram publicadas como Releases. Suas mudanças integram a beta.8:

- **beta.5 / P20261102.2 / código 106:** edição avançada de tradução desligada por padrão e ferramentas de diagnóstico de leitura.
- **beta.6 / P20261102.3 / código 107:** melhorias de retenção de texto reconhecido e OCR por regiões sobrepostas em páginas longas, inicialmente com ML Kit em inglês.
- **beta.7 / P20261102.4 / código 108:** caminho regional compartilhado por ML Kit e Paddle Small em inglês, com controles de geometria e decodificação limitada. O rascunho permaneceu sem APKs publicados.

As comparações do benchmark usaram controles sintéticos; não aprovam a qualidade de todos os capítulos reais. Nenhum modelo Tiny foi adicionado ao aplicativo.

## 0.1.0-beta.4 · P20261102.1 — 02/11/2026 (UTC)

**Estado:** candidato compilado; versionCode 105. Os APKs da beta.4 ainda não foram publicados nas Releases. Conferência visual no A12 pendente.

- Corrige o nome Yomotsu exibido pelo instalador e pelo Android, aplicando **Polaris**.
- Ícone de estrela e livro no instalador, na tela inicial, na abertura e no Sobre, com ícone temático no Android 13+.
- Preserva identificador e assinatura da beta.3 distribuída, permitindo solicitar atualização dessa instalação.
- Acrescenta uma barreira de exportação que verifica o nome e os ícones no APK compilado.

ARM32, ARM64 e x86_64 tiveram a identidade verificada. A comparação Android mantém 491 aprovações e as mesmas 34 falhas preexistentes; os seis testes do empacotador passaram.

[Notas da revisão](docs/versoes/0.1.0-beta.4.md)

## Apresentação inicial do repositório — 01/11/2026

- Página inicial em português, identidade visual e navegação.
- Análise crítica de armazenamento e distinção entre medições sintéticas e consumo real.
- Guia inicial, roadmap, modelos de relatos e organização das notas de versão.
- Atualização documental inicial, sem recompilação do aplicativo nem publicação de APK.

## 0.1.0-beta.3 · P20261101.3 — 01/11/2026

**Estado:** primeiro pré-lançamento publicado em 01/11/2026 e agora aberto ao público; versionCode 104. Aceite nos aparelhos ainda pendente.

- Sobre com descrição do aplicativo, mantenedor, créditos, versão/revisão, projeto, histórico, Releases, licenças e privacidade.
- Atualizador direcionado ao Polaris, incluindo os builds internos, com busca ao abrir e verificação manual.
- Configurações de busca automática e de versões experimentais; experimentais desativadas por padrão, inclusive no beta.
- Seleção por versão SemVer, código, identificador do app, Android e arquitetura, com manifesto de atualização e SHA-256 do APK.
- Rascunhos ignorados; desativar betas não rebaixa a instalação. A consulta não inicia o download do APK.

O repositório e a Release são públicos, com download sem login no GitHub. O título e a descrição foram adaptados para todas as pessoas que desejam experimentar o beta. Os seis anexos publicados mantêm os tamanhos e hashes SHA-256 conferidos com o pacote verificado. A atualização real no celular e a continuidade da assinatura ainda precisam de validação.

[Baixar o primeiro beta](https://github.com/Hailton-Reis/Polaris/releases/tag/v0.1.0-beta.3).

Os 20 testes novos passaram. A comparação completa registrou 525 testes: 491 aprovações e as mesmas 34 falhas preexistentes, sem novas regressões. Consulta, download e instalação reais ainda não têm aceite nos aparelhos.

[Implementação](https://github.com/Hailton-Reis/Polaris/commit/c54644cf396c816ebeb45bbfa5c619b570984523) · [Como as atualizações funcionam](docs/ATUALIZACOES.md) · [Privacidade e serviços](docs/PRIVACIDADE.md)

## 0.1.0-beta.2 · P20261101.2 — 01/11/2026

**Estado:** candidato compilado ao beta interno; instalação e preparação real dos modelos ainda pendentes nos aparelhos. Sem APK publicado. versionCode 103.

- Preparação automática dos recursos de tradução inglês → português, via mecanismo oficial do ML Kit.
- Espera por rede sem cobrança e condição de espaço do Android; preparação manual disponível com a conexão atual.
- Estado visível em Documentos e pesquisa e nas configurações de tradução, com verificação antes de exibir Pronto.
- Preservação dos idiomas de OCR/saída escolhidos pelo usuário.
- Nova capa ilustrada e página inicial com navegação e apresentação mais claras.

O OCR latino já acompanhava o APK. Os recursos de tradução continuam exigindo conexão inicial; esta versão não os empacota manualmente dentro do APK. Download, agendamento e funcionamento offline ainda precisam de conferência nos aparelhos.

Sete testes novos passaram. A comparação completa terminou com 505 testes: 471 aprovações e as mesmas 34 falhas preexistentes, sem novas regressões. Isso não representa aceite Android.

[Implementação](https://github.com/Hailton-Reis/Polaris/commit/3866531931c7705bd238d83467ce40c497343ba5) · [Como a preparação funciona](docs/INGLES_E_TRADUCAO.md)

## 0.1.0-beta.1 · P20261101.1 — 01/11/2026

**Estado:** candidato compilado ao beta interno; armazenamento total, instalação e qualidade nos aparelhos ainda em avaliação. Sem lançamento publicado nas Releases. versionCode 102.

- Painel de armazenamento com originais, cópias importadas, traduções, caches, dados internos/modelos, APKs e bibliotecas nativas extraídas.
- Meta de 256 MiB para o cache regenerável de documentos, com proteção de arquivos em uso.
- Exclusão do capítulo baixado junto de sua tradução e cache de frases, preservando glossário e correções.
- Roteamento do idioma de OCR pelos metadados conhecidos da fonte; automação global asiática opcional.
- Glossário na tradução textual e proteção de termos CJK sem exigir espaços.
- Fila de tradução mais conservadora para reduzir processamento simultâneo.
- Exportação local de APKs ARM64/ARM32, verificação de assinatura e exemplos originais de idiomas.

**Evidência:** 12 novos testes passaram; comparação total com 498 testes, 464 aprovados e as mesmas 34 falhas preexistentes. Isso não valida a qualidade do OCR nos aparelhos.

[Código desta revisão](https://github.com/Hailton-Reis/Polaris/commit/617aa0b992cc5b5966a6069d6e39eb3ebd50c4e7) · [Notas detalhadas](docs/versoes/0.1.0-beta.1.md)

## P20261031.4 — 31/10/2026

**Estado:** revisão de desenvolvimento compilada; fluxo Android pendente de aceite.

- Organização antes da inclusão de arquivos escolhidos no celular.
- Tipos de conteúdo independentes do formato: mangás, manhwas, quadrinhos, livros, artigos e documentos.
- Categorias existentes, categoria pessoal e agrupamento opcional por formato.
- Cancelamento da seleção antes de copiar o documento para a biblioteca.
- Dez novos testes aprovados, sem novas regressões na comparação registrada.

[Código](https://github.com/Hailton-Reis/Polaris/commit/a6d66d78cc5b0be65a2b113cd15169084d26bcf2)

## P20261031.3 — 31/10/2026

**Estado:** implementação inicial de documentos; validação nativa pendente.

- PDF no leitor de páginas; EPUB/DOCX/TXT em leitura textual por seções.
- Importação local e por link direto, tradução textual e retomada.
- Pesquisa em Crossref, Europe PMC, Gutendex e Open Library.
- Site de pesquisa configurável dentro do aplicativo.
- Dezenove novos testes aprovados, preservando as falhas anteriores do projeto-base.

[Código](https://github.com/Hailton-Reis/Polaris/commit/2b3cc36cf336a5f05aefd8294d44d3204727481d)

## P20261031.2 — 31/10/2026

- Proteção da geometria original nas páginas traduzidas quando o corte de bordas está ativado.
- O mantenedor confirmou que desligar o corte alinhava as traduções salvas na revisão anterior.
- A confirmação do diagnóstico não equivale ao aceite visual da correção automática.

[Código](https://github.com/Hailton-Reis/Polaris/commit/b252b225a32746c1409dbfd084db16982fd1c2fd)

## P20261031.1 — 31/10/2026

- Sincronização do posicionamento da tradução com a imagem paginada.
- Identificação explícita da revisão do Polaris em Sobre.
- O diagnóstico posterior identificou o corte de bordas como causa adicional do desalinhamento.

[Código](https://github.com/Hailton-Reis/Polaris/commit/8a23fa6)

## Revisões de engenharia — 29 e 30/10/2026

- Ação de baixar e traduzir por capítulo, solicitações persistidas e ajuste do encaixe de palavras.
- Ajustes de posicionamento, automação de downloads em inglês e respeito à escolha por obra.
- Catálogo inicial de repositórios e apresentação mais clara dos grupos/versões dos capítulos.

[Código de 29/10](https://github.com/Hailton-Reis/Polaris/commit/87c5ce7) · [Tradução em inglês](https://github.com/Hailton-Reis/Polaris/commit/e 8ef402) · [Descoberta e capítulos](https://github.com/Hailton-Reis/Polaris/commit/582e8c4)

## Como registrar as próximas versões

Cada lançamento deve informar versão, revisão, commit, estado de validação, mudanças, limitações e compatibilidade. Os APKs distribuídos devem trazer seus próprios hashes e assinatura verificada. Os hashes de uma compilação local não devem ser tratados como hashes universais de qualquer recompilação.

Não atribuir datas de lançamento ou status de estabilidade a revisões que foram apenas compiladas.
