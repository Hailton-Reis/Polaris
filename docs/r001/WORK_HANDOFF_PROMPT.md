# Prompt for Work/Codex continuation

Continue the Polaris project from repository `Hailton-Reis/Polaris`.

Use branch:
`r001/multisource-foundation`

Start by reading:
1. `docs/r001/START_HERE.md`
2. `docs/r001/NON_WORK_COMPLETED.md`
3. `docs/r001/WORK_CODEX_CHECKLIST.md`
4. `docs/r001/RUNTIME_ACCEPTANCE_TESTS.md`
5. Draft PR #1 and issues #2–#7.

Pinned Yomotsu baseline:
`0fb80c439ef816eeb50674f1b90af39918b176d8`

Primary instruction:
do not redesign framework-independent Polaris policies already covered by spikes/tests unless the real Android/Yomotsu APIs demonstrate an incompatibility.

Begin with issue #2:
- build unmodified pinned Yomotsu;
- apply/reconcile Spike-001;
- generate SQLDelight;
- build debug APK;
- prove a virtual work containing two real source mangas can open a chapter from each real source.

Do not apply canonical migration 15 until issue #2 passes.

After the runtime merge gate:
- issue #3 canonical persistence/chapter mapping/metadata/lifecycle;
- issue #5 source health/ranking/open/refresh;
- issue #4 discovery/semantic matching/manual overrides;
- issue #6 canonical translation bridge;
- issue #7 full acceptance/regression.

Record commands, diffs, failures, logs and runtime evidence in the repository/PR instead of keeping them only in chat.
