# Polaris R001 — proof of SHA-256 against encoded per-parent snapshot bytes (2026-10-20)

**Host/staging only; v2 restore remains fail-closed.**

Previously a supplied lowercase 64-digit archive digest was accepted without recalculating it. The staged Kotlin `FreshWork` now requires `archiveSnapshotBytes` and runs SHA-256 against these opaque bytes before opening `restoreNewParents`, refusing empty or mismatched payloads. This keeps a bogus digest out of the ledger in this candidate.

**76/76 local host tests PASS**: 42 compiled Kotlin/JVM behavioral tests and 34 SQL/source contract tests. Eight new checks; runner uses unique combined success marker. No actual SQLDelight generated classes, Android, v2 decoder or ProtoBuf used. The configured gate is now **1179 min test cases in 24 groups, NOT all executed**.

**Critical limitation**: the bytes are not validated as an encoding of the separately supplied `BackupManga`, child links or settings; a caller can pass unrelated bytes plus the correct hash. Before production, a trusted real v2 ProtoBuf decoder must bind the exact versioned snapshot bytes to the decoded model and canonical digest. No claim of full authentication or production readiness is made.

Evidence ZIP SHA256 `aadc80a2e234c5fd7c14778ed74dc53d782538087f535e95267b541b6a58a7f4` in Library `/Polaris/R001/opaque-snapshot-digest/`. PR #1 remains Draft, issues #2/#11 open, migration14/15 and `PolarisRestoreCoordinator` v2 preflight unchanged.
