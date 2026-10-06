# Spike-018 — Polaris backup contract

Provider-neutral contract for backing up canonical Polaris state.

Portable:
- canonical stable key/title/original language;
- aliases + provenance/confidence;
- external IDs;
- source variants via durable source identity + source work key;
- canonical chapter read/bookmark state;
- chapter relationships via chapter URL;
- stable canonical translation scope.

Local DB IDs are deliberately not portable. Restore resolves relationships against the destination installation.

Transient source-health history is optional and may be omitted.

Validated locally: valid schema, stable translation scope, duplicate variant rejection, and unsupported-newer-schema rejection.
