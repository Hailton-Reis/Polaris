# R001 Acceptance Scenarios

These are product-level gates, not unit tests only.

## A1 — Same language redundancy
Given:
- PT-BR Source A has chapters 1..80;
- PT-BR Source B has chapters 1..83;
- both are healthy.

When opening chapter 79:
- Polaris selects Source B if its score is materially better;
- no translation is requested.

## A2 — Health beats raw coverage
Given:
- PT-BR Source A has 83 chapters but is CHALLENGED;
- PT-BR Source B has 80 chapters and is healthy.

When opening chapter 79:
- Source B is selected.

## A3 — Foreign fallback
Given:
- PT-BR variants end at chapter 83;
- EN has chapter 84 and is healthy.

When opening chapter 84:
- EN child chapter is selected;
- Yomotsu translation is queued automatically;
- target is PT-BR;
- reader still opens the real EN child manga/source.

## A4 — Cache
After A3 finishes once:
- reopen chapter 84;
- existing translation is used;
- no duplicate LLM translation is queued.

## A5 — Canonical glossary
Given aliases:
- The Beginning After the End;
- O Começo Depois do Fim;
- O Começo Após o Fim.

A glossary correction saved while reading one variant must influence future translation of another variant of the same canonical work.

## A6 — User authentication
Given a strong PT-BR source is AUTH_REQUIRED:
- Polaris does not attempt bypass;
- it selects another usable variant;
- UI can expose “Entrar / Desbloquear fonte”;
- after user login and successful revalidation, source returns to normal ranking.

## A7 — Source failure while reading
If the current source fails on the next chapter:
- SourceHealth records the failure;
- another variant is selected;
- progress remains attached to the canonical work;
- no manual migration is required.

## A8 — Work correlation
Global search returns:
- English title from one source;
- Portuguese alias from another;
- same external tracker ID.

They appear as one canonical work.

## A9 — Ambiguous work
Two similar titles have no strong shared identity and conflicting metadata.
- Polaris does not silently merge.
- REVIEW is sent to semantic/LLM/user resolution.

## A10 — Server independence
With no personal backend configured:
- discovery works;
- source ranking works;
- reader works;
- Yomotsu local OCR and direct external providers work;
- only optional accelerator functions are absent.

## A11 — Novel
Foreign novel chapter selected:
- no OCR is used when source content is textual;
- text translation is used;
- canonical glossary/memory is shared with aliases of the work.

## Definition of R001 complete

R001 is complete only after A1-A7 and A10 are demonstrated on Android. A8-A9 may initially use a debug/experimental search surface if final UX is not ready.
