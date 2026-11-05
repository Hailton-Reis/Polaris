# Polaris R001 — auditoria somente leitura antes da migração de vínculos (issues #10/#11)

**Estado: ferramenta de diagnóstico host; NÃO instala migração nem modifica bancos.**

O `polarisRestore.sq` candidato usa índices físicos `UNIQUE` para as referências multifonte e um `polaris_restore_ledger` de UUID. Em bancos antigos, vínculos resolvidos e pendentes podem compartilhar `sourceId+URL`, o mesmo mangá pode ser ligado duas vezes, e pais virtuais podem ter UUIDs já armazenados no `mangas.memo` sem um registro no ledger. Instalar os índices sem uma auditoria pode abortar a migração ou induzir alguém a apagar configurações importantes para fazê-la passar.

## Executar com segurança

Trabalhe **sempre sobre uma cópia consistente e fechada do SQLite do aplicativo**, nunca o banco em uso no Android. Se o banco usar WAL, obtenha a cópia com a API de backup do SQLite ou checkpoint apropriado, e não copiando apenas o arquivo `.db` enquanto estiver aberto. Não publique sua base real no GitHub.

```bash
python3 spikes/spike001/backup/restore-candidate/migration-audit/audit_legacy_merges.py \
  /caminho/para/uma-copia-do-banco.db \
  --report /caminho/para/relatorio-sem-titulos.json
```

A conexão é aberta via URI SQLite `mode=ro` e `PRAGMA query_only=ON`. O programa executa exclusivamente `SELECT` e `PRAGMA foreign_key_check`. O único arquivo escrito, se solicitado, é o **relatório JSON** no caminho de `--report`. O relatório evita títulos, URLs completas e tokens de UUID; apresenta IDs locais, códigos de problema e contagens. O teste confere que o SHA-256 do banco antes/depois da auditoria não muda.

- **Exit code 0:** nenhum bloqueio reconhecido pela ferramenta.
- **Exit code 2:** encontrou algum problema; NÃO instalar índices únicos.
- **Exit code 3:** banco inválido, indisponível ou ilegível; não tratar como OK.

Verifica as condições relevantes para a migração candidata: duplicidade `(merge_id,manga_source,manga_url)` inclusive entre links pendentes/resolvidos; duplicidade `(merge_id,manga_id)`; pai não virtual, raiz virtual ausente/duplicada/inválida; `merge_url` incompatível com a URL do pai; filho resolvido sem correspondente exato e único; violação de FK; `memo` JSON inválido; UUID não canônico, repetido entre pais ou sem ledger correspondente. A referência **explicitamente pendente** (`manga_id=NULL`) não é religada automaticamente, mesmo que um mangá real esteja instalado.

**Importante:** resultado sem bloqueadores **não autoriza automaticamente executar uma migração**. Antes de instalar as constraints no app, ainda se exige cópia de segurança verificável, inspeção dos registros legados, revisão da migração real, SQLDelight compilado e teste Android com rollback. A ferramenta analisa o formato esperado de `mangas` e `merged` do Yomotsu fixado/Polaris; não é um verificador geral de corrupção de SQLite.

## Testes reprodutíveis

```bash
python3 -m unittest discover \
  -s spikes/spike001/backup/restore-candidate/migration-audit \
  -p 'test_*.py' -v
```

**40/40 testes Python/SQLite executados localmente e aprovados**, incluindo casos em que a ferramenta deve recusar índices, respeitar pending, detectar UUID conflituoso e preservar os bytes do banco. O código e o teste publicados foram comparados pelos hashes Git blob às versões exatas executadas. O `run_host_gate.py` e `domain-spikes.yml` exigem a suíte de 40 como estágio `backup-migration-audit` quando o runner estiver disponível.

O mínimo **configurado** dos agora **11 grupos** do host gate é **360 testes** (320 anteriores +40), mas **o gate completo 360 não foi executado**. Não houve alteração no `mangas.sq`, `merged.sq`, migration 15, classes SQLDelight de produção nem no APK. Issues #2/#10/#11 permanecem abertas e PR #1 em DRAFT.

## Ensaio real da migração sem tocar no banco original (2026-10-15)

O novo `rehearse_restore_migration.py` executa a auditoria acima e, **somente
se não houver bloqueadores**, usa a API `sqlite3.Connection.backup` para
copiar o SQLite fornecido para **um banco `:memory:`**. Aplica nesse clone
o DDL exato do candidato `../atomic-sqlite/atomic_parent_restore_candidate.sql`
e valida:

- A presença e unicidade dos dois índices `merged`, inclusive o índice
  parcial de `manga_id`, e o índice único do pai no ledger.
- A integridade do `polaris_restore_ledger`: colunas obrigatórias, chave
  primária UUID e FK para o pai com `ON DELETE CASCADE`.
- `PRAGMA integrity_check` e `foreign_key_check`, bem como **hashes
  dos dados originais de todas as linhas `mangas` e `merged`** antes e
  depois de executar o DDL em memória.

```bash
python3 spikes/spike001/backup/restore-candidate/migration-audit/rehearse_restore_migration.py \
  /caminho/copia-consistente.db \
  --report /outro/caminho/novo-relatorio.json
```

