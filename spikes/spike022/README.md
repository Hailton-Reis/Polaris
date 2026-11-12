# Spike-022 — VariantRefreshPlanner

Defines when Polaris should refresh known source variants so chapter coverage/health are recent without querying every source on every open.

## Default behavior

- current selected variant can be revalidated on work open;
- background library update uses a longer TTL;
- work open uses a shorter TTL;
- manual refresh bypasses freshness TTL;
- AUTH_REQUIRED / AUTH_EXPIRED / CHALLENGED are skipped until user interaction;
- active rate-limit cooldown is respected;
- UNREACHABLE is skipped in background but may be explicitly retested manually;
- concurrency is bounded.

Default draft values:
- background TTL: 6h;
- work-open TTL: 30m;
- max concurrency: 4.

These are tunable policy values, not hard product promises.

Validated locally:
- selected variant priority;
- stale variant refresh;
- fresh background skip;
- challenge skip;
- rate-limit cooldown;
- manual unreachable retry.
