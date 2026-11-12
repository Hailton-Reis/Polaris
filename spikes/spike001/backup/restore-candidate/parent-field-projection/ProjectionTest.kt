package polaris.spike001.backup.restore

import eu.kanade.tachiyomi.data.backup.models.*
import eu.kanade.tachiyomi.source.model.UpdateStrategy
import kotlinx.serialization.json.JsonPrimitive

private val uuid = "c95d6621-e236-4024-ae3c-49dd116d2f30"
private var passes = 0
private fun case(name: String, body: () -> Unit) { body(); passes++; println("PASS $name") }
private fun ok(v: Boolean) { check(v) { "Expected true" } }
private fun fails(code: String, body: () -> Unit) {
    val thrown = runCatching(body).exceptionOrNull()
    check(thrown is IllegalArgumentException && thrown.message == code) {
        "Expected $code, got ${thrown?.javaClass?.simpleName}: ${thrown?.message}"
    }
}
private fun parent(): BackupManga = BackupManga(
    source=6969, url="merged://legacy-9", title="My Work", artist="A", author="B", description="Full description",
    genre=listOf("Action", "Magic"), status=3, thumbnailUrl="https://example.invalid/thumb", dateAdded=123,
    viewer=17, viewer_flags=23, chapters=listOf(
        BackupChapter("/ch1", "One", scanlator="Scan", read=true,bookmark=true,lastPageRead=4,dateFetch=12,
            dateUpload=13,chapterNumber=1.5f,sourceOrder=8,lastModifiedAt=777,version=5,memo="{\"custom\":\"chapter-value\"}".toByteArray()),
        BackupChapter("/ch2", "Two",read=false,chapterNumber=2.0f)),
    categories=listOf(7, 8), tracking=listOf(BackupTracking(syncId=3,libraryId=99,mediaId=312,trackingUrl="https://tracker.invalid",title="Track",lastChapterRead=1.5f,totalChapters=44,score=8.5f,status=2,startedReadingDate=50,finishedReadingDate=80,private=true)),
    favorite=true,chapterFlags=27,history=listOf(BackupHistory("/ch1",1400,21)),
    updateStrategy=UpdateStrategy.ONLY_FETCH_ONCE,lastModifiedAt=9988,favoriteModifiedAt=500,
    excludedScanlators=listOf("Excluded"),version=44,notes="never overwrite",initialized=true,
    memo="{\"unknown-key\":\"preserve-me\"}".toByteArray()
)
private fun prepare(p: BackupManga = parent(), id:Long=900, cats:Map<Long,Long> = mapOf(7L to 70L,8L to 80L), u:String=uuid) =
    PolarisBackupMangaSqlProjection.prepare(p,u,id,cats)

