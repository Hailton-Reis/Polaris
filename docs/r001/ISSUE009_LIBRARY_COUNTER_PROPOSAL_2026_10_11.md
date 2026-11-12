# Polaris R001 — issue #9: biblioteca multifonte, proposta de contadores

**Data:** 11/10/2026 · **Estado:** SQL candidato e testes concluídos; **NÃO incorporado ao aplicativo**, aguardando SQLDelight/Android.

## Diagnóstico

A `libraryView.sq` do Yomotsu fixado (`kiritsuguxs/yomotsu@0fb80c439ef816eeb50674f1b90af39918b176d8`, blob `8ce19ae1de727f1930ddf47d6b5fc0269ae643a2`) calcula os indicadores com `chapters.manga_id = mangas._id`. O pai virtual do Polaris não tem capítulos próprios: eles continuam ligados aos IDs de origem. Resultado: zero capítulos, lidos e marcados apesar de fontes vinculadas.

## Solução candidata (isolada)

- [`libraryView_candidate.sql`](../../spikes/spike001/audit/libraryView_candidate.sql): substituição completa da view com projeção dos capítulos reais, mantendo `M.*` e os **mesmos nomes e ordem** das colunas extras esperadas pelo mapper Yomotsu.
- Referências inválidas, repetidas ou pertencentes a outro pai não influenciam o contador; fontes ausentes não provocam erro.
- Preserva comportamento original da biblioteca para mangas reais.
- Calcula os contadores da obra virtual segundo o `chapter_sort_mode` configurado no registro raiz: `NONE` e `NO_DEDUPE` contam todos; `PRIORITY` escolhe uma única fonte por número reconhecido (retendo números repetidos na própria fonte e capítulos sem número reconhecido); `MOST_CHAPTERS` e `HIGHEST_CHAPTER_NUMBER` selecionam a fonte vencedora.
- Respeita scanlators excluídos, leitura, marcadores, últimas datas, histórico, categorias e a condição de favorito.
- **Sem copiar** capítulos, leitura, marcadores ou URLs para o pai virtual.

## Resultados testados

```bash
python3 -m unittest discover -s spikes/spike001/audit -p 'test_*library*_candidate.py' -v
python3 -m unittest discover -s spikes/spike001/audit -p 'test_virtual_library_projection.py' -v
```

Os arquivos atuais de teste são [`test_virtual_library_projection.py`](../../spikes/spike001/audit/test_virtual_library_projection.py) (**18/18 PASS**) e [`test_library_upgrade_candidate.py`](../../spikes/spike001/audit/test_library_upgrade_candidate.py) (**7/7 PASS**): **25/25 casos SQLite aprovados** usando o conteúdo exato dos arquivos candidatos publicados.

O ensaio de upgrade recria a view original, confirma que ela apresenta zero para o pai, aplica a migração 14 **original, byte-idêntica à branch** (blob `8f23dc5219f49a0368705ba21d0c4e5a0d7fb1fb`), insere vínculos e só então aplica a [proposta de atualização da view](../../spikes/spike001/audit/migration14_view_candidate.sql). A mudança produz contadores corretos na instalação simulada, preservando linhas de mangas/capítulos, a estrutura de colunas da view e os contadores de mangas comuns. O pacote foi verificado também para testes de sobreposição, desempate, remoção de fontes, fontes indisponíveis e alterações de leitura.

O pequeno teste de desempenho sintético com 20 pais virtuais, três fontes por pai e seis mil capítulos consultou todos os contadores em aproximadamente **0,024 s no SQLite de desktop**. Isso **não é estimativa de desempenho Android**.

## Restrições e riscos antes de aplicar à produção

1. **Não alterar agora** `spikes/spike001/new-files/data/src/main/sqldelight/tachiyomi/migrations/14.sqm`, a view existente do Yomotsu, nem aplicar migração 15 apenas para passar um teste host. Os arquivos acima são candidatos **fora do aplicador atual**.
2. Conferir compatibilidade de `CREATE VIEW ... WITH ... ROW_NUMBER()` com o **SQLDelight do Yomotsu**, suas colunas geradas e o mapper `MangaMapper::mapLibraryManga`.
3. Verificar invalidação da consulta reativa da biblioteca ao modificar linhas `merged` e `chapters`: badges e filtros devem atualizar ao vincular/desvincular e marcar capítulos.
4. Planejar a atualização do banco de **instalações que já executaram a migração 14**. Alterar apenas o arquivo de definição da view ou reescrever 14.sqm não migra instalações existentes; uma migração posterior versionada será necessária quando liberada. Isso deve ser testado junto da issue #2, sem atropelar a migração 15 congelada.
5. Executar casos em um dispositivo com dois títulos reais e capítulos sobrepostos. O modo de deduplicação baseado somente em número de capítulo continuará sujeito às limitações do **modelo canônico**, a resolver em #3 e #4.
6. O custo da consulta quando há centenas de obras virtuais e muitos capítulos precisa de benchmark Android.

**Decisão técnica:** manter o protótipo e os testes na branch, mas **não fechar #9** até existir build Android e uma estratégia de migração comprovada. PR #1 permanece rascunho, issue #2 aberta e migração 15 bloqueada. Não confundir estes 25 testes de uma implementação candidata com os testes de produção do gate host.
