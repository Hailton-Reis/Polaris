# Spike-017 — SelectionDiagnostics

Pure Kotlin diagnostic contract for explaining a Polaris chapter-source decision.

The runtime should be able to answer which source was selected, its language tier/score/reasons, which candidates were rejected by auth/challenge/rate-limit/broken/etc., and whether translation was required.

This is a support/debug surface; it should not clutter the default reader UI.

Validated locally: selected summary, usable alternatives, unavailable candidates, translation marker, and no-usable-source summary.
