# Spike-023 — CanonicalMetadataResolver

Defines how Polaris presents one canonical work when source variants disagree about title, cover and metadata.

Rules:
- explicit user overrides win;
- usable variants are preferred over blocked/dead variants;
- preferred-language tier dominates display title/cover/description;
- an already-selected title remains stable while it still exists in the best language tier, avoiding UI churn;
- author/artist can use same-tier consensus;
- genres are unioned;
- every chosen field exposes provenance.

This changes presentation only. The immutable CanonicalWork UUID from Spike-019 never changes when metadata changes.
