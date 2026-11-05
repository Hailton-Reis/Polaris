package tachiyomi.domain.manga.refresh

import kotlinx.coroutines.CancellationException
import tachiyomi.domain.manga.model.MergedMangaReference

/**
 * Refresh linked REAL child manga, allowing one source to fail independently.
 * No network, source, or storage implementation is created here; the caller
 * supplies Yomotsu's existing update function for each child manga ID.
 */
object MergedRefreshCoordinator {
    data class Result(val succeededChildIds: List<Long>, val failedChildIds: List<Long>)

    suspend fun refresh(
        mergedMangaId: Long,
        references: List<MergedMangaReference>,
        refreshChild: suspend (Long) -> Unit,
        onFailure: (Long, Exception) -> Unit = { _, _ -> },
    ): Result {
        val targets = MergedRefreshTargets.childMangaIds(mergedMangaId, references)
        require(targets.isNotEmpty()) { "No linked real manga available for merged refresh" }
        val succeeded = mutableListOf<Long>()
        val failed = mutableListOf<Long>()
        var lastFailure: Exception? = null
        for (childId in targets) {
            try {
                refreshChild(childId)
                succeeded += childId
            } catch (error: CancellationException) {
                throw error
            } catch (error: Exception) {
                failed += childId
                lastFailure = error
                onFailure(childId, error)
            }
        }
        if (succeeded.isEmpty()) throw requireNotNull(lastFailure)
        return Result(succeeded, failed)
    }
}
