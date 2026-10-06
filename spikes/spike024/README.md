# Spike-024 — CanonicalWorkLifecyclePolicy

A canonical library entry must not disappear merely because a source was removed, blocked or temporarily unavailable.

States:
- ACTIVE: at least one usable linked variant;
- DEGRADED: variants are linked but none are currently usable;
- ORPHANED: no linked variants remain.

The canonical work is always retained. An orphan with aliases can trigger rediscovery; an in-library orphan can also surface a user-attention action. This prevents source churn from destroying the user's library identity/progress.
