# Polaris R001 — Runtime Acceptance Tests

The following tests are the gate for moving R001 out of draft.

## A. Baseline

### A01 — Yomotsu baseline
Given pinned Yomotsu commit
When built without Polaris changes
Then debug APK builds and launches.

### A02 — Polaris patched build
Given Spike-001 applied
When SQLDelight/Gradle build runs
Then build succeeds without disabling existing Yomotsu modules.

## B. Multi-source identity

### B01 — Two-source virtual work
Given Work X exists in Source A and Source B
When a virtual work is created
Then one library entry exposes chapters from both children.

### B02 — Child source reader routing
Given chapter A belongs to Source A and chapter B belongs to Source B
When each is opened from the virtual work
Then Reader uses the correct real child source without migration.

### B03 — Remove one variant
Given a work has two variants
When one variant/reference is removed
Then the canonical/virtual work remains valid with the remaining source.

## C. Ranking

### C01 — More complete PT-BR source
PT-BR A: 80 chapters, healthy.
PT-BR B: 83 chapters, healthy.
Requested chapter exists in both.
Expected: B.

### C02 — Health beats tiny coverage advantage
PT-BR A: 83, CHALLENGED/unusable.
PT-BR B: 80/82, healthy and has requested chapter.
Expected: B.

### C03 — PT-BR before EN
PT-BR source usable for requested chapter.
EN source has substantially more chapters.
Expected: PT-BR.

### C04 — EN fallback
No usable PT-BR variant has chapter 84.
EN healthy has chapter 84.
Expected: EN selected.

### C05 — Hysteresis
Current PT source and alternate differ only slightly in score.
Expected: keep current source.

### C06 — Material degradation
Current source becomes materially slower/failing.
Expected: switch to healthy same-language alternative.

## D. Translation

### D01 — EN auto translation
Given EN selected because PT-BR is missing
When canonical translation is enabled
Then Yomotsu translation pipeline is queued automatically.

### D02 — Cache reopen
Given chapter translation already exists
When reopened
Then no new LLM/OCR work is required for cached content.

### D03 — Canonical glossary sharing
Given two source aliases for one canonical work
When both require translation
Then glossary/memory use one canonical context, not separate source-title contexts.

### D04 — Provider unavailable
Given foreign source selected but no translator configured
Expected: original opens with explicit translation-unavailable diagnostic, not hard failure.

## E. Authentication/health

### E01 — AUTH_REQUIRED
Given best source requires login
Expected: source is temporarily ineligible and next source is selected.

### E02 — Revalidation
After user logs in/unlocks manually
When a probe succeeds
Expected: source becomes usable again and may reenter ranking.

### E03 — Rate limit
429 with Retry-After/cooldown.
Expected: source skipped until cooldown, then eligible without reinstall/migration.

### E04 — Broken parser
Repeated parsing/contract failures.
Expected: source reaches BROKEN and alternatives are preferred.

## F. Matching

### F01 — Shared external ID
English title and Portuguese translated title share tracker/external ID.
Expected: auto-merge.

### F02 — Alias
PT result contains known EN alias.
Expected: auto-merge.

### F03 — Fully translated title
Different text, same author/structural chapter evidence, no ID.
Expected: semantic/LLM review; never silently discarded.

### F04 — Conflicting tracker IDs
Same-looking title but same namespace contains different external IDs.
Expected: DIFFERENT, no auto-merge.

## G. Chapter normalization

### G01 — Decimal
10,5 vs 10.5.
Expected: one canonical chapter.

### G02 — Seasons
Season 1 Chapter 1 vs Season 2 Chapter 1.
Expected: separate canonical chapters.

### G03 — Prologue
Prologue vs Chapter 0.
Expected: separate unless later explicitly mapped.

### G04 — Number offset
One source is 0-based, another 1-based with strong sequence overlap.
Expected: trusted +1 alignment.

### G05 — Different extras
Two different specials/extras.
Expected: do not silently merge.

## H. Progress

### H01 — Completed chapter source switch
Read chapter from Source A.
Later Source A disappears and B is selected.
Expected: canonical chapter remains read.

### H02 — Partial page progress
Partially read Source A chapter, source becomes unavailable.
Expected: do not copy page index blindly to B; canonical chapter identity is preserved.

## I. Regression

Verify:
- ordinary non-canonical manga still opens normally;
- downloads for ordinary manga work;
- global search works;
- Yomotsu manual translation still works;
- trackers still work;
- novels still work;
- local source still works;
- backup does not crash even before Polaris-specific backup support is added.

## R001 PASS definition

R001 is PASS only when:
- B01/B02;
- C01–C04;
- D01–D03;
- E01/E02;
- F01–F04;
- G01/G02/G04;
- H01;
all pass on a real Android build, with no critical regressions in section I.
