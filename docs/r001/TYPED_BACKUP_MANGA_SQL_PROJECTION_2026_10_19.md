# Polaris R001: typed BackupManga field projection (host candidate)

Date: 2026-10-19. Draft PR #1, issues #2/#11.

Staged Kotlin source: spikes/spike001/backup/restore-candidate/parent-field-projection/PolarisBackupMangaSqlProjection.kt

Maps pinned Yomotsu BackupManga fields to strongly typed parent/chapter/history/tracking/category and excluded-scanlator rows. Uses the real public imports for BackupManga, UpdateStrategy, MemoColumnAdapter, StringListColumnAdapter, JsonObject and JsonPrimitive. Preserves original archive URL independently from the canonical UUID destination URL. Requires category archive ORDER mapped to destination ID. Validates chapter URL/history, tracker media IDs, memo UUID consistency and unknown-key preservation. Rejects genres that cannot round-trip through the upstream comma-space StringListColumnAdapter. Fields not archived (last_update, next_update, cover_last_modified, calculate_interval) have explicit destination policy, never purported to be original archive values.

**89/89 new Kotlin host tests PASS.** Host uses DTO/JSON stubs, not the actual upstream compiled classes. Rechecked **33/33** driver guard Kotlin, **51/51** field/trigger SQLite and **98/98** migration14/readiness SQLite separately: **271 local host tests PASS**, no Android tests. Host gate now configures **1,020 cases across 22 groups**, not executed together or on GitHub CI.

Library evidence ZIP: Polaris_R001_TypedParent_271_HostChecks_2026-10-19.zip, SHA-256 5cf2d82cc7e59a9264552b21d7234a9d1a6a2017755e625eb5cef5d4d44f8a65.

Remaining: bind typed prepared rows to generated pinned real SQLDelight statements inside ONE parent-LAST transaction, persist all relations and compare full physical readback; separate existing-parent/replay policies; validate real ProtoBuf and Android B01-B05.

SAFETY: backup v2 remains fail-closed, migration14/15 untouched, no user DB writes, PR #1 Draft and issue #11 OPEN.
