package eu.kanade.tachiyomi.data.backup.models

private const val ID = "123e4567-e89b-42d3-a456-426614174000"
private val options = BackupPolarisMergeSettings(false, false, 2, 0, false)
private fun validBundle() = BackupPolarisBundle(
    works = listOf(BackupPolarisWork(ID, "Book", options,
        listOf(BackupPolarisLink(22, "/chapterbook", "Observed", options)), ID)),
    supplementalManga = listOf(BackupManga(22, "/chapterbook")),
)
fun main() {
    var checked = 0
    fun scenario(name: String, block: () -> Unit) { block(); checked++; println("BACKUP_FIELD_PASS $checked $name") }
    scenario("legacy model uses optional null section") { check(Backup(emptyList()).polaris == null) }
    scenario("exporter named polaris parameter is accepted by constructor") {
        val polarisBundle = validBundle()
        val archive = Backup(backupManga = emptyList(), polaris = polarisBundle)
        check(archive.polaris === polarisBundle)
    }
    scenario("consumer retrieves the same strongly typed portable section") {
        val archive = Backup(emptyList(), polaris = validBundle())
        archive.polaris!!.validateSnapshotCoverage(emptyList())
    }
    scenario("copy preserves optional field and ordinary manga list") {
        val normal = BackupManga(55, "/ordinary")
        val original = Backup(listOf(normal), polaris = validBundle())
        val cloned = original.copy(backupCategories = emptyList())
        check(cloned.polaris === original.polaris && cloned.backupManga.single() === normal)
    }
    scenario("restorer can detect unsupported pending supplemental before stock writes") {
        val bad = BackupPolarisBundle(works = listOf(BackupPolarisWork(ID, "Book", options,
            listOf(BackupPolarisLink(11, "/pending", "Observed", options, isPending = true)), ID)),
            supplementalManga = listOf(BackupManga(11, "/pending")))
        val archive = Backup(emptyList(), polaris = bad)
        check(runCatching { archive.polaris!!.validateSnapshotCoverage(archive.backupManga) }.isFailure)
    }
    println("POLARIS_BACKUP_FIELD_INTEROP_PASS $checked")
}