As duas ferramentas agora geram relatórios com `os.O_EXCL`, permissão
`0600`: **nunca sobrescrevem um arquivo existente**, mesmo se for um
atalho simbólico/hard link para o banco. O parâmetro `--report` exige
arquivo **novo** `.json`, distinto de `.db`, `-wal`, `-shm` ou
`-journal`. A versão anterior de `--report` usava `write_text` e
poderia truncar acidentalmente o próprio banco se o usuário escolhesse
o mesmo caminho; este problema foi corrigido.

O ensaio retorna `PASS_IN_MEMORY_ONLY` no relatório e código 0 quando
passa; um bloqueio ou falha no DDL retorna código 2; ausência de banco,
erro de leitura ou relatório indisponível retorna código 3. **Isso NÃO
significa que a migração está liberada para instalação no Android**:
a execução é SQLite/Python host, não geração SQLDelight nem Gradle/APK.
Se houver WAL ativo, faça uma cópia consistente pela API SQLite de backup
antes do ensaio.

**Evidência verificada:** 40/40 cenários no host (20 antigos +20
novos), hashes Git de todos os arquivos de código e testes idênticos
aos executados. Os testes incluem tentativa de usar o próprio banco
como relatório, symlink/hardlink, relatório existente, SQL destrutivo
em memória, índice não único, ledger incompatível e confirmação dos
bytes do arquivo original. [ZIP no Drive](https://drive.google.com/file/d/1yDAhdjx4tpoItj-NfbjmfjYO7Ay70QaO/view),
SHA-256 `140b2c192a2ccfbf4d9efe765148b0f0db63c8aad6f89f22e6fa40851ae7adb2`.
O 11º gate host agora exige 40, elevando o mínimo configurado total
de **340 para 360**, sem execução conjunta dos onze grupos.

## 2026-10-15 — plano de reconciliação sem exclusões automáticas

`plan_legacy_reconciliation.py` estende as ferramentas anteriores com
**grupos de conflitos relacionados** antes de ativar índices físicos UNIQUE:

- Duas referências podem compartilhar a mesma `(merge_id,manga_source,manga_url)`,
  inclusive uma pendente (`manga_id=NULL`) e outra resolvida.
- Duas referências podem apontar o mesmo `(merge_id,manga_id)` real
  embora armazenem `source+URL` diferentes.
- Esses conflitos podem estar conectados indiretamente: a linha A
  conflita com B por fonte+URL e B com C por manga_id. O plano
  une o trio num **único grupo de revisão**, evitando resolver partes
  de um problema e criar outro.

Classes: `EXACT_DUPLICATE_CANDIDATE_REVIEW` (TODOS os campos iguais,
exceto `_id`); `PENDING_VS_RESOLVED_MANUAL_REVIEW`;
`REAL_IDENTITY_MANUAL_REVIEW`;
`SETTINGS_OR_IDENTITY_MANUAL_REVIEW` e
`VIRTUAL_ROOT_REVIEW_REQUIRED`.

Mesmo para cópias idênticas, a ferramenta somente **sugere** o ID
a preservar e os IDs redundantes para análise. Não assume que ninguém
referencia o antigo `merged._id`. **Não cria SQL DELETE para produção,
não atribui prioridade arbitrária e não reconecta links NULL.**
Para conflitos de configurações, raiz, IDs ou estado pendente, nem sequer
sugere uma linha vencedora.

A opção `--simulate-exact` remove SOMENTE as candidatas idênticas
em `:memory:`, preserva e compara integralmente os registros
sobreviventes, chama o ensaio DDL anterior sobre outra cópia em memória e
mostra se os índices passariam **nesse cenário hipotético**. A análise
continua exigindo revisão humana. Relatórios são redigidos (somente
IDs locais, tipos de conflito, contagens e hashes) e gerados com
`O_EXCL` para não sobrescrever arquivos.

```bash
python3 spikes/spike001/backup/restore-candidate/migration-audit/plan_legacy_reconciliation.py \
  /caminho/copia-consistente.db --simulate-exact \
  --report /caminho/novo-relatorio-revisao.json
```

Exit codes: `0` apenas sem bloqueadores ou grupos pendentes
(`0` **não autoriza a migração**); `2` se requer revisão,
possui conflitos ou ensaio bloqueado; `3` para falha de abertura,
esquema ou relatório. Um ensaio `PASS_IN_MEMORY_ONLY` com
cópias idênticas ainda retorna **2** no CLI, pois exige revisão antes
de qualquer alteração real.

**Validação executada:** 22/22 novos testes PASS e **62/62 no grupo
completo de auditoria (40 anteriores + 22 novos)**; ambos os arquivos
Python publicados possuem hashes Git idênticos aos executados.
Dois exemplos sintéticos no ZIP mostram a classificação, sem dados reais.
[ZIP com código, 62 testes, relatório fictício e hashes no Drive](https://drive.google.com/file/d/1sBlgoCNOSQYCLnjDirQNJJDJLlq5OTLU/view).
SHA256 `f21374ce7373f54ab16154c9e25a69c7e1ca33a146e8226d62931ccf48145d35`.

O gate `backup-migration-audit` passa a exigir **62 casos**
(e não 40), total mínimo configurado da R001 agora **382**
(360+22) distribuídos em 11 grupos. **Não houve execução
conjunta das 382 verificações nem compilação SQLDelight/Android.**
Não usar para alterar o banco do aparelho ou migration 15.
