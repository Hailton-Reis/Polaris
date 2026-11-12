# Biblioteca unificada — P20261110.1

Revisão de desenvolvimento da beta.11/código 112, posterior a ed2c5e1. A beta.10 pública, main, tag e assets permanecem inalterados. [Comportamento, preservação e limites](../../../docs/BIBLIOTECA_UNIFICADA_P20261110_1.md).

A biblioteca associa edições favoritas corroboradas e projeta uma entrada sem apagar os registros nativos. Capítulos lógicos, categorias e histórico recente são agregados; capítulos, posição parcial e armazenamento mantêm o dono original. A associação é recíproca e transacional, usando fonte/URL para sobreviver a IDs novos. É possível separar edições e permitir novamente a associação. Restauração, atualização por fonte e migração continuam consultando somente capítulos nativos.

## Verificação

- **837/837 testes JVM passaram**, com todos os 811 casos anteriores presentes e 26 novos, sem falhas ou skips. Os novos casos cobrem associação/restauração por fonte/URL, reciprocidade, mudança de metadados, homônimos, autores genéricos e pontes de autoria, conflitos de fonte fixada, preferência de separação, fonte fixada em inglês antes da preferência automática por português sem trocar o capítulo aberto, preservação de IDs/posição, PT antes de EN, colisões de URLs, contagens/categorias, limite de lotes, nova tentativa concorrente e fronteira nativa das consultas. [Comparação](unit-comparison.json) e [JUnit](junit).
- **13 controles passaram:** quatro de aplicação/deriva/idempotência/CRLF/gate do overlay e nove do empacotador. A aplicação limpa também exige o novo modelo e teste Android, preservando a remoção do manager/logo legado.
- **17 testes Android passaram em API26 x86_64:** os 12 componentes anteriores e cinco novos casos de banco real. Usam o esquema gerado, driver SQLite e repositórios de produção, sem banco pessoal, conta ou provedor real. Verificam associação com dados intactos, rejeição de snapshot obsoleto, rollback completo quando um trigger aborta a segunda gravação, separar/permitir novamente e exportação Protobuf/restauração com IDs novos. O teste de restauração existente usa a mesma URL `/one` em dois donos e comprova que atualizar um não altera o outro. [Instrumentação](android-final.log).
- **369 caminhos do overlay conferem com os fontes compilados, incluindo cinco exclusões cumulativas.** São 23 caminhos novos e 19 modificados nesta etapa contra a revisão anterior. [Hashes](compiled-overlay.json) e [delta](source-delta.json).
- Os APKs são debug/x86_64 para componentes, não distribuição para celular. SELinux e verificação de APK ficam ativos. Antes da instrumentação, houve ANR do System UI no boot e de um serviço SystemJobService da instalação anterior enquanto o APK era substituído. O diálogo foi fechado e o processo de fundo do app encerrado, sem limpar dados ou mudar código. A janela ativa voltou ao launcher antes dos testes; [registro do ambiente](system-ui-recovery.json). Isso mantém o desempenho/inicialização completa como pendência, sem atribuir causa ao novo código ou aprová-lo. As dependências e modelos de OCR não mudaram; a consulta anterior de vulnerabilidades não foi repetida nesta etapa.

[Resultado estruturado](TEST_RESULTS.json) e [hashes das evidências](SHA256SUMS.txt).

## Reprodução

Aplique os overlays ao upstream fixado conforme os scripts do projeto, usando JDK21/SDK37. Rode os testes dos módulos `domain`, `data`, `source-api` e `app`, depois `:app:assembleDebug :app:assembleDebugAndroidTest`, com os init scripts arquivados. O runtime init configura apenas x86_64 e host de componentes; não o use para empacotar celulares.

Depois de instalar os dois APKs num emulador API26, o novo componente pode ser executado isoladamente:

```sh
adb -s SERIAL shell am instrument -w -r \
  -e class eu.kanade.tachiyomi.polaris.LibraryConsolidationAndroidTest \
  app.mihon.tachiyomiat.dev.test/eu.kanade.translation.recognizer.OcrComponentTestRunner
```

Essa seleção deve concluir com `OK (5 tests)`. O registro arquivado inclui também os componentes anteriores e deve concluir com `OK (17 tests)`; exit0 do ADB sozinho não comprova aprovação.

## Limites

A prova de banco/backup usa dados sintéticos com os componentes reais, sem captura nova de biblioteca restaurada. Não prova existência de arquivos, navegação completa pelo leitor, preferências da tela de obra, desempenho em ARM ou compatibilidade por interface/banco de outro aplicativo. Esses aceites continuam pendentes. Outros leitores podem mostrar as edições nativas separadas; o backup mantém os dados em vez de impor o agrupamento do Polaris. A associação não busca conteúdo ilimitadamente nem junta correspondências ambíguas.

A confirmação confere numeração antes de associar. Revalidar automaticamente uma renumeração posterior dentro de grupos já formados ainda é desenvolvimento pendente; a separação manual permanece disponível.
