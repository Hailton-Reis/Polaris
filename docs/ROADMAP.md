# Próximos passos do Polaris

O roadmap indica prioridades e critérios de verificação. Não representa prazo de entrega nem recurso já aprovado.

## Prioridades atuais — decisão P20261114.4

Sandbox inteira pausada, [arquivada e removida dos fontes compilados](ARQUIVAMENTO_SANDBOX_P20261115_2.md) nesta beta. Não ampliar controles, ações, login isolado, OAuth/Cloudflare ou novels isoladas agora. Esses itens históricos não bloqueiam a conclusão da beta. O [aviso único de extensões](PAUSA_SANDBOX_E_AVISO_P20261114_4.md) exige as duas confirmações pedidas pelo usuário, sem substituir verificações de assinatura/integridade.

As quatro frentes ativas são armazenamento, backups, leitura e distribuição. Testes pessoais após consolidação; conta/login Google/nuvem permanecem adiados. Pausar não comprova redução do APK: comparar pacotes equivalentes durante a distribuição.

## Consolidação da beta.11

O [checklist atual](BETA11_CHECKLIST.md) acompanha as frentes autorizadas em 13/11. Proteções de armazenamento/backups têm candidatas verificadas; testes finais e publicação continuam pendentes. As revisões históricas de sandbox abaixo estão pausadas por decisão atual.

Conta do Polaris com login Google e sincronização em nuvem é uma evolução desejada, mas foi **adiada por decisão do usuário**. Não priorizar configuração de Google Cloud ou provisionamento de contas agora. O backup local existente é preservado.

## Estado da auditoria P20261107.1

A [auditoria geral](AUDITORIA_GERAL_P20261107_1.md) separa implementação, prova por componentes e aceite externo. A Jornada Polaris, títulos decorativos, três ícones alternativos e três temas estão implementados na revisão de desenvolvimento. A beta.10 publicada não muda com esta revisão.

Antes de ampliar a distribuição, priorizar:

- Medir abertura de capítulos, memória, armazenamento e processamento no A12/ARM32 e no S20FE/ARM64.
- Validar restauração e continuidade com fontes reais e ida/volta por banco/interface de leitores externos.
- Validar a [biblioteca unificada P20261110.1](BIBLIOTECA_UNIFICADA_P20261110_1.md) com uma biblioteca restaurada e downloads reais nos aparelhos. A associação conservadora está implementada; faltam aceite completo do leitor, desempenho e ida/volta em leitores externos.
- Validar em fontes reais a [revalidação de numeração P20261110.2](REVISAO_BIBLIOTECA_P20261110_2.md), inclusive renumerações semanticamente ambíguas e mudanças durante a leitura. A checagem atual de critérios compartilhados está implementada.
- Validar em fontes reais as [preferências e filtros da sandbox](SANDBOX_PREFERENCIAS_FILTROS_P20261110_3.md) e a [persistência de sessões HTTP P20261111.1](SESSOES_E_ICONES_P20261111_1.md). Login/WebView, integração de perfis do navegador, controles personalizados e novels continuam pendentes.
- Consolidar distribuição não depurável, preservando ID, assinatura e instalação por cima; validar callbacks dos rastreadores em navegador real.

A [continuação P20261114.1](RESTAURACAO_CATEGORIAS_P20261114_1.md) corrige a ordem de restauração entre categorias, configurações e biblioteca. O aceite em SQLite/interface Android e em leitores externos continua pendente.

A [continuação P20261114.3](SANDBOX_ACOES_LOCAIS_P20261114_3.md) acrescenta ações locais padrão na sandbox, com confirmação e sem capacidade HTTP. Telas/ações personalizadas, assincronia, OAuth e novels continuam pendentes. Os testes pessoais ficam para a consolidação final, conforme pedido do usuário.

A [continuação P20261115.1](RECUPERACAO_IMPORTACOES_P20261115_1.md) retoma cópias completas deixadas por publicação interrompida, sem outra cópia do payload pelo importador. Resíduos parciais, legado e medição de pico permanecem abertos.

