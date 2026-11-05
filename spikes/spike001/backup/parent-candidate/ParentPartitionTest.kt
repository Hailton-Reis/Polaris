package polaris.spike001.backup.parent
import eu.kanade.tachiyomi.data.backup.models.BackupManga

private var n=0
private fun test(label:String,run:()->Unit) { run();++n;println("PASS $n $label") }
private fun fail(run:()->Unit){ check(runCatching(run).isFailure) }
private const val A="123e4567-e89b-42d3-a456-426614174000"
private const val B="123e4567-e89b-42d3-a456-426614174001"
private fun p(id:Long,uuid:String,url:String,title:String)=ExpectedVirtualParent(id,uuid,url,title)
private fun c(id:Long, manga:BackupManga)=CapturedMangaSnapshot(id,manga.source,manga.url,manga)
private val full=BackupManga(6969,"merged://work","Work","note saved",listOf(4,6),listOf("/chapter"),listOf("/history"),listOf("track"),byteArrayOf(0,1,2))
private val one=BackupManga(11,"/child","Child")
private val other=BackupManga(12,"/other","Other")
private fun split(data:List<CapturedMangaSnapshot> = listOf(c(101,one),c(900,full),c(102,other)),
                  specs:List<ExpectedVirtualParent> = listOf(p(900,A,"merged://work","Work")))=
    PolarisParentSnapshotPartitioner.partition(data,specs)
fun main(){
 test("full parent snapshot removed from ordinary lane"){ val r=split();check(r.ordinaryManga==listOf(one,other));check(r.virtualParents.single().manga===full) }
 test("metadata categories notes chapters history trackers memo retained"){val r=split().virtualParents.single().manga;check(r.notes=="note saved"&&r.categories==listOf(4L,6L)&&r.chapters==listOf("/chapter")&&r.history==listOf("/history")&&r.tracking==listOf("track")&&r.memo.contentEquals(byteArrayOf(0,1,2)))}
 test("restore original position exactly"){val r=split();check(r.virtualParents.single().originalOrdinal==1);check(r.reassembleOriginalOrder().zip(listOf(one,full,other)).all{(a,b)->a===b})}
 test("parent ordinal zero"){val r=split(listOf(c(900,full),c(101,one)));check(r.virtualParents.single().originalOrdinal==0&&r.reassembleOriginalOrder().first()===full)}
 test("parent ordinal last"){val r=split(listOf(c(101,one),c(900,full)));check(r.virtualParents.single().originalOrdinal==1)}
 test("two parents and single child preserves order"){val second=BackupManga(6969,"merged://two","Second");val r=split(listOf(c(900,full),c(101,one),c(901,second)),listOf(p(900,A,"merged://work","Work"),p(901,B,"merged://two","Second")));check(r.virtualParents.map{it.archiveUuid}==listOf(A,B));check(r.reassembleOriginalOrder()==listOf(full,one,second))}
 test("reject missing parent uuid"){fail{split(specs=emptyList())}}
 test("reject second virtual without identity"){val two=BackupManga(6969,"merged://two","Two");fail{split(listOf(c(900,full),c(901,two)))}}
 test("reject absent UUID parent from original archive"){fail{split(specs=listOf(p(999,A,"merged://work","Work")))}}
 test("reject duplicate local manga id"){fail{split(listOf(c(900,full),c(900,full)))}}
 test("reject duplicate parent local id"){fail{split(specs=listOf(p(900,A,"merged://work","Work"),p(900,B,"merged://work","Work")))}}
 test("reject duplicate UUID for different parents"){val two=BackupManga(6969,"merged://two","Two");fail{split(listOf(c(900,full),c(901,two)),listOf(p(900,A,"merged://work","Work"),p(901,A,"merged://two","Two")))}}
 test("reject noncanonical UUID"){fail{split(specs=listOf(p(900,"NOT-UUID","merged://work","Work")))}}
 test("reject source+URL snapshot mismatch"){fail{split(data=listOf(CapturedMangaSnapshot(101,99,"/child",one),c(900,full)))}}
 test("reject parent title mismatch"){fail{split(specs=listOf(p(900,A,"merged://work","Changed")))}}
 test("reject parent URL mismatch"){fail{split(specs=listOf(p(900,A,"merged://other","Work")))}}
 test("reject expecting nonvirtual parent"){fail{split(specs=listOf(p(101,A,"/child","Child")))}}
 test("reject invalid manga local id"){fail{split(data=listOf(c(-1,one),c(900,full)))}}
 test("reject negative expected ID"){fail{split(specs=listOf(p(-1,A,"merged://work","Work")))}}
 test("reject tampered split: duplicate ordinal"){val r=split();fail{r.copy(virtualParents=r.virtualParents+r.virtualParents.single()).reassembleOriginalOrder()}}
 test("reject tampered split: missing ordinary"){val r=split();fail{r.copy(ordinaryManga=emptyList()).reassembleOriginalOrder()}}
 test("reject tampered split: wrong count"){val r=split();fail{r.copy(originalCount=4).reassembleOriginalOrder()}}
 test("require unchanged object reference: no projection"){val r=split();check(r.virtualParents.single().manga.memo===full.memo)}
 println("POLARIS_PARENT_SPLIT_HOST_PASS $n")
}
