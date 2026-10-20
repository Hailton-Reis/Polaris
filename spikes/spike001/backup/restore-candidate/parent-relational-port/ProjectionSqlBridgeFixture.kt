package polaris.spike001.backup.restore

import eu.kanade.tachiyomi.data.backup.models.*
import eu.kanade.tachiyomi.source.model.UpdateStrategy
import kotlinx.serialization.json.JsonObject

/** HOST TEST FIXTURE ONLY: emit the real staged Kotlin projection as a JSON row
 * set for the Python SQLite native-table writer. Host annotations/adapters are
 * intentionally small doubles; this is NOT real ProtoBuf or Android. */
private const val UUID = "123e4567-e89b-42d3-a456-426614174000"
private fun quote(s: String): String = buildString {
    append('"')
    for (c in s) when (c) {
        '\\' -> append("\\\\")
        '"' -> append("\\\"")
        '\n' -> append("\\n")
        '\r' -> append("\\r")
        '\t' -> append("\\t")
        else -> if (c.code < 0x20) append("\\u%04x".format(c.code)) else append(c)
    }
    append('"')
}
private fun json(obj: Any?): String = when (obj) {
    null -> "null"
    is JsonObject -> obj.toString() // test double emits valid JSON for simple string entries
    is String -> quote(obj)
    is Boolean -> if (obj) "true" else "false"
    is Number -> obj.toString()
    is UpdateStrategy -> obj.ordinal.toString()
    is Map<*,*> -> obj.entries.joinToString(",", "{", "}") { (k,v) ->
        quote(k as String) + ":" + json(v)
    }
    is Iterable<*> -> obj.joinToString(",", "[", "]") { json(it) }
    else -> error("unsupported fixture type: ${obj.javaClass.simpleName}")
}

fun main() {
    val archive = BackupManga(
        source=6969, url="merged://old-url",title="Projected Parent",artist="Artist",
        description="Bridge", genre=listOf("Action", "Mystery"),status=2, dateAdded=120,
        chapters=listOf(BackupChapter("/ch-proj", "Projected Chapter", scanlator="One",read=true,
          bookmark=true,lastPageRead=8,dateFetch=3,dateUpload=4,chapterNumber=1.5f,
          lastModifiedAt=2222,version=4,memo="{\"marker\":\"chapter\"}".toByteArray())),
        categories=listOf(7L),
        tracking=listOf(BackupTracking(syncId=5,libraryId=10,mediaId=321,trackingUrl="/track",title="Tracker",
          lastChapterRead=1.5f,totalChapters=30,score=7.5f,status=2)),
        favorite=true,chapterFlags=6,viewer_flags=3,
        history=listOf(BackupHistory("/ch-proj",777,88)),
        version=12,lastModifiedAt=4444,notes="Kotlin projected into SQLite",initialized=true,
        excludedScanlators=listOf("Bad Scan"),
        memo="{\"preserved\":\"yes\"}".toByteArray(),
    )
    val p=PolarisBackupMangaSqlProjection.prepare(archive, UUID, 103, mapOf(7L to 71L))
    val parent=p.parent.run { mapOf(
        "reservedParentId" to reservedParentId, "source" to source, "destinationUrl" to destinationUrl,
        "artist" to artist, "author" to author, "description" to description,
        "genre" to genre, "title" to title, "status" to status,
        "thumbnailUrl" to thumbnailUrl, "favorite" to favorite,
        "lastUpdate" to lastUpdate, "nextUpdate" to nextUpdate,
        "initialized" to initialized, "viewer" to viewer,
        "chapterFlags" to chapterFlags, "coverLastModified" to coverLastModified,
        "dateAdded" to dateAdded, "updateStrategy" to updateStrategy,
        "calculateInterval" to calculateInterval, "lastModifiedAt" to lastModifiedAt,
        "favoriteModifiedAt" to favoriteModifiedAt, "version" to version,
        "isSyncing" to isSyncing, "notes" to notes, "memo" to memo,
    ) }
    val chapters=p.chapters.map { c -> mapOf(
        "parentId" to c.parentId, "chapterUrl" to c.url,"chapterName" to c.name,"scanlator" to c.scanlator,
        "read" to c.read,"bookmark" to c.bookmark,"lastPageRead" to c.lastPageRead,
        "chapterNumber" to c.chapterNumber,"sourceOrder" to c.sourceOrder,
        "dateFetch" to c.dateFetch,"dateUpload" to c.dateUpload,
        "chapterLastModifiedAt" to c.lastModifiedAt,"chapterVersion" to c.version,
        "chapterIsSyncing" to c.isSyncing,"chapterMemo" to c.memo,
    ) }
    val history=p.history.map { h -> mapOf("chapterUrl" to h.chapterUrl,
        "lastRead" to h.lastRead,"readDuration" to h.readDuration) }
    val tracking=p.tracking.map { t -> mapOf(
        "syncId" to t.syncId,"remoteId" to t.remoteId,"libraryId" to t.libraryId,
        "trackTitle" to t.title,"lastChapterRead" to t.lastChapterRead,
        "totalChapters" to t.totalChapters,"trackStatus" to t.status,
        "trackScore" to t.score,"remoteUrl" to t.remoteUrl,
        "startDate" to t.startDate,"finishDate" to t.finishDate,"isPrivate" to t.private,
    ) }
    val data=mapOf(
        "uuid" to UUID, "digest" to "d".repeat(64), "parent" to parent,
        "chapters" to chapters,"history" to history,"tracking" to tracking,
        "categories" to p.categories,"exclusions" to p.excludedScanlators,
        "edges" to listOf(
           mapOf("source" to 77,"url" to "/real/101","manga_id" to 101,
                 "priority" to 0,"info" to true,"updates" to true),
           mapOf("source" to 6969,"url" to p.parent.destinationUrl,"manga_id" to null,
                 "priority" to 2147483647,"info" to false,"updates" to false),
        ),
    )
    println(json(data))
}
