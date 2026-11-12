# Spike-001 observed integration gaps (diagnostic, not test PASS)

This diagnostic runs **actual staged** `migrations/14.sqm` and the **exact pinned Yomotsu** `libraryView.sq` (blob `8ce19ae1de727f1930ddf47d6b5fc0269ae643a2`). The small supporting `mangas`/`chapters` tables are fixtures, not an Android full database.

Run from project root:

```bash
python3 spikes/spike001/audit/reproduce_known_gaps.py
```

The JSON should reproduce two currently **unresolved** failures:

- favorite merged parent reports `[totalCount,readCount,bookmarkCount]=[0,0,0]` even with four child chapters (one read, one bookmarked), because the original library view only counts chapters on the direct parent ID; see issue [#9](https://github.com/Hailton-Reis/Polaris/issues/9).
- two `merged` rows with the same parent+child+source can coexist in migration 14, because no logical unique constraint exists; see issue [#10](https://github.com/Hailton-Reis/Polaris/issues/10).

**A successful execution means these gaps are still present**, not that the product is correct. The file is deliberately named `reproduce_known_gaps.py` and excluded from the host correctness gate. If either condition stops reproducing, inspect the changed integration/migrations and update this audit; do not silently treat a failure as a regression.

Before a user-facing release, also resolve [#8](https://github.com/Hailton-Reis/Polaris/issues/8) (full virtual deletion) and [#11](https://github.com/Hailton-Reis/Polaris/issues/11) (backup/restore loses source links). Android issue #2 remains the immediate B01–B04 build/runtime gate.
