# Polaris R001 — decoded-object-bound v2 snapshot admission (host candidate)

**Staging only: do not enable v2 restore, overwrite a local parent or apply migration 15.**

This code addresses the prior `generated-adapter/SqlDelightPolarisFreshParentAdapter.kt` weakness: a caller may provide arbitrary `archiveSnapshotBytes` plus its SHA256 unrelated to the separately supplied decoded `BackupManga` and portable source-link settings. The current adapter's hash check is valid **only for those opaque bytes**, not for the user's decoded model.

## Candidate new boundary

- `PolarisV2ProtoBufEnvelope.kt`: `@Serializable` v2 digest envelope holding the **actual staged portable `BackupPolarisWork`**, **full `BackupPolarisParentPayload`** (and thus its real mutable `BackupManga`), and the original backup's `BackupCategory` records referenced by its archive category orders. The digest envelope field numbers are **1–4**; this is *not* a new `.tachibk` field and does not replace outer tag **107**. It deliberately excludes destination manga IDs/category IDs. Link source+URL, observed titles, pending bits, edge settings, parent chapters, history, memo, notes, category flags, etc. are represented through those nested DTO types.
- `PolarisV2DecodedEnvelopeGateway.kt`: accepts a **validated decoded `BackupPolarisBundle` and ordinary manga/category snapshots**, not caller bytes or a digest. Calls the existing bundle's `validateSnapshotCoverage()`, requires the exact archive UUID work and parent, maps original category orders without name guessing, validates the envelope, and constructs the admission.
- `PolarisV2SnapshotAdmission.kt`: only a factory can mint an admission by **encoding the decoded envelope through an injected codec**, decode/encode stability checking it and retaining a private byte copy and SHA256. `verifyBeforeTransaction()` reencodes the *same decoded DTO graph* and fails if any relevant mutable field changed. No database writes.
- `PolarisV2ProtoBufCodec`: intended Android implementation calling the pinned Kotlinx `ProtoBuf` serializer. The **real** compiler-generated `serializer()` and Android ProtoBuf runtime have NOT been tested here.

**Important:** The digest is of a *canonical reserialization of a decoded envelope*, **not** a proof of authenticity or the original compressed `.tachibk` wire bytes. It cannot detect a tampered malicious archive that was consistently decoded and reserialized. The transport does not use signatures. Verification must run from the trusted decoder and be checked immediately before the real SQLDelight transaction, with the generated adapter using the SAME vetted `BackupManga` and link values. This bridge is NOT yet connected to the existing `FreshWork`/`PolarisRestoreCoordinator` (the latter MUST remain blocked). A generic injected codec could lie; production DI must fix it to real ProtoBuf.

## Executed locally

`bash run_all.sh`

- **20/20** portable Kotlin admission tests (deterministic codec host double), including title, UUID, chapter additions/deletions/order, memo, link mutations, defensive copy and unstable codec.
- **22/22** Kotlin decoded-bundle gateway tests with stand-in DTOs and codec; validates missing/ambiguous categories, malformed links/roots and mutations to mutable category name/order, title, chapter and URL after admission.
- **16/16** Python `google.protobuf==6.33.6` dynamic-schema wire proxy checks for the exact four envelope tags and representative real nested model tag positions, UTF-8 chapters/categories, link pending/state/settings, version/ordinal, memo and category flags. NOT the actual generated Kotlin protobuf bytes.

**58/58 new host checks PASS.** A unique `POLARIS_V2_BOUND_ARCHIVE_GATE_PASS 58` marker is mandatory for the R001 aggregator. All tests are disposable and never access a user's SQLite database.

## Release blockers

1. Compile `PolarisV2ProtoBufEnvelope` against actual Yomotsu `@Serializable` DTOs, Kotlinx plugin/runtime and decode actual `.tachibk` files; verify true Kotlin ProtoBuf round-trip and default-field behavior.
2. Integrate decoder-owned admission into `PolarisRestoreCoordinator`/`SqlDelightPolarisFreshParentAdapter` with the **same decoded instance**, immutable/archive-locked models or recheck immediately before SQLDelight writes; disallow the current separate arbitrary `FreshWork.archiveSnapshotBytes` input in the production interface.
3. Confirm source child restore, destination category mapping and real SQLDelight schema/readback on Android B01–B05. Ledger migration still under review.
4. The two GitHub Actions jobs have previously failed with **zero executed steps**, so CI success cannot be claimed.

PR #1 Draft; issues #2 and #11 open. Migration14 and migration15 and v2 fail-closed preflight remain untouched.
