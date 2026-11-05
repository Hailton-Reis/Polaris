package eu.kanade.tachiyomi.data.backup.models
import polaris.spike001.backup.parent.BackupPolarisParentPayload
class BackupPolarisMergeSettings(
    val infoManga:Boolean = false,
    val getChapterUpdates:Boolean = false,
    val chapterSortMode:Long = 2,
    var chapterPriority:Long = 0,
    val downloadChapters:Boolean = false,
)
class BackupPolarisLink(var sourceId:Long,var sourceUrl:String,var observedTitle:String,
    val settings:BackupPolarisMergeSettings,var isPending:Boolean=false)
class BackupPolarisWork(val archiveWorkKey:String,var displayTitle:String,val canonicalUuid:String?,
    val rootSettings:BackupPolarisMergeSettings,val links:MutableList<BackupPolarisLink>)
class BackupPolarisBundle(val formatVersion:Int,val works:List<BackupPolarisWork>,
    val parentSnapshots:List<BackupPolarisParentPayload>) {
  fun validateSnapshotCoverage(ordinaryManga:List<BackupManga>) {
    require(formatVersion==2 && works.isNotEmpty() && parentSnapshots.size==works.size)
    require(ordinaryManga.none {it.source==6969L})
    require(works.map{it.archiveWorkKey}.distinct().size==works.size)
    require(parentSnapshots.map{it.archiveUuid}.distinct().size==parentSnapshots.size)
  }
}
