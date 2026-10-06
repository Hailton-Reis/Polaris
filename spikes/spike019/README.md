# Spike-019 — Stable canonical work identity

Polaris canonical identity must not depend on a display title or a tracker ID.

## Decision

Every CanonicalWork receives an internal UUID when it is created.

That UUID:
- never changes when the preferred title changes;
- never changes when aliases are added;
- never changes when AniList/MAL/etc IDs are discovered later;
- is the basis of the stable translation memory scope and backup identity.

External IDs remain powerful correlation anchors, but not the primary identity.

Recommended translation scope:
`polaris:<canonical-uuid>`

Validated locally:
- rename keeps identity;
- adding external ID keeps identity;
- translation scope remains stable.
