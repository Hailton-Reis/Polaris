package polaris.spike001.backup.restore.yomotsu

import eu.kanade.tachiyomi.data.backup.models.BackupManga
import eu.kanade.tachiyomi.data.backup.models.BackupPolarisBundle
import polaris.spike001.backup.restore.PolarisRestoreCoordinator
import polaris.spike001.backup.restore.RestoredPolarisWork

/**
 * Non-production candidate for BackupRestorer's Polaris-specific call path.
 * Run preflightBeforeAnyWrites immediately after decoding; then call
 * restoreAfterStockOrdinaryJobsOrThrow AFTER all stock library restore jobs
 * complete. A normal Yomotsu error log is NOT a successful completion signal.
 */
class PolarisYomotsuStrictRestoreSequence(
    private val coordinator: PolarisRestoreCoordinator,
    private val source: YomotsuPolarisSourceRestorePort,
) {
    fun preflightBeforeAnyWrites(bundle: BackupPolarisBundle?, ordinary: List<BackupManga>, libraryEntries: Boolean) {
        coordinator.preflight(bundle, ordinary, libraryEntries)
    }

    suspend fun restoreAfterStockOrdinaryJobsOrThrow(
        bundle: BackupPolarisBundle?,
        ordinary: List<BackupManga>,
        libraryEntries: Boolean,
        awaitStockOrdinaryJobs: suspend () -> Unit,
    ): List<RestoredPolarisWork> {
        // Avoid replay or even awaiting normal work here if restore does not
        // contain a Polaris segment. The original legacy path is unchanged.
        if (!libraryEntries || bundle == null) return emptyList()
        coordinator.preflight(bundle, ordinary, true)
        val keys = bundle.works.flatMap { it.links }
            .filterNot { it.isPending }
            .map { it.sourceId to it.sourceUrl }.toSet()
        return coordinator.restore(bundle, ordinary, true) {
            awaitStockOrdinaryJobs()
            // This strict replay is REQUIRED because stock BackupRestorer
            // catches some per-manga exceptions. Only linked ordinary children
            // are retried, with a mandatory DB chapter verification afterward.
            source.strictRestoreRequiredOrdinaryOrThrow(ordinary, keys)
        }
    }
}
