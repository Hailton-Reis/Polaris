# Polaris R001 — decoded v2 canonical envelope binding (2026-10-20)

**Staging only: import v2 remains blocked.**

Three Kotlin source candidates and 58 local host checks address a gap in the previous archive hash validation: a caller previously could pass unrelated opaque bytes plus their matching digest alongside a different BackupManga. The new decoder-bound gateway instead accepts the validated v2 bundle, source snapshots, archived category snapshots and exact UUID; creates a `PolarisV2ProtoBufEnvelope` from the `BackupPolarisWork`, complete `BackupPolarisParentPayload.manga` and referenced archived `BackupCategory` DTOs; canonical-encodes this object and computes SHA256 itself. No arbitrary bytes/digest argument. Any subsequent mutation of the decoded object is detectable through `verifyBeforeTransaction`.

The new inner envelope has four fields (formatVersion, work, parent, referencedCategories), and the source includes intended Kotlinx ProtoBuf codec implementation. It is not added to the outer `.tachibk` schema (tag 107 remains reserved for the existing Polaris bundle candidate).

**Verified now:** 20/20 generic Kotlin admission tests, 22/22 Kotlin decoded-bundle gateway tests with DTO doubles, and 16/16 google.protobuf Python dynamic-schema wire proxy tests, **58/58 local host passes**. No actual Kotlin compiler plugin-generated ProtoBuf serializer was used. The Python proxy tests selected known nested tags, not every original Yomotsu field or the actual Android wire format.

**Not yet solved:** Existing `SqlDelightPolarisFreshParentAdapter.FreshWork` still accepts separately supplied opaque bytes; the gateway must be integrated with the trusted decoder and replace this unsafe entrypoint in the Android build. No archive authenticity/signatures are claimed, and the digest is of canonical reserialization, not raw compressed source bytes. Real ProtoBuf compatibility, SQLDelight 2.3.2 generated binding and Android B01–B05 remain required. The coordinator's v2 refusal stays intact, migration14/15 untouched, PR #1 Draft, issue #11 OPEN.

Gate: `backup-v2-decoded-envelope` requires distinct 20/22/16 suite results plus unique combined marker 58; 25 groups and **1,237 configured minimum cases, NOT an executed aggregate/CI pass**.

Evidence ZIP SHA256: `defb5464ef0a817d5ad2552e798bb0569e652f00ddd0c9a434244a98567d5d4e`, Library `/Polaris/R001/decoded-v2-envelope-binding/`.
