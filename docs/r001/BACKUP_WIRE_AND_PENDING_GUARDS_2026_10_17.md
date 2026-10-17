# Polaris R001 — backup portable e integridade de pais virtuais — 17/10/2026

## O que foi demonstrado

1. **Bug de campo ProtoBuf 107**: o exportador candidato `BackupCreator.staged.kt` utiliza o argumento nomeado `polaris`, mas os candidatos posteriores `Backup.staged.kt` e `BackupRestorer.staged.kt` usavam `polarisBundle`. Os nomes foram padronizados para **`polaris`**, mantendo o contrato do aplicador `apply_backup_proto_candidate.py` e o valor opcional `null` para backups antigos.
2. **Restauração indevida de fontes pendentes**: o `validateForImport()` anterior admitia `supplementalManga` associado apenas a um link `isPending=true`. O coordenador restauraria a obra real desnecessariamente. A validação exige agora que cada snapshot suplementar tenha ao menos um vínculo resolvido. Um mesmo source+URL pode continuar pendente em uma obra e resolvido em outra.
3. **Duplo pai virtual**: um backup Polaris com `BackupManga(source=6969)` na seção normal importaria primeiro o pai virtual pelo Yomotsu e depois criaria outro pai pelo ledger UUID. O teste reproduziu o risco e a nova `validateSnapshotCoverage()` **recusa o arquivo misto antes de qualquer gravação**. Isto é uma barreira temporária, não um conserto do exportador.

**Bloqueio de produção P0:** o exportador *ainda inclui* pais virtuais na lista de mangás normais, e o pacote portátil não preserva todos os atributos do pai (e.g. categorias, notas). Portanto, a combinação atual exportador/restaurador Polaris pode ser recusada pelo novo preflight; **não usar o caminho em produção até haver migração do pai que preserve todos os metadados, sem duplicação**. O candidato `BackupCreator.staged.kt` também escreve no destino antes do planejamento do backup; deve ser auditado para não remover/sobrescrever backups existentes quando a pré-validação falha. Migration15 permanece inalterada.

## Testes executados localmente, com fonte exata da branch

- `18/18` modelos portáteis existentes, `9/9` novos testes de fonte pendente/duplo pai, `5/5` compatibilidade do campo 107: **32/32 Kotlin/JVM**. `7/7` testes Python do aplicador do modelo ProtoBuf também passaram.
- Reinserida a fonte `BackupPolarisBundle.kt` corrigida nos dois conjuntos anteriores: **53/53 Kotlin/JVM** (restauração rigorosa Yomotsu) e **41/41 Kotlin/JVM** (adaptador transacional com tipos de modelo reais).
- **16/16 testes SQLite** da consulta candidata, executados na mesma rodada.
- **142/142 cenários dos quatro grupos Kotlin+SQLite**, separados: 32+53+41+16. O construtor do bundle (`BackupPolarisBundleBuilderTest.kt`, 19 casos) permanece obrigatório no novo runner, mas **não foi reexecutado nesta rodada**. Seis verificações diretas de consistência de nomes foram aplicadas aos quatro arquivos remotos no GitHub; o teste Python de CI específico ainda depende do runner.
- Evidências da *falha antes da correção*: `before-pending.log` e `before-parent-collision.log`. Evidências posteriores: logs finais `contract-32-final.log`, `lifecycle-53-final.log`, `sqldelight-41-final.log`, `sqlite-16-after.log` e `python-proto-stage.log`.

## Gate e escopo

O host gate possui agora **13 estágios / mínimo configurado de 537 casos** (os 486 existentes + 51 do gate `backup-proto-contract`: 18+19+9+5). O executor `run_model_validation.sh` foi atualizado para compilar o arquivo exato `android-bridge/Backup.staged.kt` e rodar quatro mains; `.github/workflows/domain-spikes.yml` executará também `test_android_bridge_field_contract.py`. **O total 537/537 não foi executado.**

Esta rodada **não gerou classes SQLDelight via Gradle**, não rodou ProtoBuf real, não compilou APK e não modificou produção Android, migration15, nem bancos do usuário. PR #1 segue em DRAFT e issues #2/#10/#11 permanecem abertas.

Repositório: https://github.com/Hailton-Reis/Polaris/tree/r001/multisource-foundation/spikes/spike001/backup/proto-candidate

Handoff: https://github.com/Hailton-Reis/Polaris/blob/r001/multisource-foundation/docs/r001/RESUME_2026_10_15.md

## 17 October 2026 — lossless virtual-parent snapshot partition (23 new tests)

The staged Yomotsu full `BackupManga` already contains notes, categories,
chapters, history, tracking, viewer flags, memo and user metadata.
`spikes/spike001/backup/parent-candidate/` has a standalone **full snapshot**
partition plan: bind original selected local manga ID and canonical parent
UUID; separate source-6969 parent payloads from stock ordinary backups
WITHOUT dropping any field; keep original list indices to prove reversibility.
It refuses orphan/mismatching parents, changed titles/URLs and duplicate UUIDs.
`bash spikes/spike001/backup/parent-candidate/run_tests.sh` ran
**23/23 Kotlin/JVM host cases PASS** with BackupManga/ProtoBuf host doubles.
Source code was checked against pinned BackupManga's source/url/title field
names but not compiled against real Android dependencies.

`backup-parent-split` is now the 14th fail-closed gate, minimum 23.
Aggregate **configured** 560 cases across 14 groups, not executed 560/560.
[GitHub candidate](https://github.com/Hailton-Reis/Polaris/tree/r001/multisource-foundation/spikes/spike001/backup/parent-candidate).
[Drive ZIP](https://drive.google.com/file/d/1Qj-6J0Ie0Be2CVFfhuBt44N5kCdTi5kb/view),
SHA256 `411e5d91333a58386074b4ee11d8044531157ec74bbd0c8c217cf779a563f6af`.

Critical P0 remains: add a versioned archive payload for full parent
snapshots, real ProtoBuf roundtrip, ensure stock path excludes virtual
manga, restore full metadata onto exactly one UUID parent ID inside
reviewed DB operations, safely merge memo JSON and map categories/history.
Keep the preflight guard that refuses duplicate virtual parents.
Migration 15 and production source files untouched.
