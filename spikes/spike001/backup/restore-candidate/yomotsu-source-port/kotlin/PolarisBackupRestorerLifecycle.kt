package polaris.spike001.backup.restore.yomotsu

import eu.kanade.tachiyomi.data.backup.models.BackupManga
import eu.kanade.tachiyomi.data.backup.models.BackupPolarisBundle
import polaris.spike001.backup.restore.RestoredPolarisWork

/**
 * Narrow, Android-neutral seam around Yomotsu BackupRestorer.restoreFromFile.
 *
 * Stock jobs must be executed IN A STRUCTURED coroutineScope so this suspend
 * callback does not return while jobs are still running. Never launch detached
 * workers or rely on a notifier progress counter as a completion barrier.
 *
 * Stage only: this class does not change BackupRestorer or the backup wire format.
 */
class PolarisBackupRestorerLifecycle(
    private val strict: PolarisYomotsuStrictRestoreSequence,
) {
    suspend fun restoreAfterDecodedPreflight(
        polarisBundle: BackupPolarisBundle?,
        ordinary: List<BackupManga>,
        libraryEntries: Boolean,
        runStockYomotsuJobs: suspend () -> Unit,
    ): List<RestoredPolarisWork> {
        // Preflight MUST precede the first stock DB job; invalid portable
        // parents must not produce a half-restored library.
        strict.preflightBeforeAnyWrites(polarisBundle, ordinary, libraryEntries)

        // The normal Yomotsu path runs ONCE for both old and new archives,
        // regardless of whether Polaris has a segment or library is disabled.
        // This must be a structured/suspending completion barrier.
        runStockYomotsuJobs()

        // The stock MangaRestorer may log and swallow failures. Its completion
        // alone is not trusted: strict sequence retries/verifies only required
        // linked children before any virtual parent is committed.
        return strict.restoreAfterStockOrdinaryJobsOrThrow(
            polarisBundle, ordinary, libraryEntries,
            awaitStockOrdinaryJobs = { /* already joined above */ },
        )
    }
}
