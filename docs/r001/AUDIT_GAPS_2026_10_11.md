# Polaris — R001: auditoria de lacunas e riscos
**Data:** 11/10/2026 · **Branch:** `r001/multisource-foundation`

## Sumário executivo

**O Spike-001 é uma fundação técnica testada, não um leitor multifonte pronto para uso.** O gate host foi executado neste checkpoint com **116/116 PASS**: 72 Python, 10 SQLite, 34 Kotlin/JVM. Isso valida contratos em ambiente isolado, mas **não** compila o APK Android, não executa extensões reais e não verifica backup/reinstalação. O último Android CI ainda falhou antes de obter runner.

A auditoria acrescentou evidências reproduzíveis de **dois defeitos reais de integração/persistência**; identificou **um defeito de serialização de backup** por revisão completa dos caminhos originais; e confirmou o problema de exclusão total já aberto. Foram corrigidos apenas dois defeitos de baixo risco e com teste reproduzido, sem alterar esquema SQL nem os Spikes 001–024.

## Prioridade para liberar um APK útil

| Ordem | Categoria e achado | Evidência e efeito | Ação |
| --- | --- | --- | --- |
| **P0 — build** | Ainda não há compilação Android integrada nem leitura real de duas fontes | Jobs de GitHub Actions terminam com `runner_id=0`, `steps=[]`. Testes host não substituem SQLDelight/Compose/Gradle. | [#2](https://github.com/Hailton-Reis/Polaris/issues/2): recuperar runner ou provisionar outro host Android; build baseline e patched, B01–B05. |
| **P0 — dados/backup** | Backup não preserva os vínculos de obra virtual | `Backup.kt`, `BackupManga.kt`, `MangaBackupCreator` e `MangaRestorer` do Yomotsu fixado não serializam a tabela `merged`. Um parent sem capítulos próprios restaura sem saber suas fontes. | [#11](https://github.com/Hailton-Reis/Polaris/issues/11): backup versionado, IDs de filho remapeados, ida e volta em dispositivo. |
| **P1 — UX/biblioteca** | Mangá virtual exibe zero capítulos/lidos/marcados na biblioteca | O `libraryView.sq` original conta somente `chapters.manga_id = manga._id`; quatro capítulos reais ligados em dois filhos retornam `0/0/0` no pai. **Reproduzido em SQLite.** | [#9](https://github.com/Hailton-Reis/Polaris/issues/9): projeção correta de dados canônicos/variantes, coerência da view e migração. |
| **P1 — integridade** | Não há unicidade dos vínculos merge→filho | Dois `INSERT` idênticos no `merged` passam e criam duas referências; `mangas` também não tem `UNIQUE(source,url)`, expondo janela de concorrência. **Reproduzida a duplicação de referências**; duplicidade de pais concorrentes ainda é risco. | [#10](https://github.com/Hailton-Reis/Polaris/issues/10): unicidade/upsert/atomicidade e testes de concorrência na engine real. |
| **P1 — ciclo de vida** | `deleteMerge` remove associações, mas mantém o pai virtual | A consulta `DELETE FROM merged WHERE merge_id=?` não exclui `mangas`. Isso interage com a recuperação de criações interrompidas. | [#8](https://github.com/Hailton-Reis/Polaris/issues/8): semântica de remover referência vs obra inteira, com cascata segura. |
| **P1 — uso automático** | Ainda falta descoberta, seleção e atualização automática de filhos | O Spike-001 agrega obras inseridas por depuração; não dispõe de um fluxo completo de UI nem escolhe por estabilidade/idioma/contagem. Background exclui corretamente o pai virtual, mas isso não atualiza filhos não favoritos. | [#4](https://github.com/Hailton-Reis/Polaris/issues/4) + [#5](https://github.com/Hailton-Reis/Polaris/issues/5): clusterização/aliases, ranking, health e refresh planner. |
| **P1 — continuidade** | Estado canônico de capítulos/leitura entre fontes não persiste | IDs reais são preservados (bom para abrir capítulos), mas leitura/marcação da fonte A não é automaticamente mapeada para B; capítulos com o mesmo número podem ser volumes/temporadas distintos. | [#3](https://github.com/Hailton-Reis/Polaris/issues/3): resolução canônica, progresso e aliases; migração 15 **somente após** Android baseline/Spike-001. |
| **P2 — tradução** | Tradução automática e cache canônico integrados ainda não estão prontos | Há pipeline Yomotsu a reutilizar, mas o leitor virtual atualmente só despacha para o filho real; não enfileira/faz cache automático do fallback EN. | [#6](https://github.com/Hailton-Reis/Polaris/issues/6): ponte de tradução, contexto canônico, memória e cache. |
| **P2 — regressão** | Falta a matriz de aparelho e extensão/novel | Teste JVM do tipo `INovelSource` é host-only, não prova abertura/decodificação de páginas, bloqueio de fonte, renovação de sessão ou backup. | [#7](https://github.com/Hailton-Reis/Polaris/issues/7): matriz completa de regressões e evidências B01–B05. |

## Demonstração reproduzível de dois bugs

O script `spikes/spike001/audit/reproduce_known_gaps.py` usa a migração 14 real mais a view original do Yomotsu fixado (blob upstream `8ce19ae1de727f1930ddf47d6b5fc0269ae643a2`). Execute:

```bash
python3 spikes/spike001/audit/reproduce_known_gaps.py
```

Resultado observado: contador da biblioteca virtual `[0,0,0]` versus filhos vinculados `[4,1,1]`; **duas** referências idênticas coexistindo no banco. O script é propositalmente **diagnóstico de falha conhecida**, não teste de aprovação. Não adicionar seus dois indicadores à contagem de testes "PASS" da aplicação.

## Correções desta auditoria, com prova host

1. `CreateMergedManga` agora rejeita entrada vazia com `IllegalArgumentException` legível e rejeita IDs de manga não positivos antes de qualquer acesso ao repositório.
2. `GetMergedChaptersByMangaId.dedupeByPriority` agora usa mapa de proprietário por número de capítulo em vez de `out.any` para cada capítulo, reduzindo a deduplicação de **quadrática para linear** em função do número de capítulos. Preserva números repetidos na mesma fonte, prioridade da fonte vencedora, capítulos não numerados e equivalência `-0.0/0.0`. Não altera ID real `mangaId/chapterId`.
3. Foram acrescentados **4 cenários Kotlin novos**; suíte completa **34/34 PASS**, gate unificado **116/116 PASS** (72 Python, 10 SQLite, 34 Kotlin), em checkout parcial com arquivos originais conferidos por blob SHA no GitHub. **Não é teste Android.**
4. Nenhuma mudança foi feita em `14.sqm`, `merged.sq` ou migração 15: consertar view, índice único e backup exige decisão de compatibilidade e testes na engine real.

## Sequência recomendada

**Primeiro:** solucionar execução Android da issue #2 (runner ou host próprio) e obter build, testes de abertura A+B, novel e exclusão de uma referência. **Depois, antes de versão pública:** corrigir backup (#11), contadores (#9), exclusão completa (#8), unicidade (#10), verificando upgrade/reinstalação. **Em seguida:** implementar etapas canônicas, descoberta, saúde e tradução das issues #3–#6 conforme os Spikes congelados; finalizar a matriz #7. Isso evita confundir muitos testes unitários verdes com um aplicativo pronto.

## Limites de certeza

- **Reproduzidos em SQL:** biblioteca retorna zero; banco aceita referências duplicadas.
- **Comprovado por código fonte:** backup atual não grava nem restaura referências da tabela `merged`; exclusão total só remove associações; falta UI pública de fusão e ranking automático.
- **Riscos que exigem execução real:** concorrência de duas criações simultâneas, crashes de UI, SQLDelight gerado/Gradle, Cloudflare/sessões, desempenho em Android, histórico/capas/contagem final com leitores novel.
- Não há evidência suficiente para afirmar que uma falha do Gradle existe: os jobs de CI nem iniciaram. Não modificar Spikes 001–024 sem incompatibilidade real.

## Seguimento — 11/10/2026: mitigação de duplicatas ao ler capítulos

A auditoria reproduziu mais um bug concreto na camada de leitura: duas associações `merged` ao mesmo `mangaId` produziam capítulos repetidos no modo sem deduplicação e registros de outros pais poderiam influenciar a prioridade de fonte. Correção aplicada em `GetMergedChaptersByMangaId` para normalizar os vínculos em `await` e `subscribe`, sem trocar IDs reais ou mudar a migração 14. Teste antigo falhou antes da correção; quatro novos cenários Kotlin passaram após a alteração. Gate host vigente: **120/120 PASS** (72 Python, 10 SQLite, 38 Kotlin). Evidências no Drive: https://drive.google.com/file/d/1x4NA1OAadA23NaWQpYfVDy08zsLt_El9/view.

**Não encerrar a issue #10**: o banco continua aceitando INSERT duplicado. A correção só impede que referências repetidas/corrompidas afetem a apresentação do leitor; não estabelece UNIQUE, concorrência atômica nem reparação do banco.


## 11/10/2026: mitigação idempotente da persistência sem migração

Os dois métodos gerados a partir de `merged.sq` (`insert` e `insertReturningId`) agora usam `INSERT ... SELECT ... WHERE NOT EXISTS` para evitar criar novas duplicatas ao repetir a mesma vinculação. Os vínculos com `manga_id` nulo são identificados por fonte + URL; o vínculo já existente conserva prioridade e configurações. Uma exclusão intencional ainda permite inserção posterior.

O defeito foi reproduzido **antes** (4 falhas na suíte de 9 testes novos) e corrigido **depois** (20/20 SQLite, incluindo quatro conexões simultâneas). Gate offline atualizado: **130/130 PASS** (72 Python, 20 SQLite, 38 Kotlin). Evidências: https://drive.google.com/file/d/1Ii4t2QUChADw6KjTIVG82dDbe1XMkIS3/view.

**Ressalva:** este guardião pertence às consultas SQL, **não** ao esquema da tabela. Um SQL direto ainda pode gravar repetidos, linhas antigas continuam, e nenhum gerador SQLDelight / APK Android foi executado. A issue #10 segue aberta.
