package eu.kanade.tachiyomi.data.backup.models

private const val UUID_A = "123e4567-e89b-42d3-a456-426614174000"
private const val UUID_B = "123e4567-e89b-42d3-a456-426614174001"
private val flags = BackupPolarisMergeSettings(false, true, 2, 1, false)
private fun link(source: Long, url: String, pending: Boolean = false) = BackupPolarisLink(source, url, "Observed", flags, pending)
private fun work(uuid: String, vararg links: BackupPolarisLink) = BackupPolarisWork(uuid, "Virtual", flags, links.toList(), uuid)
private fun bundle(vararg works: BackupPolarisWork, extras: List<BackupManga> = emptyList()) = BackupPolarisBundle(works = works.toList(), supplementalManga = extras)
private fun failure(action: () -> Unit) { check(runCatching(action).isFailure) }

fun main() {
    var checked = 0
    fun scenario(name: String, body: () -> Unit) { body(); checked++; println("PENDING_SNAPSHOT_PASS $checked $name") }
    scenario("pending-only child cannot acquire a supplemental full manga") {
        failure { bundle(work(UUID_A, link(11, "/pending", true)), extras = listOf(BackupManga(11, "/pending"))).validateForImport() }
    }
    scenario("mixed child snapshot for pending link rejected even when another resolved link exists") {
        failure { bundle(work(UUID_A, link(11,"/pending",true),link(12,"/active")), extras = listOf(BackupManga(11,"/pending"))).validateForImport() }
    }
    scenario("resolved child may have a valid supplemental snapshot") {
        bundle(work(UUID_A, link(11, "/active")), extras = listOf(BackupManga(11, "/active"))).validateSnapshotCoverage(emptyList())
    }
    scenario("shared identity may be supplemental if resolved by at least one virtual work") {
        bundle(work(UUID_A, link(11,"/same",true)), work(UUID_B, link(11,"/same")), extras=listOf(BackupManga(11,"/same"))).validateSnapshotCoverage(emptyList())
    }
    scenario("same URL but different source does not resolve pending child") {
        failure { bundle(work(UUID_A,link(11,"/same",true),link(12,"/same")), extras=listOf(BackupManga(11,"/same"))).validateForImport() }
    }
    scenario("explicit pending without supplemental snapshot remains valid") {
        bundle(work(UUID_A,link(11,"/pending",true))).validateSnapshotCoverage(emptyList())
    }
    scenario("supplemental identity must also pass ordinary/supplemental disjointness") {
        val b=bundle(work(UUID_A,link(11,"/active")),extras=listOf(BackupManga(11,"/active")))
        failure { b.validateSnapshotCoverage(listOf(BackupManga(11,"/active"))) }
    }
    scenario("portable multi-source backup refuses ordinary virtual parent duplicate") {
        val b=bundle(work(UUID_A,link(11,"/active")))
        failure { b.validateSnapshotCoverage(listOf(BackupManga(11,"/active"), BackupManga(6969,"merged://legacy"))) }
    }
    scenario("empty optional Polaris section keeps ordinary legacy backup compatible") {
        BackupPolarisBundle().validateSnapshotCoverage(listOf(BackupManga(6969,"merged://legacy")))
    }
    println("POLARIS_PENDING_SNAPSHOT_MODEL_PASS $checked")
}