fun main() {
    case("full prepared payload"){val x=prepare();ok(x.chapters.size==2&&x.history.size==1&&x.tracking.size==1&&x.categories==listOf(70L,80L))}
    case("uuid destination, original archive unchanged"){val x=parent();val t=prepare(x);ok(x.url=="merged://legacy-9"&&t.parent.destinationUrl=="merged://polaris/$uuid")}
    case("source 6969"){ok(prepare().parent.source==6969L)}
    case("parent reserved id"){ok(prepare(id=12).parent.reservedParentId==12L)}
    case("title"){ok(prepare().parent.title=="My Work")}
    case("artist"){ok(prepare().parent.artist=="A")}
    case("author"){ok(prepare().parent.author=="B")}
    case("description"){ok(prepare().parent.description=="Full description")}
    case("genre entries intact"){ok(prepare().parent.genre==listOf("Action","Magic"))}
    case("manga status"){ok(prepare().parent.status==3L)}
    case("thumbnail"){ok(prepare().parent.thumbnailUrl=="https://example.invalid/thumb")}
    case("favorite"){ok(prepare().parent.favorite)}
    case("initialized"){ok(prepare().parent.initialized)}
    case("viewer flags precedence"){ok(prepare().parent.viewer==23L)}
    case("viewer legacy fallback"){val x=parent();x.viewer_flags=null;ok(prepare(x).parent.viewer==17L)}
    case("chapter flags"){ok(prepare().parent.chapterFlags==27L)}
    case("date added"){ok(prepare().parent.dateAdded==123L)}
    case("update strategy"){ok(prepare().parent.updateStrategy==UpdateStrategy.ONLY_FETCH_ONCE)}
    case("last modified"){ok(prepare().parent.lastModifiedAt==9988L)}
    case("favorite modified"){ok(prepare().parent.favoriteModifiedAt==500L)}
    case("version"){ok(prepare().parent.version==44L)}
    case("notes"){ok(prepare().parent.notes=="never overwrite")}
    case("memo unknown keys retained"){val x=prepare();ok(x.parent.memo["unknown-key"]==JsonPrimitive("preserve-me"))}
    case("memo uuid injected"){val x=prepare();ok(x.parent.memo[PolarisBackupMangaSqlProjection.UUID_MEMO_KEY]==JsonPrimitive(uuid))}
    case("memo matching existing UUID accepted"){val x=parent();x.memo="{\"polaris.merge.work.uuid\":\"$uuid\",\"custom\":\"v\"}".toByteArray();ok(prepare(x).parent.memo["custom"]==JsonPrimitive("v"))}
    case("chapter url"){ok(prepare().chapters[0].url=="/ch1")}
    case("chapter name"){ok(prepare().chapters[0].name=="One")}
    case("chapter scanlator"){ok(prepare().chapters[0].scanlator=="Scan")}
    case("chapter read and bookmark"){val c=prepare().chapters[0];ok(c.read&&c.bookmark)}
    case("chapter last page"){ok(prepare().chapters[0].lastPageRead==4L)}
    case("chapter dates"){val c=prepare().chapters[0];ok(c.dateFetch==12L&&c.dateUpload==13L)}
    case("chapter number preserves backup Float"){ok(prepare().chapters[0].chapterNumber.toFloat()==1.5f)}
    case("chapter source order"){ok(prepare().chapters[0].sourceOrder==8L)}
    case("chapter timestamp and version"){val c=prepare().chapters[0];ok(c.lastModifiedAt==777L&&c.version==5L)}
    case("chapter memo preserved"){ok(prepare().chapters[0].memo["custom"]==JsonPrimitive("chapter-value"))}
    case("chapter parent id"){ok(prepare(id=97).chapters.all{it.parentId==97L})}
    case("all rows is_syncing zero"){val x=prepare();ok(x.parent.isSyncing==0L&&x.chapters.all{it.isSyncing==0L})}
    case("history exact url and duration"){val h=prepare().history[0];ok(h.chapterUrl=="/ch1"&&h.readDuration==21L&&h.lastRead==1400L)}
    case("track sync and media IDs"){val t=prepare().tracking[0];ok(t.syncId==3L&&t.remoteId==312L)}
    case("track library and title"){val t=prepare().tracking[0];ok(t.libraryId==99L&&t.title=="Track")}
    case("track progress score status"){val t=prepare().tracking[0];ok(t.lastChapterRead==1.5&&t.score==8.5&&t.status==2L)}
    case("track dates privacy"){val t=prepare().tracking[0];ok(t.startDate==50L&&t.finishDate==80L&&t.private)}
    case("track remote url and chapter count"){val t=prepare().tracking[0];ok(t.remoteUrl=="https://tracker.invalid"&&t.totalChapters==44L)}
    case("scanlator exclusions preserved"){ok(prepare().excludedScanlators==listOf("Excluded"))}
    case("technical unarchived defaults explicit"){val t=prepare().parent;ok(t.lastUpdate==null&&t.nextUpdate==null&&t.calculateInterval==0L&&t.coverLastModified==0L)}
    case("technical caller policy explicit"){val t=PolarisBackupMangaSqlProjection.prepare(parent(),uuid,900,mapOf(7L to 70L,8L to 80L),PolarisBackupMangaSqlProjection.TechnicalState(1,2,3,4)).parent;ok(t.lastUpdate==1L&&t.nextUpdate==2L&&t.coverLastModified==3L&&t.calculateInterval==4L)}
    case("empty optional children and tags"){val p=parent();p.chapters=emptyList();p.history=emptyList();p.tracking=emptyList();p.categories=emptyList();p.excludedScanlators=emptyList();val x=prepare(p);ok(x.chapters.isEmpty()&&x.history.isEmpty()&&x.categories.isEmpty()&&x.tracking.isEmpty())}
    case("legacy tracking mediaIdInt fallback"){val p=parent();p.tracking=listOf(BackupTracking(3,1,mediaIdInt=12,mediaId=0));ok(prepare(p).tracking[0].remoteId==12L)}
    case("two equal tracking IDs accepted"){val p=parent();p.tracking=listOf(BackupTracking(3,1,mediaIdInt=12,mediaId=12));ok(prepare(p).tracking[0].remoteId==12L)}
    case("invalid reserved zero"){fails("POLARIS_V2_INVALID_PARENT_ID"){prepare(id=0)}}
    case("invalid reserved negative"){fails("POLARIS_V2_INVALID_PARENT_ID"){prepare(id=-1)}}
    case("reject non-merged source"){val p=parent();p.source=3;fails("POLARIS_V2_NOT_VIRTUAL_PARENT"){prepare(p)}}
    case("reject empty parent archive url"){val p=parent();p.url="";fails("POLARIS_V2_INVALID_ARCHIVED_PARENT"){prepare(p)}}
    case("reject empty parent title"){val p=parent();p.title="";fails("POLARIS_V2_INVALID_ARCHIVED_PARENT"){prepare(p)}}
    case("reject random work identifier"){fails("POLARIS_V2_NONCANONICAL_UUID"){prepare(u="not-a-uuid")}}
    case("reject uppercase UUID"){fails("POLARIS_V2_NONCANONICAL_UUID"){prepare(u=uuid.uppercase())}}
    case("reject malformed memo"){val p=parent();p.memo="garbage".toByteArray();fails("Invalid JSON"){prepare(p)}}
    case("reject conflicting memo UUID"){val p=parent();p.memo="{\"polaris.merge.work.uuid\":\"wrong\"}".toByteArray();fails("POLARIS_V2_CONFLICTING_MEMO_UUID"){prepare(p)}}
    case("reject genre with delimiter"){val p=parent();p.genre=listOf("Action, Adventure");fails("POLARIS_V2_GENRE_NOT_ROUNDTRIPPABLE"){prepare(p)}}
    case("reject genre one empty entry"){val p=parent();p.genre=listOf("");fails("POLARIS_V2_GENRE_NOT_ROUNDTRIPPABLE"){prepare(p)}}
    case("reject empty genre collision"){val p=parent();p.genre=listOf("","");fails("POLARIS_V2_GENRE_NOT_ROUNDTRIPPABLE"){prepare(p)}}
    case("reject negative version"){val p=parent();p.version=-1;fails("POLARIS_V2_INVALID_PARENT_FIELDS"){prepare(p)}}
    case("reject negative parent timestamp"){val p=parent();p.lastModifiedAt=-1;fails("POLARIS_V2_INVALID_PARENT_FIELDS"){prepare(p)}}
    case("reject invalid technical field"){fails("POLARIS_V2_INVALID_PARENT_FIELDS"){PolarisBackupMangaSqlProjection.prepare(parent(),uuid,900,mapOf(7L to 70L,8L to 80L),PolarisBackupMangaSqlProjection.TechnicalState(coverLastModified=-1))}}
    case("reject absent category order"){fails("POLARIS_V2_MISSING_CATEGORY_ORDER"){prepare(cats=mapOf(7L to 70L))}}
    case("reject zero category id"){fails("POLARIS_V2_MISSING_CATEGORY_ORDER"){prepare(cats=mapOf(7L to 70L,8L to 0L))}}
    case("reject duplicate category orders"){val p=parent();p.categories=listOf(7,7);fails("POLARIS_V2_DUPLICATE_CATEGORY_ORDER"){prepare(p)}}
    case("reject destination category collisions"){fails("POLARIS_V2_CATEGORY_DESTINATION_COLLISION"){prepare(cats=mapOf(7L to 70L,8L to 70L))}}
    case("reject duplicate chapter URLs"){val p=parent();p.chapters=p.chapters+BackupChapter("/ch1","duplicate");fails("POLARIS_V2_DUPLICATE_OR_EMPTY_CHAPTER_URL"){prepare(p)}}
    case("reject empty chapter URL"){val p=parent();p.chapters=listOf(BackupChapter("","empty"));p.history=emptyList();fails("POLARIS_V2_DUPLICATE_OR_EMPTY_CHAPTER_URL"){prepare(p)}}
    case("reject blank chapter name"){val p=parent();p.chapters[0].name="";fails("POLARIS_V2_INVALID_CHAPTER_FIELD"){prepare(p)}}
    case("reject NaN chapter number"){val p=parent();p.chapters[0].chapterNumber=Float.NaN;fails("POLARIS_V2_INVALID_CHAPTER_FIELD"){prepare(p)}}
    case("reject Infinity chapter number"){val p=parent();p.chapters[0].chapterNumber=Float.POSITIVE_INFINITY;fails("POLARIS_V2_INVALID_CHAPTER_FIELD"){prepare(p)}}
    case("reject negative last page"){val p=parent();p.chapters[0].lastPageRead=-1;fails("POLARIS_V2_INVALID_CHAPTER_FIELD"){prepare(p)}}
    case("reject negative chapter version"){val p=parent();p.chapters[0].version=-1;fails("POLARIS_V2_INVALID_CHAPTER_FIELD"){prepare(p)}}
    case("reject corrupt chapter memo"){val p=parent();p.chapters[0].memo="oops".toByteArray();fails("Invalid JSON"){prepare(p)}}
    case("reject unknown history chapter"){val p=parent();p.history=listOf(BackupHistory("/missing",100,5));fails("POLARIS_V2_UNRESOLVED_OR_DUPLICATE_HISTORY"){prepare(p)}}
    case("reject duplicate history chapter"){val p=parent();p.history=p.history+p.history[0];fails("POLARIS_V2_UNRESOLVED_OR_DUPLICATE_HISTORY"){prepare(p)}}
    case("reject negative history duration"){val p=parent();p.history=listOf(BackupHistory("/ch1",10,-1));fails("POLARIS_V2_INVALID_HISTORY_FIELD"){prepare(p)}}
    case("reject negative history time"){val p=parent();p.history=listOf(BackupHistory("/ch1",-1,0));fails("POLARIS_V2_INVALID_HISTORY_FIELD"){prepare(p)}}
    case("reject duplicate sync ID"){val p=parent();p.tracking=p.tracking+p.tracking[0];fails("POLARIS_V2_DUPLICATE_TRACKER_ID"){prepare(p)}}
    case("reject legacy/new remote conflict"){val p=parent();p.tracking=listOf(BackupTracking(3,1,mediaIdInt=12,mediaId=13));fails("POLARIS_V2_CONFLICTING_TRACK_MEDIA_IDS"){prepare(p)}}
    case("reject nonfinite tracker score"){val p=parent();p.tracking[0].score=Float.NaN;fails("POLARIS_V2_INVALID_TRACK_FIELDS"){prepare(p)}}
    case("reject nonfinite tracker progress"){val p=parent();p.tracking[0].lastChapterRead=Float.POSITIVE_INFINITY;fails("POLARIS_V2_INVALID_TRACK_FIELDS"){prepare(p)}}
    case("reject tracker negative total"){val p=parent();p.tracking[0].totalChapters=-1;fails("POLARIS_V2_INVALID_TRACK_FIELDS"){prepare(p)}}
    case("reject tracker negative library ID"){val p=parent();p.tracking[0].libraryId=-1;fails("POLARIS_V2_INVALID_TRACK_FIELDS"){prepare(p)}}
    case("reject repeated scanlator exclusion"){val p=parent();p.excludedScanlators=listOf("x","x");fails("POLARIS_V2_INVALID_SCANLATOR_EXCLUSIONS"){prepare(p)}}
    case("reject blank scanlator exclusion"){val p=parent();p.excludedScanlators=listOf("");fails("POLARIS_V2_INVALID_SCANLATOR_EXCLUSIONS"){prepare(p)}}
    case("empty memo retained with UUID"){val p=parent();p.memo="{}".toByteArray();ok(prepare(p).parent.memo.size==1)}
    println("POLARIS_BACKUP_MANGA_TYPED_PROJECTION_PASS $passes")
}
