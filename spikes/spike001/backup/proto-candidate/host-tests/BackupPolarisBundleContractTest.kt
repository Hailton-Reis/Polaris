package eu.kanade.tachiyomi.data.backup.models

private var checks = 0
private fun trial(name: String, body: () -> Unit) { body(); checks++; println("PASS $checks $name") }
private fun rejected(body: () -> Unit) { check(runCatching(body).isFailure) }

fun main() {
    val root = BackupPolarisMergeSettings(false,false,2,999,false)
    val a = BackupPolarisLink(1001L,"/a","A",BackupPolarisMergeSettings(true,true,2,1,true))
    val b = BackupPolarisLink(-2002L,"/b","B",BackupPolarisMergeSettings(false,false,2,2,false))
    val work=BackupPolarisWork("stable-1","Work",root,listOf(a,b),"123e4567-e89b-12d3-a456-426614174000")
    val pkg=BackupPolarisBundle(works=listOf(work),supplementalManga=listOf(BackupManga(-2002L,"/b")))
    trial("valid portable snapshot and negative source ID") { pkg.validateForImport() }
    trial("empty optional bundle is valid") { BackupPolarisBundle().validateForImport() }
    trial("unknown future version rejected") { rejected { pkg.copy(formatVersion=2).validateForImport() } }
    trial("version zero rejected") { rejected { pkg.copy(formatVersion=0).validateForImport() } }
    trial("duplicate work archive identity rejected") { rejected { pkg.copy(works=listOf(work,work)).validateForImport() } }
    trial("blank archive key rejected") { rejected { pkg.copy(works=listOf(work.copy(archiveWorkKey=""))).validateForImport() } }
    trial("blank work title rejected") { rejected { pkg.copy(works=listOf(work.copy(displayTitle=" "))).validateForImport() } }
    trial("empty link set rejected") { rejected { pkg.copy(works=listOf(work.copy(links=emptyList()))).validateForImport() } }
    trial("duplicate source+url link rejected") { rejected { pkg.copy(works=listOf(work.copy(links=listOf(a,a)))).validateForImport() } }
    trial("same URL under two sources accepted") { pkg.copy(works=listOf(work.copy(links=listOf(a,b.copy(sourceUrl="/a")))),supplementalManga=emptyList()).validateForImport() }
    trial("synthetic child rejected") { rejected { pkg.copy(works=listOf(work.copy(links=listOf(a.copy(sourceId=6969L))))).validateForImport() } }
    trial("root metadata rejected") { rejected { pkg.copy(works=listOf(work.copy(rootSettings=a.settings))).validateForImport() } }
    trial("two metadata sources rejected") { rejected { pkg.copy(works=listOf(work.copy(links=listOf(a,b.copy(settings=a.settings))))).validateForImport() } }
    trial("unknown snapshot rejected") { rejected { pkg.copy(supplementalManga=listOf(BackupManga(999L,"/unknown"))).validateForImport() } }
    trial("duplicate source snapshot rejected") { rejected { pkg.copy(supplementalManga=pkg.supplementalManga+pkg.supplementalManga).validateForImport() } }
    trial("synthetic snapshot rejected") { rejected { pkg.copy(supplementalManga=listOf(BackupManga(6969L,"/fake"))).validateForImport() } }
    trial("invalid blank snapshot URL rejected") { rejected { pkg.copy(supplementalManga=listOf(BackupManga(-2002L,""))).validateForImport() } }
    trial("link not reconstructed from snapshot of absent variant") { rejected { pkg.copy(works=listOf(work.copy(links=listOf(a)))).validateForImport() } }
    println("POLARIS_BACKUP_PROTO_MODEL_PASS $checks")
}
