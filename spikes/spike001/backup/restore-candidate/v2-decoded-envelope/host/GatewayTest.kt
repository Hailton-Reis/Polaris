package polaris.spike001.backup.restore
import eu.kanade.tachiyomi.data.backup.models.*
import polaris.spike001.backup.parent.BackupPolarisParentPayload
import java.nio.charset.StandardCharsets
private var passed = 0
private fun ok(s:String,f:()->Unit){f();passed++;println("PASS $passed $s")}
private fun reject(s:String,f:()->Unit)=ok(s){check(runCatching(f).isFailure){"Expected refusal: $s"}}
private const val UUID="123e4567-e89b-42d3-a456-426614174000"
private data class BundleFixture(val bundle:BackupPolarisBundle,val parent:BackupManga,val work:BackupPolarisWork)
private fun fixture():BundleFixture {
  val manga=BackupManga(6969,"/old","Manga", mutableListOf(8),chapterNames=mutableListOf("Chapter 1","第二话"))
  val work=BackupPolarisWork(UUID,"Manga",UUID,BackupPolarisMergeSettings(false,10),
    mutableListOf(BackupPolarisLink(77,"/real","Source",BackupPolarisMergeSettings(true,0))))
  return BundleFixture(BackupPolarisBundle(2,listOf(work),listOf(BackupPolarisParentPayload(UUID,manga,0))),manga,work)
}
private val archivedCats=listOf(BackupCategory("Português",8))
private class EnvelopeHostCodec:PolarisV2EnvelopeCodec<PolarisV2ProtoBufEnvelope> {
  private var mostRecent:PolarisV2ProtoBufEnvelope?=null
  override fun encodeCanonical(value:PolarisV2ProtoBufEnvelope):ByteArray {
    value.validateDecoded()
    mostRecent=value
    val parts=listOf(value.formatVersion.toString(),value.work.archiveWorkKey,value.work.displayTitle,
      value.work.canonicalUuid?:"",value.work.rootSettings.infoManga.toString(),value.work.rootSettings.chapterPriority.toString(),
      value.parent.archiveUuid,value.parent.originalOrdinal.toString(),value.parent.manga.source.toString(),value.parent.manga.url,
      value.parent.manga.title,value.parent.manga.memo,value.parent.manga.chapterNames.size.toString())+
      value.parent.manga.chapterNames+
      listOf(value.parent.manga.categories.size.toString())+value.parent.manga.categories.map{it.toString()}+
      listOf(value.work.links.size.toString())+value.work.links.flatMap{
        listOf(it.sourceId.toString(),it.sourceUrl,it.observedTitle,it.settings.infoManga.toString(),
        it.settings.chapterPriority.toString(),it.isPending.toString())}+
      listOf(value.referencedCategories.size.toString())+value.referencedCategories.flatMap{listOf(it.name,it.order.toString())}
    return parts.joinToString(""){v-> val bytes=v.toByteArray(StandardCharsets.UTF_8);"${bytes.size}:$v"}.toByteArray(StandardCharsets.UTF_8)
  }
  override fun decodeCanonical(bytes:ByteArray):PolarisV2ProtoBufEnvelope =
    checkNotNull(mostRecent) {"HOST_DECODE_WITHOUT_ENCODE"}
}
// The host codec is a test double; no claim of real ProtoBuf wire decoding.
private val codec=EnvelopeHostCodec()
private fun admit(f:BundleFixture=fixture(),cat: List<BackupCategory> = archivedCats)=
 PolarisV2DecodedEnvelopeGateway.admitDecodedParent(f.bundle,emptyList(),cat,UUID,codec)
fun main(){
 ok("admit real archive UUID + full parent + categories") {val a=admit();check(a.sha256.length==64 && a.size>0)}
 ok("snapshot does not accept separate external bytes") {val a=admit();check(a.verifyBeforeTransaction()==a.sha256)}
 reject("refuse wrong UUID") {PolarisV2DecodedEnvelopeGateway.admitDecodedParent(fixture().bundle,emptyList(),archivedCats,"wrong",codec)}
 reject("refuse legacy v1") {val f=fixture();PolarisV2DecodedEnvelopeGateway.admitDecodedParent(BackupPolarisBundle(1,f.bundle.works,f.bundle.parentSnapshots),emptyList(),archivedCats,UUID,codec)}
 reject("refuse missing archived category snapshot") {admit(cat=emptyList())}
 reject("refuse ambiguous archived category order") {admit(cat=archivedCats+BackupCategory("other",8))}
 reject("refuse duplicate parent categories") {val f=fixture();f.parent.categories.add(8);admit(f)}
 reject("refuse wrong archived category order") {admit(cat=listOf(BackupCategory("Português",4)))}
 reject("refuse duplicate portable source pair") {val f=fixture();f.work.links.add(f.work.links[0]);admit(f)}
 reject("refuse changed virtual title") {val f=fixture();f.parent.title="changed";admit(f)}
 reject("refuse nonvirtual parent source") {val f=fixture();f.parent.source=99L;admit(f)}
 reject("refuse no metadata info source") {val f=fixture();f.work.links.clear();admit(f)}
 reject("refuse portable root as metadata source") {val f=fixture();val w=BackupPolarisWork(UUID,"Manga",UUID,BackupPolarisMergeSettings(true,10),f.work.links);admit(f.copy(bundle=BackupPolarisBundle(2,listOf(w),f.bundle.parentSnapshots)))}
 reject("refuse changed archive categories after binding") {val f=fixture();val a=admit(f);f.parent.categories[0]=12L;a.verifyBeforeTransaction()}
 reject("refuse changed archive title after binding") {val f=fixture();val a=admit(f);f.parent.title="edited";a.verifyBeforeTransaction()}
 reject("refuse changed archive chapter after binding") {val f=fixture();val a=admit(f);f.parent.chapterNames[0]="edited";a.verifyBeforeTransaction()}
 reject("refuse changed portable URL after binding") {val f=fixture();val a=admit(f);f.work.links[0]=BackupPolarisLink(77,"/changed","Source",BackupPolarisMergeSettings(true,0));a.verifyBeforeTransaction()}
 reject("refuse changed note/memo after binding") {val f=fixture();val a=admit(f);f.parent.memo="{}";a.verifyBeforeTransaction()}
 ok("different source order changes digest") {val f=fixture();val a=admit(f);f.work.links.add(BackupPolarisLink(88,"/b","B",BackupPolarisMergeSettings(false,2)));val b=admit(f);check(a.sha256!=b.sha256)}
 ok("portable output includes multilingual fields") {val a=admit();check(String(a.canonicalBytes()).contains("Português") && String(a.canonicalBytes()).contains("第二话"))}
 reject("changed category name after admission fails before write") {
    val f=fixture();val cats=listOf(BackupCategory("Original",8));val a=admit(f,cats)
    cats[0].name="Renamed";a.verifyBeforeTransaction()
 }
 reject("changed category order after admission fails before write") {
    val f=fixture();val cats=listOf(BackupCategory("Original",8));val a=admit(f,cats)
    cats[0].order=22;a.verifyBeforeTransaction()
 }
 println("POLARIS_V2_DECODED_ENVELOPE_HOST_PASS $passed")
}
