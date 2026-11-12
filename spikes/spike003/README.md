# Spike-003 — AutomaticWorkMatcher

Pure Kotlin prototype for correlating source-specific results into one canonical work.

## Purpose

Polaris must recognize that different source entries may represent the same work even when:
- the title is translated;
- punctuation differs;
- aliases differ;
- one source uses the original title;
- another source uses an English or PT-BR title.

Local evidence is used first. LLM/semantic resolution is an escalation path, not a mandatory first step.

## Evidence order

Strongest:
1. shared external/tracker ID;
2. normalized title/alias overlap.

Supporting:
- author;
- artist;
- description token overlap;
- genre overlap;
- chapter-number overlap.

Conflict:
- same external-ID namespace with different IDs is strong evidence against auto-merge.

## Decisions

- AUTO_MATCH: safe to merge automatically.
- REVIEW: plausible but ambiguous; ask semantic/LLM provider or user.
- DIFFERENT: insufficient or conflicting evidence.

## Important

Cross-language titles with no shared IDs/aliases often cannot be proven locally. This is exactly where Polaris may ask an LLM or metadata provider to decide whether two candidates are translations/aliases of the same work.
