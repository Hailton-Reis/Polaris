package polaris.spike001.backup.restore

/** Host API-shaped doubles. Production uses the actual coordinator types. */
data class BackupPolarisMergeSettings(val infoManga:Boolean=false,val getChapterUpdates:Boolean=false,val chapterSortMode:Long=2,val chapterPriority:Long=1,val downloadChapters:Boolean=false)
data class RestoredPolarisLink(val sourceId:Long,val sourceUrl:String,val realMangaId:Long?,val wasPending:Boolean,val settings:BackupPolarisMergeSettings)
data class RestoredPolarisWork(val archiveUuid:String,val title:String,val rootSettings:BackupPolarisMergeSettings,val children:List<RestoredPolarisLink>)
interface PolarisAtomicVirtualWorkPort { suspend fun commitAllOrThrow(works:List<RestoredPolarisWork>) }
