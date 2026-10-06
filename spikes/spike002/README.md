# Spike-002 — CanonicalWork / SourceRanker

Framework-independent Kotlin prototype for the next Polaris layer.

It intentionally does not depend on Android, Mihon, Yomotsu, SQLDelight or a server. The goal is to freeze and test ranking semantics before wiring them into the app.

## Included
- CanonicalWork
- SourceVariant
- ChapterVariant
- SourceHealthState
- SourceHealthSnapshot
- SourceRanker
- deterministic language tiers
- health/coverage/freshness/latency scoring
- hysteresis to avoid source flapping

## Ranking policy
1. A source must be usable for the requested chapter.
2. Language preference is dominant, not merely a small score bonus.
3. Inside the best available language tier, sources are ranked by health, historical success, coverage, highest chapter, freshness, latency and failures.
4. A currently active source is kept when the improvement from another source is smaller than the hysteresis margin.
5. AUTH_REQUIRED, AUTH_EXPIRED, CHALLENGED, BROKEN and UNREACHABLE are not eligible until revalidated.
6. RATE_LIMITED becomes eligible only after cooldown expires.

Default language order:
pt-BR -> pt -> en -> original/other configured languages.
