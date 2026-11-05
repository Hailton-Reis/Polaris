# Polaris R001 - SQLDelight scalar query return values - 2026-10-20

Host-only staging: backup v2 import remains blocked.

## Identified defect
The existing SQLDelight candidate queries select exactly one column for category_id and scanlator. The adapter incorrectly assumed generated wrapper objects with properties, because its host doubles supplied invented CategoryRec and ExclusionRec data classes.
The Kotlin readback now consumes List<Long> and List<String> directly, while strict host API-shape doubles and four source contract tests check the scalar results.

## Executed evidence
**38/38 Kotlin/JVM host behaviors PASS**, **30/30 Python source/SQL contract checks PASS**: combined **68/68 local PASS**. The package was compiled using API-shape test doubles, NOT original SQLDelight-generated classes. ZIP SHA256 99889e4acd929be1c991cc63be471b2dffade0220795f05b7d371ddae50b3c28, Library /Polaris/R001/sqlite-scalar-query-fix/.
Host gate minimum is 68 (+4), **1171 minimum configured across 24 gates**, NOT a full aggregate/Android/CI pass.

## CI diagnosis
The latest PR-triggered jobs fail in 3-4 seconds with zero executed steps. Job logs/annotations are unavailable via connected GitHub resources; no actual source compilation failure can be attributed. CI remains unverified.
The code still needs real SQLDelight 2.3.2 generation, Android B01-B05 and ProtoBuf tests. Migration14/15 untouched; PR #1 Draft, issues #2 and #11 open; restore v2 fail-closed.
