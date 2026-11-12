# Spike-018 — Polaris backup contract

Provider-neutral contract for backing up canonical Polaris state.

Portable:
- canonical internal UUID/title/original language;
- aliases + provenance/confidence;
- external IDs;
- source variants via durable source identity + source work key;
- canonical chapter read/bookmark state;
- chapter relationships via chapter URL;
- stable canonical translation scope;
- explicit user work-link overrides, including FORCE_DIFFERENT_WORK.

Local DB IDs are deliberately not portable. Restore resolves relationships against the destination installation.

Transient source-health history is optional and may be omitted.

Why overrides are included:
a user decision such as “do not merge these two works” must survive restore, otherwise automatic/semantic matching could recreate a relationship the user explicitly rejected.

Validated locally: stable UUID schema, translation scope, duplicate variant rejection, override validation, and unsupported-newer-schema rejection.
