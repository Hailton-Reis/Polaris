# Spike-012 — Source access error classifier

Android/OkHttp adapters should not decide SourceHealth state directly.

This spike defines a small neutral observation model and converts it to Spike-005 health events.

## Important distinctions

- A title/chapter 404 is not proof that the entire source is broken.
- HTTP 401/403 may mean authentication, but a known challenge page takes precedence.
- HTTP 429 becomes RATE_LIMIT and preserves Retry-After.
- 5xx becomes SERVER_5XX.
- parse/contract errors mean the extension/source parser is likely out of sync.
- cancellation is not a failure.
- user navigation cancellation and cancelled prefetch must never reduce health.

The Android adapter only has to translate OkHttp/exceptions into SourceRequestObservation.
