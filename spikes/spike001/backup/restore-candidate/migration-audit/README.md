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

**20/20 testes Python/SQLite executados localmente e aprovados**, incluindo casos em que a ferramenta deve recusar índices, respeitar pending, detectar UUID conflituoso e preservar os bytes do banco. O código e o teste publicados foram comparados pelos hashes Git blob às versões exatas executadas. O `run_host_gate.py` e `domain-spikes.yml` exigem a suíte de 20 como estágio `backup-migration-audit` quando o runner estiver disponível.

O mínimo **configurado** dos agora **11 grupos** do host gate é **340 testes** (320 anteriores +20), mas **o gate completo 340 não foi executado**. Não houve alteração no `mangas.sq`, `merged.sq`, migration 15, classes SQLDelight de produção nem no APK. Issues #2/#10/#11 permanecem abertas e PR #1 em DRAFT.
