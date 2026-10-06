# Spike-011 — SemanticWorkMatcher contract

This spike defines the LLM boundary used only after local matching returns REVIEW.

Polaris may call an LLM frequently when it improves quality, but the LLM is not allowed to override hard contradictory evidence.

## Expected semantic answer

- sameWork: true/false
- confidence: 0..1
- canonicalTitle
- aliases with languages when inferable
- short reason code

## Hard rules outside the LLM

The caller MUST NOT ask the LLM to override:
- conflicting IDs in the same trusted tracker namespace;
- an explicit user “do not merge” decision.

## Merge policy

- confidence >= 0.90 and sameWork -> may auto-confirm REVIEW candidate;
- 0.65..0.90 -> keep for user review unless another metadata provider confirms it;
- below 0.65 or sameWork=false -> do not merge.

The thresholds remain configurable.
