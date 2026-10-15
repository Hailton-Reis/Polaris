# Polaris R001 — isolated backup contract Gradle lab

This **JVM-only** project exists to compile the actual staged backup candidates
together with their explicitly fake serialization, database and JSON type
stubs. It does not compile a Yomotsu APK or exercise real
`kotlinx.serialization.protobuf.ProtoBuf`.

## Why it exists

The previous `spikes/domain-lab/build.gradle.kts` registered executable
`spike001ProtoModel`, `spike001ProtoBuilder` and `spike001UuidStore`
JavaExec tasks but did **not** add their nested Kotlin sources to its
`test` source set. Their main classes therefore were unavailable at runtime
even on a working GitHub runner. Adding the nested source roots directly to
the domain lab would also pollute unrelated domain spike compilation with
Android/API-shaped **fake classes**.

The domain lab now runs only domain spikes. This module alone compiles all
five backup test mains from these exact source directories:
- `../spike001/backup`
- `../spike001/backup/proto-candidate`
- `../spike001/backup/proto-candidate/host-tests`
- `../spike001/backup/uuid-candidate`
- `../spike001/backup/uuid-candidate/host-tests`

Run from the repository root (requires Gradle/Kotlin toolchain 21 setup):

```bash
gradle -p spikes/backup-lab checkBackup --no-daemon --stacktrace
```

The `domain-spikes.yml` workflow now runs `checkBackup` before
`domain-lab checkSpikes` and watches edits to `spikes/backup-lab/**`.
`scripts/r001/test_backup_lab_structure.py` is an offline Python
regression against missing source roots, ghost Gradle tasks and CI drift.

## Tests verified independently on 2026-10-15

All five programs were compiled together with local `kotlinc` and ran:
24 restore + 20 export + 18 protobuf model + **19** backup bundle builder
+ 21 UUID = **102/102 host JVM scenarios PASS**. The three new builder
scenarios reproduce a TOCTOU flaw: a manga child transitions between
`manga_id=NULL` (pending) and real child, or the parent identity changes,
after planning but before archive assembly. The original source **failed** a
new test; the revised planner snapshots all per-parent link states, and the
builder rejects any subsequent change, passing all **19/19** builder tests.

Evidence: [GitHub/Drive archived ZIP](https://drive.google.com/file/d/1jd9Et9pOZMqDhFd7TL9kMk2qlYwM953D/view),
SHA256 `380bace69264e44cd634ab91bc41de24a79e1f89a6cb8890362eebe4b62ae5d6`.

**Important limitations:** There was NO actual Gradle build because the local
Gradle CLI was unavailable; current GitHub Actions jobs had `runner_id=0`
and no steps. Compiler was `kotlinc` with host doubles. This is
**not** an Android B01–B05 runtime pass, production database transaction,
real Kotlin protobuf serialization or complete five-stage host gate.
The configured five-stage minimum remains **228**, separately.
No migration 15 or production Yomotsu backup files were changed.
