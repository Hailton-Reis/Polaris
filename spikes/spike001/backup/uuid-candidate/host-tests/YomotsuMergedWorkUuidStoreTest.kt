package polaris.spike001.backup.uuid

import java.util.UUID
import kotlin.coroutines.*
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import tachiyomi.domain.manga.model.Manga
import tachiyomi.domain.manga.model.MangaUpdate
import tachiyomi.domain.manga.repository.MangaRepository

private const val KEY = YomotsuMergedWorkUuidStore.MEMO_KEY
private const val A = "123e4567-e89b-42d3-a456-426614174000"
private const val B = "123e4567-e89b-42d3-a456-426614174001"
private var assertions = 0
private fun case(name: String, f: () -> Unit) { f(); assertions++; println("MERGE_UUID_PASS $assertions $name") }
private fun rejected(f: () -> Unit) { check(runCatching(f).isFailure) }
private fun <T> block(f: suspend () -> T): T {
    var result: Result<T>? = null
    f.startCoroutine(object : Continuation<T> {
        override val context: CoroutineContext = EmptyCoroutineContext
        override fun resumeWith(outcome: Result<T>) { result = outcome }
    })
    return checkNotNull(result).getOrThrow()
}
private class MemoryRepo(vararg mangas: Manga) : MangaRepository {
    val rows = mangas.associateBy { it.id }.toMutableMap()
    var shouldUpdate = true
    var writes = 0
    var overrideReadAfterWrite: Manga? = null
    override suspend fun getMangaById(id: Long): Manga {
        if (writes > 0 && overrideReadAfterWrite != null) return overrideReadAfterWrite!!
        return rows.getValue(id)
    }
    override suspend fun update(update: MangaUpdate): Boolean {
        writes++
        if (!shouldUpdate) return false
        rows[update.id] = rows.getValue(update.id).copy(memo = checkNotNull(update.memo))
        return true
    }
}
private fun virtual(id: Long, memo: JsonObject = JsonObject()) = Manga(id, 6969L, memo)
private fun factory(id: String) = { UUID.fromString(id) }

