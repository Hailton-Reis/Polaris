package tachiyomi.domain.manga.refresh

import tachiyomi.domain.manga.model.MergedMangaReference
import tachiyomi.domain.source.model.MERGED_SOURCE_ID

/** Resolve real, currently linked manga rows for a virtual work's refresh. */
object MergedRefreshTargets {
    fun childMangaIds(mergedMangaId: Long, references: List<MergedMangaReference>): List<Long> =
        references.asSequence()
            .filter { it.mergeId == mergedMangaId && it.mangaSourceId != MERGED_SOURCE_ID }
            .mapNotNull { it.mangaId }
            .filter { it > 0L && it != mergedMangaId }
            .distinct()
            .toList()
}
