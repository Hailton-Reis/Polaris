# Polaris — Spike-001 patch bundle

This bundle is a first engineering port for the agreed architecture:

- Base: Yomotsu `0fb80c439ef816eeb50674f1b90af39918b176d8`
- Reference: TachiyomiSY `14648c7cf0aa84e5a35d48de9dbf1386df6cca42`
- Both upstream projects use Apache License 2.0.

## Goal

Prove a virtual work can reference multiple source-specific manga entries and expose one aggregated chapter list, while each chapter still opens through its original source.

## Deliberate constraints

This is NOT yet CanonicalWork, SourceHealth, SourceRanker, automatic title matching, or translation routing.

It intentionally avoids ReaderViewModel changes because Yomotsu's `MangaScreen.openChapter()` already starts the reader with `chapter.mangaId`; aggregated chapters therefore retain their real source identity.

## Implemented in staging

- SQLDelight `merged` table + migration 14
- merge domain model/repository
- merge CRUD/use cases
- merged chapter aggregation adapted to Yomotsu's existing ChapterRepository API
- virtual `MergedSource`
- manual `CreateMergedManga` use case for the spike
- replacement `GetMangaWithChapters` that automatically routes merged works

## Before PASS

1. Apply existing-file modifications in `MODIFICATIONS.md`.
2. Build Yomotsu.
3. Create two child manga entries with populated chapters.
4. Call `CreateMergedManga(listOf(idA, idB))`.
5. Open the virtual manga and verify aggregated/deduplicated chapters.
6. Open one chapter from each source.
7. Remove one reference and verify the virtual work survives.

See `VALIDATION.md` for completed compiler/domain tests.


## Windows 10/11 — contract mismatch FIX9, 23/10/2026

A execução real do CMD FIX8 chegou ao aplicador Spike-001, mas a validação `check_spike001_full_apply.py` recusou `DomainModule.kt`, mesmo com `apply_spike001.py` concluído. Em Python no Windows, `Path.write_text` converte quebras LF para CRLF; a validação compara bytes exatos. O aplicador agora grava UTF-8 com LF fixo por `write_bytes`, e o verificador normaliza **apenas o checkout de entrada**. O arquivo patchado continua sendo comparado byte a byte; alterações de código ou CRLF inesperado são rejeitados.

**Validação executada:** 13/13 testes do contrato; aplicação e verificação de todas as 28 alterações e 18 novos arquivos no conjunto real de fontes Kotlin do Yomotsu fixado em `0fb80c439ef816eeb50674f1b90af39918b176d8`, tanto com entradas LF quanto com CRLF simulado, PASS. Verificação `bash -n` do script de build, PASS.

Um `BUILD FAILED` anterior no console pode vir do gate de testes unitários **da baseline original**, cujo retorno não zero é deliberadamente registrado para comparação com a variante Spike-001. Isso não constitui por si só falha do `:app:assembleDebug` da baseline. Os logs `baseline-build.log` e `baseline-unit-tests.log` devem ser diferenciados.

O CMD **FIX8 SAFE-CLONE** não precisa ser substituído: a opção 4 clona a versão atual do GitHub em nova pasta isolada, se o checkout do usuário estiver alterado. **Ainda não houve comprovação de APK Spike-001 compilado no Windows**. Nenhum arquivo local do usuário foi apagado ou corrigido à força.

## 2026-10-23 — FIX10: trailing whitespace detected on Windows

A nova execução do CMD FIX8 avançou pelo contrato de integração, mas `git diff --check` rejeitou a linha 339 de `MangaViewModel.kt` porque um literal de `apply_spike001.py` gerava uma linha vazia com quatro espaços. Esses espaços foram removidos no **literal que produz o arquivo**, e a verificação `git diff --check` foi mantida.

Novo teste em `scripts/r001/test_check_spike001_full_apply.py`: percorre todas as 28 operações `replace_once` e rejeita qualquer linha produzida com espaços ou tabs finais. Resultado local: **14/14 testes PASS**, `git diff --check` PASS com fixtures da baseline Yomotsu tanto LF quanto CRLF. As advertências do Git sobre normalização CRLF/LF não constituem falha por si sós.

Não é necessário atualizar o CMD FIX8 no Drive; a opção 4 sincroniza a branch GitHub para um clone isolado. O APK patched ainda não foi compilado no Windows nesta revisão.
