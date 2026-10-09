# Pinned Yomotsu Source API compatibility test

**Scope:** Compiles the actual staged `MergedSource.kt` from Spike-001 against the
**actual** `Source.kt` from Yomotsu commit `0fb80c439ef816eeb50674f1b90af39918b176d8`.
Tests source identity, immutable no-network update behavior, and explicit refusal
of search, latest, popular and page fetch operations.

```bash
bash scripts/r001/test_merged_source_api_host.sh /path/to/clean-pinned-yomotsu
```

Requires JDK21, `kotlinc`, and its `kotlinx-coroutines-core-jvm.jar` installed.
The upstream path must be a Git checkout at the pinned exact HEAD; the script
does **not** check out, download or modify the upstream repository.

The three tiny fixture types in `SourceModelStubs.kt` and `RxStub.kt`
are compile-only stand-ins for unrelated models and deprecated Rx methods.
**The Source API interface itself is never stubbed**, which is why compiler
acceptance of the real `MergedSource : Source` is meaningful.
This does not compile the full Yomotsu/Android application, fetch real chapters,
or pass B01–B05.

First execution on 2026-10-09 with pinned Source blob
`708012a8f3b0cdf693404a9b30d2df971ba4d382`,
Polaris MergedSource blob `b46144fc9c2b171dada21fa4a9ffbd13b4d8e02e`,
and Polaris internal source IDs blob
`76dfc4cdb26295bd7f4319c8b0529b61017668c2`:
**8/8 PASS**. Sources were hash-verified, compilation used JDK21 and kotlinc1.9.
