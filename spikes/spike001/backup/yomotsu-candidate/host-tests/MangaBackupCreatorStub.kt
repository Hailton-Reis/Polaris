package eu.kanade.tachiyomi.data.backup.create.creators
import eu.kanade.tachiyomi.data.backup.create.BackupOptions
import eu.kanade.tachiyomi.data.backup.models.BackupManga
import tachiyomi.domain.manga.model.Manga
open class MangaBackupCreator {
    var calls = 0
    var lastOptions: BackupOptions? = null
    var onBackup: (() -> Unit)? = null
    open suspend operator fun invoke(mangas: List<Manga>, options: BackupOptions): List<BackupManga> {
        calls++; lastOptions=options; onBackup?.invoke()
        return mangas.map { BackupManga(it.source, it.url, if(options.chapters) listOf("chapter-${it.id}") else emptyList()) }
    }
}
