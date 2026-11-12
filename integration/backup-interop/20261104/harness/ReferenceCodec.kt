import eu.kanade.tachiyomi.data.backup.models.*
import eu.kanade.tachiyomi.source.model.UpdateStrategy
import kotlinx.serialization.protobuf.ProtoBuf
import java.io.File
import java.util.zip.GZIPOutputStream
import java.util.zip.GZIPInputStream

private val codec = ProtoBuf { encodeDefaults = false }
fun sample(): Backup {
 val chapter=BackupChapter("/work/ch-40", "Chapter 40", "Synthetic", true, true, 17, 1700000000100, 1700000000200, 40f, 3)
 val manga=BackupManga(8787213233662904706L,"/work","Obra de teste — ação").apply {
  artist="Artista";author="Autor";description="Somente dados sintéticos";genre=listOf("Aventura");status=2
  dateAdded=1700000000000;favorite=true;chapterFlags=13;viewer_flags=5
  chapters=listOf(chapter);categories=listOf(7);history=listOf(BackupHistory(chapter.url,1700000000300,12345))
  tracking=listOf(BackupTracking(1,123,trackingUrl="https://example.invalid/track/456",title="Tracking",lastChapterRead=39.5f,totalChapters=100,score=8.5f,status=1,mediaId=456))
  updateStrategy=UpdateStrategy.ONLY_FETCH_ONCE;favoriteModifiedAt=1700000000
 }
 return Backup(listOf(manga),backupCategories=listOf(sampleCategory()),backupSources=listOf(BackupSource("Fonte ausente",manga.source)),
  backupPreferences=listOf(BackupPreference("sample.int",IntPreferenceValue(42)),BackupPreference("sample.long",LongPreferenceValue(5000000000)),BackupPreference("sample.float",FloatPreferenceValue(1.25f)),BackupPreference("sample.bool",BooleanPreferenceValue(true)),BackupPreference("sample.string",StringPreferenceValue("ação")),BackupPreference("sample.set",StringSetPreferenceValue(setOf("pt","en")))),
  backupSourcePreferences=listOf(BackupSourcePreferences("source-${manga.source}",listOf(BackupPreference("sample.option",StringPreferenceValue("synthetic"))))))
}
fun main(args:Array<String>) {
 val expected=sample()
 if(args[0]=="generate") {
  customize(expected)
  val bytes=codec.encodeToByteArray(Backup.serializer(),expected)
  File(args[1]+".proto").writeBytes(bytes)
  GZIPOutputStream(File(args[1]+".tachibk").outputStream()).use{it.write(bytes)}
  println("REFERENCE_GENERATED ${bytes.size}")
 } else {
  val file=File(args[1]);val bytes=if(file.extension=="tachibk")GZIPInputStream(file.inputStream()).use{it.readBytes()}else file.readBytes()
  val restored=codec.decodeFromByteArray(Backup.serializer(),bytes)
  verifyExtras(restored)
  val semantic = kotlinx.serialization.json.Json { encodeDefaults = true }
  val equal = semantic.encodeToJsonElement(Backup.serializer(),expected) == semantic.encodeToJsonElement(Backup.serializer(),restored)
  if(!equal) {
   File(args[1]+".expected.json").writeText(kotlinx.serialization.json.Json.encodeToString(Backup.serializer(),expected))
   File(args[1]+".actual.json").writeText(kotlinx.serialization.json.Json.encodeToString(Backup.serializer(),restored))
  }
  check(equal) { "Common/reference fields changed on Polaris export" }
  println("REFERENCE_IMPORT_OF_POLARIS_EXPORT_PASS")
 }
}