## Prioridade atual: armazenamento antes da ampliação do beta

- Medir instalação completa, modelos, cópias, renderização e temporários nos aparelhos.
- Verificar espaço insuficiente no volume do cache e no volume da biblioteca.
- Avaliar reaproveitamento de materialização, importação repetida e recuperação de inclusão incompleta.
- Conferir a meta de cache com arquivos em uso e o crescimento dos caches fora dessa meta.
- Validar a limpeza conjunta de download/tradução mantendo o vocabulário.

A [continuação P20261114.2](CACHE_DOCUMENTOS_P20261114_2.md) corrige cache antigo quando tamanho/data estão ausentes. Releitura e temporário adicionais mantêm a necessidade de medir pico e desempenho no A12/ARM.

A [análise crítica](ARMAZENAMENTO.md) explica o que motivou cada prioridade e qual evidência falta.

A [continuação P20261113.7](IMPORTACAO_REPETIDA_P20261113_7.md) trata importações novas repetidas e retomada de publicação válida após falha de registro. Pastas antigas, staging abandonado e aceites físicos permanecem abertos.

## Rodada interna de leitura e tradução

- Instalação/atualização nos sistemas ARM64/ARM32 correspondentes.
- Biblioteca e documentos: seleção manual, categorias, figuras, retomada e título.
- Paginado/faixa longa: alinhamento da tradução, corte de bordas e zoom.
- Inglês, japonês horizontal/vertical, chinês simplificado/tradicional e coreano.
- Glossário e correções antes/depois de exclusão e novo download.
- Memória, processamento e comportamento em segundo plano nos aparelhos mais modestos.

Os exemplos preparados ajudam a começar. Páginas reais autorizadas e revisão do idioma de origem continuam necessárias para avaliar a qualidade.

## Distribuição e versões

- Manter candidato, beta e estável claramente identificados no histórico.
- Registrar versão, revisão, commit, assinatura, hashes e limitações de cada pacote distribuído.
- Manter notas de versão e instruções de atualização coerentes com os APKs efetivamente disponibilizados.
- Publicar uma Release somente com o estado de validação correspondente; um rascunho permanece rascunho.

## Evolução do leitor

- Melhorias de fidelidade de EPUB/DOCX, navegação e tratamento de documentos complexos.
- Gerenciamento mais claro de modelos e dados regeneráveis.
- Medição e possível redução do pacote de instalação.
- Melhor acessibilidade e desempenho conforme resultados da rodada física.

## Múltiplas fontes

A beta.8 integra agrupamento de edições, seleção automática de catálogos compatíveis e fonte fixa por obra, com testes de provedores simulados. O aceite completo com duas fontes, a ponte de tradução canônica e a evolução de backup seguem os critérios próprios da engenharia. Não são declarados concluídos por esta página ou pelo pacote de leitura local.

Um servidor pessoal continua opcional; o projeto não deve depender dele para a leitura básica.

A [revisão P20261115.3](REVISAO_IMPORTACOES_P20261115_3.md) apresenta importações interrompidas e pastas no formato antigo na tela de armazenamento. Inventário somente leitura, com limites e resultado parcial explícito; arquivos sem origem comprovada continuam preservados para conferência manual. Medição de pico e aceites SAF/aparelhos permanecem para a consolidação final.

A [revisão P20261115.4](BACKUPS_SQLITE_P20261115_4.md) impede que um backup antigo reduza a última página. Acrescenta persistência e reexportação com SQLite real e repositórios de produção em JVM, incluindo rollback/retomada do lote. Driver adicional exclusivo de testes; validação Android/interface e troca em leitores externos permanecem pendentes.

A [revisão P20261115.5](CANCELAMENTO_MLKIT_P20261115_5.md) protege o ciclo de vida das Tasks de processamento ML Kit ao cancelar OCR/tradução: aguarda a Task antes de liberar/trocar recursos e reconfere o chamador antes de entregar resultados. Downloads de modelo continuam canceláveis. Não substitui diagnóstico/medição de memória, qualidade ou desempenho no A12/ARM.