fun main() {
    case("Generates UUID and persists in existing memo column") {
        val repo = MemoryRepo(virtual(1))
        check(block { YomotsuMergedWorkUuidStore(repo, factory(A)).ensure(1) } == A)
        check((repo.rows.getValue(1).memo[KEY] as JsonPrimitive).content == A && repo.writes == 1)
    }
    case("Repeated backup reuses UUID without a second database write") {
        val repo=MemoryRepo(virtual(1)); val store=YomotsuMergedWorkUuidStore(repo,factory(A))
        check(block { store.ensure(1) } == block { store.ensure(1) } && repo.writes==1)
    }
    case("Existing portable UUID remains stable, no overwrite") {
        val repo=MemoryRepo(virtual(1,JsonObject(mapOf(KEY to JsonPrimitive(B)))))
        check(block { YomotsuMergedWorkUuidStore(repo,factory(A)).ensure(1) }==B && repo.writes==0)
    }
    case("Other user's memo metadata is preserved verbatim") {
        val memo=JsonObject(mapOf("user.memo" to JsonPrimitive("keep")))
        val repo=MemoryRepo(virtual(1,memo))
        block { YomotsuMergedWorkUuidStore(repo,factory(A)).ensure(1) }
        check((repo.rows.getValue(1).memo["user.memo"] as JsonPrimitive).content == "keep")
    }
    case("Real manga source must never get merged-work UUID") {
        val repo=MemoryRepo(Manga(1,1001L))
        rejected { block { YomotsuMergedWorkUuidStore(repo,factory(A)).ensure(1) } }
        check(repo.writes == 0)
    }
    case("Nonpositive virtual local ID rejected") {
        val repo=MemoryRepo(virtual(1))
        rejected { block { YomotsuMergedWorkUuidStore(repo,factory(A)).ensure(-1) } }
        check(repo.writes==0)
    }
    case("Malformed string UUID cannot be overwritten silently") {
        val repo=MemoryRepo(virtual(1,JsonObject(mapOf(KEY to JsonPrimitive("bad-uuid")))))
        rejected { block { YomotsuMergedWorkUuidStore(repo,factory(A)).ensure(1) } }
        check(repo.writes==0)
    }
    case("JSON nonstring UUID cannot be overwritten") {
        val repo=MemoryRepo(virtual(1,JsonObject(mapOf(KEY to JsonPrimitive("42",false)))))
        rejected { block { YomotsuMergedWorkUuidStore(repo,factory(A)).ensure(1) } }
        check(repo.writes==0)
    }
    case("Noncanonical uppercase UUID is rejected") {
        val repo=MemoryRepo(virtual(1,JsonObject(mapOf(KEY to JsonPrimitive(A.uppercase())))))
        rejected { block { YomotsuMergedWorkUuidStore(repo,factory(A)).ensure(1) } }
        check(repo.writes==0)
    }
    case("Repository refused update: fail closed") {
        val repo=MemoryRepo(virtual(1));repo.shouldUpdate=false
        rejected { block { YomotsuMergedWorkUuidStore(repo,factory(A)).ensure(1) } }
    }
    case("Readback diverges from generated UUID: abort export") {
        val repo=MemoryRepo(virtual(1));repo.overrideReadAfterWrite=virtual(1,JsonObject(mapOf(KEY to JsonPrimitive(B))))
        rejected { block { YomotsuMergedWorkUuidStore(repo,factory(A)).ensure(1) } }
    }
    case("Parent changed to real source during write: reject") {
        val repo=MemoryRepo(virtual(1));repo.overrideReadAfterWrite=Manga(1,1001L,JsonObject(mapOf(KEY to JsonPrimitive(A))))
        rejected { block { YomotsuMergedWorkUuidStore(repo,factory(A)).ensure(1) } }
    }
    case("Two distinct virtual manga sharing one legacy UUID cannot silently merge") {
        val memo=JsonObject(mapOf(KEY to JsonPrimitive(A)))
        val repo=MemoryRepo(virtual(1,memo),virtual(2,memo))
        rejected { block { YomotsuMergedWorkUuidStore(repo).ensureDistinct(listOf(1,2)) } }
    }
    case("One parent requested twice cannot be serialized twice") {
        val repo=MemoryRepo(virtual(1))
        rejected { block { YomotsuMergedWorkUuidStore(repo,factory(A)).ensureDistinct(listOf(1,1)) } }
        check(repo.writes==0)
    }
    case("Distinct persisted UUIDs build portable map for both parents") {
        val repo=MemoryRepo(virtual(1,JsonObject(mapOf(KEY to JsonPrimitive(A)))),virtual(2,JsonObject(mapOf(KEY to JsonPrimitive(B)))))
        check(block { YomotsuMergedWorkUuidStore(repo).ensureDistinct(listOf(1,2)) } == mapOf(1L to A,2L to B))
        check(repo.writes==0)
    }
    case("Imported UUID is persisted exactly on a newly restored parent") {
        val repo=MemoryRepo(virtual(1))
        check(block { YomotsuMergedWorkUuidStore(repo,factory(A)).assignArchived(1,B) } == B)
        check((repo.rows.getValue(1).memo[KEY] as JsonPrimitive).content == B)
    }
    case("Re-importing the same UUID does not make a second write") {
        val repo=MemoryRepo(virtual(1)); val store=YomotsuMergedWorkUuidStore(repo,factory(A))
        check(block { store.assignArchived(1,B) } == block { store.assignArchived(1,B) } && repo.writes==1)
    }
    case("Import cannot replace an existing conflicting work UUID") {
        val repo=MemoryRepo(virtual(1,JsonObject(mapOf(KEY to JsonPrimitive(A)))))
        rejected { block { YomotsuMergedWorkUuidStore(repo).assignArchived(1,B) } }
        check(repo.writes==0)
    }
    case("Malformed imported UUID is rejected before reading/writing manga") {
        val repo=MemoryRepo(virtual(1))
        rejected { block { YomotsuMergedWorkUuidStore(repo).assignArchived(1,"not-a-uuid") } }
        check(repo.writes==0)
    }
    case("Imported UUID cannot be attached to a real source manga") {
        val repo=MemoryRepo(Manga(1,1001L))
        rejected { block { YomotsuMergedWorkUuidStore(repo).assignArchived(1,A) } }
        check(repo.writes==0)
    }
    case("Imported UUID readback disagreement stops relinking") {
        val repo=MemoryRepo(virtual(1)); repo.overrideReadAfterWrite=virtual(1,JsonObject(mapOf(KEY to JsonPrimitive(A))))
        rejected { block { YomotsuMergedWorkUuidStore(repo).assignArchived(1,B) } }
    }
    println("POLARIS_PERSISTED_MERGE_UUID_PASS $assertions")
}
