# Spike-020 — Manual work-link overrides

Automatic/semantic matching must never repeatedly fight an explicit user decision.

## Decisions

- FORCE_SAME_WORK
- FORCE_DIFFERENT_WORK

The pair key is symmetric:
A/B == B/A.

The latest explicit override wins.

Runtime policy:
1. check manual override first;
2. if none, use local matcher;
3. if REVIEW, use semantic/LLM provider;
4. persist confirmed relationship.

A manual FORCE_DIFFERENT_WORK must prevent future background clustering from silently re-merging the pair.

Validated locally:
- symmetric pair identity;
- no override -> automatic matcher;
- force same;
- later force different wins;
- self-pair rejected.
