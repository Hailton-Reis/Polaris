package eu.kanade.tachiyomi.data.backup.models
class BackupManga(var source:Long,var url:String,var title:String,var categories:MutableList<Long> = mutableListOf(),
    var memo:String="{\"memo\":true}", var chapterNames:MutableList<String> = mutableListOf("one"))
class BackupCategory(var name:String,var order:Long)
class BackupPolarisMergeSettings(val infoManga:Boolean,val chapterPriority:Long)
class BackupPolarisLink(val sourceId:Long,val sourceUrl:String,val observedTitle:String,
    val settings:BackupPolarisMergeSettings,val isPending:Boolean=false)
class BackupPolarisWork(val archiveWorkKey:String,val displayTitle:String,val canonicalUuid:String?,
    val rootSettings:BackupPolarisMergeSettings,val links:MutableList<BackupPolarisLink>)
class BackupPolarisBundle(val formatVersion:Int,val works:List<BackupPolarisWork>,
    val parentSnapshots:List<polaris.spike001.backup.parent.BackupPolarisParentPayload>) {
    fun validateSnapshotCoverage(ordinaryManga:List<BackupManga>) {
        require(formatVersion==2 && works.isNotEmpty() && parentSnapshots.size==works.size)
        require(ordinaryManga.none { it.source==6969L })
        require(works.map{it.archiveWorkKey}.distinct().size==works.size)
    }
}
