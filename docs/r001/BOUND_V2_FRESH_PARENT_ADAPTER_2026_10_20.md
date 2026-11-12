# Polaris R001 — v2 decoded bundle bound to Kotlin fresh-parent adapter

Date: 2026-10-20. **Staging host candidate only; v2 import remains blocked.**

## Concrete gap addressed

The decoded-v2-envelope gateway computed a SHA-256 fingerprint of an actual decoded BackupPolarisBundle's parent, links and archived categories, but the independent SQLDelight Kotlin restore adapter still accepted a separately created FreshWork containing arbitrary opaque bytes and digest. A valid-looking hash was therefore not enough to bind the object that would be written.

## Changes committed

- Added PolarisV2BoundFreshRestoreBridge.kt. It accepts the decoded v2 BackupPolarisBundle, original ordinary manga, original archived categories, explicit destination order->category ID and resolved child source+URL->local ID maps and a codec. It refuses omitted/extra UUID destinations, mismatched mapping keys, missing/extra physical source resolutions and local IDs on pending links. It constructs all five merge flags directly from the admitted decoded work.
- Added restoreBoundNewOnly() to SqlDelightPolarisFreshParentAdapter. It REQUIRES a PolarisV2SnapshotAdmission on every FreshWork; the old opaque-only restoreNewOnly() was narrowed to Kotlin internal and remains for existing host checks, NOT a safe production import API.
- The adapter recomputes canonical proof, checks byte-for-byte snapshot digest, original parent object reference, archived category object references, source identities, explicit pending state and all five root/link settings. These checks run before the writer, again inside it, after persisted physical readback, and across the complete batch before COMMIT.
- Added 26 Kotlin negative/positive behavior tests. A host-only callback mutates the decoded parent title, a link URL and a category name in the middle of the write; all changes roll back without committing the parent, link ledger, chapters or categories.

## Tests actually executed

- 26/26 NEW Kotlin/JVM decoder-bound restore tests PASS.
- 42/42 existing Kotlin candidate adapter behaviors and 34/34 Python source/SQL checks PASS (76/76).
- 20/20 Kotlin admission, 22/22 Kotlin decoded-gateway and 16/16 Python protobuf wire-proxy checks PASS (58/58).
- Combined **160 individually executed local HOST checks in three independent suites**, not a single aggregate execution. The all-in-one runner exceeded this container's time limit during repeated Kotlin compilation, so it is **not recorded as a pass**.
- New host and CI gate backup-v2-bound-adapter requires a unique 26-case marker and refuses skipped reports. The configured minimum is now **1263 cases across 26 gates**, not an aggregate or CI PASS.

## Hard blockers / not yet proven

The canonical codec used by the gateway test is a fake Kotlin implementation and may omit fields. The real kotlinx.serialization ProtoBuf plugin and Yomotsu BackupDecoder/BackupRestorer have not been exercised. The Kotlin SQLDelight 2.3.2 adapter continues to compile only against host query doubles; reviewed physical UUID ledger migration, actual Android driver runtime, B01–B05 and existing-parent/replay policies are still pending.

Kotlin internal is not a security boundary against other same-module callers; before release the legacy opaque-only path must be removed or sealed behind the real decoder-owned entrypoint. No archive authenticity/signature is claimed. The current v2 coordinator preflight stays fail-closed; migration 14/15 unchanged, PR #1 Draft, issues #2 and #11 open. No user data modified.

Evidence ZIP SHA256: 3289784d80c0745f160b35e264945539673dcf79683af2d4b5f8ab77535893f4.
Library: /Polaris/R001/decoded-v2-to-sqldelight-bridge/.
Host repro: bash spikes/spike001/backup/restore-candidate/v2-decoded-envelope/run_bound_adapter_tests.sh
