package polaris.spike001.backup.restore
import eu.kanade.tachiyomi.data.backup.models.*
import polaris.spike001.backup.parent.BackupPolarisParentPayload
import java.util.UUID
/** Host stand-in for the separately staged real @Serializable ProtoBuf envelope. */
class PolarisV2ProtoBufEnvelope(val formatVersion:Int,val work:BackupPolarisWork,
    val parent:BackupPolarisParentPayload,val referencedCategories:List<BackupCategory>) {
  fun validateDecoded() {
    require(formatVersion==2)
    require(work.canonicalUuid!=null &&
      runCatching { UUID.fromString(work.canonicalUuid).toString()==work.canonicalUuid }.getOrDefault(false))
    require(work.archiveWorkKey==work.canonicalUuid && parent.archiveUuid==work.canonicalUuid)
    require(parent.manga.source==6969L && parent.originalOrdinal>=0 && parent.manga.title==work.displayTitle)
    require(!work.rootSettings.infoManga && work.links.count{it.settings.infoManga}==1)
    require(work.links.isNotEmpty() && work.links.map{it.sourceId to it.sourceUrl}.distinct().size==work.links.size)
    require(work.links.all{it.sourceId!=6969L && it.sourceUrl.isNotBlank() && it.observedTitle.isNotBlank()})
    require((work.links.map{it.settings.chapterPriority}+work.rootSettings.chapterPriority).distinct().size==work.links.size+1)
    val orders=parent.manga.categories
    require(orders.distinct().size==orders.size && referencedCategories.size==orders.size &&
      referencedCategories.map{it.order}.toSet()==orders.toSet() &&
      referencedCategories.map{it.name}.distinct().size==referencedCategories.size &&
      referencedCategories.all{it.name.isNotBlank()})
  }
}
