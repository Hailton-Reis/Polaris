# Spike-005 — SourceHealthTracker

Pure Kotlin state machine that converts source access outcomes into a health snapshot usable by SourceRanker.

## Events

Success:
- records latency;
- clears consecutive failures;
- recovers AUTH/CHALLENGE/RATE_LIMIT states after a real successful request.

Failures:
- timeout/network/5xx -> DEGRADED, then UNREACHABLE after repeated failures;
- parse/source-contract errors -> DEGRADED, then BROKEN after repeated failures;
- authentication required/expired -> AUTH_REQUIRED / AUTH_EXPIRED;
- challenge -> CHALLENGED;
- 429/rate-limit -> RATE_LIMITED until cooldown.

## Design

The tracker deliberately does not try to bypass authentication or challenges. It only classifies the state so Polaris can:
- ask the user to authenticate/unlock;
- retry after cooldown;
- select another source immediately;
- restore ranking after a successful revalidation.

The produced snapshot is compatible with Spike-002 SourceRanker semantics.
