package polaris.spike001.host

import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import tachiyomi.domain.chapter.interactor.GetMergedChaptersByMangaId
import tachiyomi.domain.manga.interactor.CreateMergedManga
import tachiyomi.domain.manga.interactor.DeleteMergedManga
import tachiyomi.domain.manga.model.Manga
import tachiyomi.domain.manga.repository.MangaRepository
import tachiyomi.domain.chapter.model.Chapter
import tachiyomi.domain.chapter.repository.ChapterRepository
import tachiyomi.domain.manga.model.MergedMangaReference
import tachiyomi.domain.manga.repository.MangaMergeRepository
import tachiyomi.domain.source.model.MERGED_SOURCE_ID
import tachiyomi.domain.manga.refresh.MergedRefreshTargets
import tachiyomi.domain.manga.refresh.MergedRefreshCoordinator

private const val PARENT = 99L
private const val A = 11L
private const val B = 22L
private const val SOURCE_A = 7001L
private const val SOURCE_B = 7002L
private fun ref(id: Long, manga: Long?, source: Long, mode: Int = MergedMangaReference.CHAPTER_SORT_NO_DEDUPE, priority: Int = 0) = MergedMangaReference(
  id, false, true, mode, priority, false, PARENT, "merged://test", manga, "manga/${manga ?: -1}", source
)
private fun refs(mode: Int = MergedMangaReference.CHAPTER_SORT_NO_DEDUPE) = listOf(
  ref(1,A,SOURCE_A,priority=0), ref(2,B,SOURCE_B,priority=1), ref(3,PARENT,MERGED_SOURCE_ID, mode)
)
private fun ch(id: Long, manga: Long, number: Double) = Chapter(id,manga,number)

private class Repository(initial: List<MergedMangaReference> = refs()) : MangaMergeRepository {
  val flow = MutableStateFlow(initial)
  private var nextReference = 500L
  var failNextInsert = false
  override suspend fun insertAll(references: List<MergedMangaReference>) {
    if (failNextInsert) {
      failNextInsert = false
      error("Injected reference transaction failure")
    }
    flow.value = flow.value + references.map { ref -> ref.copy(id = nextReference++) }
  }
  override suspend fun deleteById(id: Long) { flow.value = flow.value.filterNot { it.id == id } }
  override suspend fun deleteByMergeId(mergeId: Long) { flow.value = flow.value.filterNot { it.mergeId == mergeId } }
  override suspend fun getReferencesById(id: Long): List<MergedMangaReference> { check(id == PARENT); return flow.value }
  override fun subscribeReferencesById(id: Long): Flow<List<MergedMangaReference>> { check(id == PARENT); return flow }
}
private class MangaStore : MangaRepository {
  private val rows = mutableMapOf(
    A to Manga(A, SOURCE_A, "source-a/title", "Work"),
    B to Manga(B, SOURCE_B, "source-b/title", "Work"),
  )
  override suspend fun getMangaById(id: Long): Manga = requireNotNull(rows[id])
  override suspend fun getMangaByUrlAndSourceId(url: String, source: Long) = rows.values.firstOrNull { it.url == url && it.source == source }
  var insertedParents = 0
  fun add(manga: Manga) { check(rows.putIfAbsent(manga.id, manga) == null) }
  override suspend fun insertNetworkManga(mangas: List<Manga>): List<Manga> = mangas.map { manga ->
    insertedParents++
    val saved = manga.copy(id = PARENT)
    check(rows.putIfAbsent(saved.id, saved) == null)
    saved
  }
}
private class Chapters : ChapterRepository {
  val data = mapOf(A to MutableStateFlow(listOf(ch(101,A,1.0),ch(102,A,2.0))),
                   B to MutableStateFlow(listOf(ch(201,B,1.0),ch(202,B,3.0))))
  override suspend fun getChapterByMangaId(id: Long, applyScanlatorFilter: Boolean) = requireNotNull(data[id]).value
  override suspend fun getChapterByMangaIdAsFlow(id: Long, applyScanlatorFilter: Boolean) = requireNotNull(data[id])
}

fun main() = runBlocking {
  var passes = 0
  suspend fun test(name: String, body: suspend () -> Unit) { body(); passes++; println("PASS $name") }
  val repo = Repository()
  val chapters = Chapters()
  val merged = GetMergedChaptersByMangaId(chapters, repo)
  test("B01-like: source-specific chapters preserved in combined list") {
    val all = merged.await(PARENT)
    check(all.map { it.id } == listOf(101L,102L,201L,202L))
    check(all.map { it.mangaId }.toSet() == setOf(A,B))
    check(all.none { it.mangaId == PARENT })
  }
  test("B02 identity contract: chapter pairs resolve real children") {
    check(merged.await(PARENT).map { it.mangaId to it.id } ==
      listOf(A to 101L,A to 102L,B to 201L,B to 202L))
  }
  test("priority dedupe keeps real winning source") {
    repo.flow.value = refs(MergedMangaReference.CHAPTER_SORT_PRIORITY)
    val result = merged.await(PARENT)
    check(result.map { it.id } == listOf(101L,102L,202L))
    check(result.map { it.sourceOrder } == listOf(0L,1L,2L))
  }
  test("highest-chapter variant mode") {
    repo.flow.value = refs(MergedMangaReference.CHAPTER_SORT_HIGHEST_CHAPTER_NUMBER)
    check(merged.await(PARENT).all { it.mangaId == B })
  }
  test("source removal preserves parent and remaining real chapters") {
    repo.flow.value = refs().filterNot { it.mangaId == A }
    check(merged.await(PARENT).map { it.id } == listOf(201L,202L))
    check(repo.flow.value.any { it.mangaSourceId == MERGED_SOURCE_ID })
  }
  test("orphan/null source reference does not crash") {
    repo.flow.value = listOf(ref(1,null,SOURCE_A),ref(2,B,SOURCE_B),ref(3,PARENT,MERGED_SOURCE_ID))
    check(merged.await(PARENT).map { it.id } == listOf(201L,202L))
  }
  test("subscription reflects source removal") {
    repo.flow.value = refs()
    val initial = withTimeout(3_000) { merged.subscribe(PARENT).first { it.size == 4 } }
    check(initial.map { it.mangaId }.toSet() == setOf(A,B))
    val subsequent = async { withTimeout(3_000) { merged.subscribe(PARENT).first { it.size == 2 && it.all { c -> c.mangaId == B } } } }
    yield()
    repo.flow.value = refs().filterNot { it.mangaId == A }
    check(subsequent.await().map { it.mangaId }.toSet() == setOf(B))
  }
  test("empty remaining references emits empty list") {
    repo.flow.value = refs().filter { it.mangaSourceId == MERGED_SOURCE_ID }
    check(merged.await(PARENT).isEmpty())
    check(withTimeout(3_000) { merged.subscribe(PARENT).first() }.isEmpty())
  }
  test("priority opt-out returns all source chapters without dedupe") {
    repo.flow.value = refs(MergedMangaReference.CHAPTER_SORT_PRIORITY)
    check(merged.await(PARENT, dedupe = false).map { it.id } == listOf(101L,102L,201L,202L))
  }
  test("none sort mode preserves both source chapter groups") {
    repo.flow.value = refs(MergedMangaReference.CHAPTER_SORT_NONE)
    check(merged.await(PARENT).map { it.id } == listOf(101L,102L,201L,202L))
  }
  test("live child refresh updates virtual chapter list without parent copies") {
    repo.flow.value = refs()
    val updated = async {
      withTimeout(3_000) { merged.subscribe(PARENT).first { it.size == 5 && it.any { ch -> ch.id == 203L } } }
    }
    yield()
    chapters.data.getValue(B).value = listOf(ch(201,B,1.0),ch(202,B,3.0),ch(203,B,4.0))
    val list = updated.await()
    check(list.map { it.id } == listOf(101L,102L,201L,202L,203L))
    check(list.none { it.mangaId == PARENT })
  }
  test("most chapters mode selects source with larger real coverage") {
    repo.flow.value = refs(MergedMangaReference.CHAPTER_SORT_MOST_CHAPTERS)
    val winner = merged.await(PARENT)
    check(winner.map { it.id } == listOf(201L,202L,203L))
    check(winner.all { it.mangaId == B })
  }
  test("merged refresh enumerates both real child mangas") {
    check(MergedRefreshTargets.childMangaIds(PARENT, refs()) == listOf(A, B))
  }
  test("merged refresh ignores removed or orphan child") {
    val orphan = listOf(ref(1, null, SOURCE_A), ref(2, B, SOURCE_B), ref(3, PARENT, MERGED_SOURCE_ID))
    check(MergedRefreshTargets.childMangaIds(PARENT, orphan) == listOf(B))
  }
  test("merged refresh excludes parent and cross-work references") {
    val extras = refs() + ref(5, 100, SOURCE_A).copy(mergeId = 500) + ref(6, PARENT, SOURCE_A)
    check(MergedRefreshTargets.childMangaIds(PARENT, extras) == listOf(A,B))
  }
  test("merged refresh deduplicates repeated references without reordering") {
    check(MergedRefreshTargets.childMangaIds(PARENT, refs() + ref(5,A,SOURCE_A)) == listOf(A,B))
  }
  test("refresh coordinator calls each real source once") {
    val visited = mutableListOf<Long>()
    val result = MergedRefreshCoordinator.refresh(PARENT, refs(), { visited += it })
    check(visited == listOf(A,B) && result.failedChildIds.isEmpty())
  }
  test("refresh coordinator succeeds despite first source error") {
    val visited = mutableListOf<Long>(); val errors = mutableListOf<Long>()
    val result = MergedRefreshCoordinator.refresh(
      PARENT, refs(), { visited += it; if (it == A) error("temporarily offline") },
      { id, _ -> errors += id },
    )
    check(visited == listOf(A,B) && errors == listOf(A))
    check(result.succeededChildIds == listOf(B) && result.failedChildIds == listOf(A))
  }
  test("refresh coordinator fails after both source errors") {
    val visited = mutableListOf<Long>(); var message = ""
    try {
      MergedRefreshCoordinator.refresh(PARENT, refs(), { visited += it; error("offline:$it") })
    } catch (e: IllegalStateException) { message = e.message.orEmpty() }
    check(visited == listOf(A,B) && message == "offline:$B")
  }
  test("refresh coordinator cancellation never attempts next child") {
    val visited = mutableListOf<Long>(); var cancelled = false
    try {
      MergedRefreshCoordinator.refresh(PARENT, refs(), {
        visited += it
        throw CancellationException("cancel requested")
      })
    } catch (e: CancellationException) { cancelled = true }
    check(cancelled && visited == listOf(A))
  }
  test("refresh coordinator discards stale and unrelated references") {
    val extras = refs() + ref(20,null,SOURCE_A) +
      ref(21,33,SOURCE_B).copy(mergeId=700) + ref(22,PARENT,SOURCE_A)
    val result = MergedRefreshCoordinator.refresh(PARENT, extras, {})
    check(result.succeededChildIds == listOf(A,B))
  }
  test("refresh coordinator rejects a merge without actual children") {
    var called = false; var failed = false
    try {
      MergedRefreshCoordinator.refresh(PARENT, listOf(ref(3,PARENT,MERGED_SOURCE_ID)), { called = true })
    } catch (e: IllegalArgumentException) { failed = true }
    check(failed && !called)
  }
  test("real CreateMergedManga inserts virtual favorite and three refs") {
    val source = MangaStore()
    val refs = Repository(emptyList())
    val parent = CreateMergedManga(source, refs)(listOf(A,B))
    check(parent.id == PARENT && parent.source == MERGED_SOURCE_ID)
    check(parent.favorite && parent.initialized && parent.url == "merged://11-22")
    val rows = refs.getReferencesById(PARENT)
    check(rows.size == 3 && rows.map { it.mangaId }.toSet() == setOf(A,B,PARENT))
    check(rows.single { it.mangaId == PARENT }.mangaSourceId == MERGED_SOURCE_ID)
    check(rows.single { it.mangaId == A }.mangaSourceId == SOURCE_A)
    check(rows.single { it.mangaId == B }.mangaSourceId == SOURCE_B)
    check(source.getMangaById(A).source == SOURCE_A)
    check(source.getMangaById(B).source == SOURCE_B)
    check(GetMergedChaptersByMangaId(Chapters(), refs).await(PARENT).map { it.id } == listOf(101L,102L,202L))
  }
  test("repeated real CreateMergedManga is idempotent") {
    val source = MangaStore(); val refs = Repository(emptyList())
    val create = CreateMergedManga(source, refs)
    val first = create(listOf(A,B))
    val second = create(listOf(B,A), infoMangaId = B)
    check(first.id == second.id)
    check(refs.getReferencesById(PARENT).size == 3)
  }
  test("real DeleteMergedManga removes only requested child reference") {
    val source = MangaStore(); val refs = Repository(emptyList())
    val parent = CreateMergedManga(source, refs)(listOf(A,B))
    val before = refs.getReferencesById(parent.id)
    val aRef = before.single { it.mangaId == A }
    DeleteMergedManga(refs).deleteReference(aRef.id)
    val after = refs.getReferencesById(parent.id)
    check(after.map { it.mangaId }.toSet() == setOf(B,PARENT))
    check(source.getMangaById(PARENT).source == MERGED_SOURCE_ID)
    check(source.getMangaById(A).source == SOURCE_A)
    check(GetMergedChaptersByMangaId(Chapters(), refs).await(PARENT).all { it.mangaId == B })
    // Repeating create after a deliberate deletion must not resurrect Source A.
    val repeated = CreateMergedManga(source, refs)(listOf(A,B))
    check(repeated.id == PARENT)
    check(refs.getReferencesById(PARENT).map { it.mangaId }.toSet() == setOf(B,PARENT))
  }
  test("real CreateMergedManga rejects only one distinct variant") {
    val store = MangaStore(); val refs = Repository(emptyList()); var denied = false
    try { CreateMergedManga(store, refs)(listOf(A,A)) } catch (e: IllegalArgumentException) { denied = true }
    check(denied && refs.getReferencesById(PARENT).isEmpty())
  }
  test("orphan virtual parent is recovered after failed reference transaction") {
    val source = MangaStore()
    val refs = Repository(emptyList())
    refs.failNextInsert = true
    val create = CreateMergedManga(source, refs)
    var failed = false
    try { create(listOf(A,B)) } catch (e: IllegalStateException) {
      failed = e.message == "Injected reference transaction failure"
    }
    check(failed && source.insertedParents == 1)
    check(refs.getReferencesById(PARENT).isEmpty())
    val recovered = create(listOf(A,B))
    check(recovered.id == PARENT && source.insertedParents == 1)
    check(refs.getReferencesById(PARENT).map { it.mangaId }.toSet() == setOf(A,B,PARENT))
  }
  test("recovery remains idempotent after interrupted first insert") {
    val source = MangaStore(); val refs = Repository(emptyList())
    val create = CreateMergedManga(source, refs)
    refs.failNextInsert = true
    try { create(listOf(A,B)) } catch (_: IllegalStateException) {}
    create(listOf(A,B))
    val count = refs.getReferencesById(PARENT).size
    create(listOf(B,A), infoMangaId = B)
    check(count == 3 && refs.getReferencesById(PARENT).size == count && source.insertedParents == 1)
  }
  test("production create rejects nested merged work before side effects") {
    val store = MangaStore(); val refs = Repository(emptyList())
    val create = CreateMergedManga(store, refs)
    val parent = create(listOf(A, B))
    check(store.insertedParents == 1)
    val originalCount = refs.getReferencesById(PARENT).size
    var rejected = false
    try { create(listOf(parent.id, A)) }
    catch (error: IllegalArgumentException) { rejected = error.message == "Nested merged works are not supported" }
    check(rejected && store.insertedParents == 1)
    check(refs.getReferencesById(PARENT).size == originalCount)
  }
  test("production create rejects same-source variants before any writes") {
    val store = MangaStore(); val refs = Repository(emptyList())
    store.add(Manga(33L, SOURCE_A, "source-a/alternate", "Other variant"))
    var rejected = false
    try { CreateMergedManga(store, refs)(listOf(A, 33L)) }
    catch (error: IllegalArgumentException) { rejected = error.message == "Merge requires variants from two real sources" }
    check(rejected && store.insertedParents == 0)
    check(refs.getReferencesById(PARENT).isEmpty())
  }
  test("empty merged candidate set fails with actionable argument error") {
    val store = MangaStore(); val refs = Repository(emptyList())
    var message = ""
    try { CreateMergedManga(store, refs)(emptyList()) }
    catch (e: IllegalArgumentException) { message = e.message.orEmpty() }
    check(message == "A merged manga requires at least two source variants")
    check(store.insertedParents == 0 && refs.getReferencesById(PARENT).isEmpty())
  }
  test("invalid negative child identity is rejected before repository access") {
    val store = MangaStore(); val refs = Repository(emptyList())
    var rejected = false
    try { CreateMergedManga(store, refs)(listOf(A,-42L)) }
    catch (e: IllegalArgumentException) { rejected = e.message == "Merged variants require persisted positive manga IDs" }
    check(rejected && store.insertedParents == 0)
  }
  test("priority dedupe preserves repeated chapter numbers within one source") {
    val refs = Repository(refs(MergedMangaReference.CHAPTER_SORT_PRIORITY))
    val childChapters = Chapters()
    childChapters.data.getValue(A).value = listOf(ch(101,A,1.0),ch(102,A,1.0),ch(103,A,-1.0))
    childChapters.data.getValue(B).value = listOf(ch(201,B,1.0),ch(202,B,2.0),ch(203,B,-1.0))
    val got = GetMergedChaptersByMangaId(childChapters, refs).await(PARENT)
    check(got.map { it.id } == listOf(101L,102L,103L,202L,203L))
    check(got.map { it.sourceOrder } == (0L..4L).toList())
  }
  test("priority dedupe treats positive and negative zero as the same chapter") {
    val refs = Repository(refs(MergedMangaReference.CHAPTER_SORT_PRIORITY))
    val childChapters = Chapters()
    childChapters.data.getValue(A).value = listOf(ch(101,A,-0.0))
    childChapters.data.getValue(B).value = listOf(ch(201,B,0.0),ch(202,B,2.0))
    check(GetMergedChaptersByMangaId(childChapters, refs).await(PARENT).map { it.id } == listOf(101L,202L))
  }
  println("SPIKE001_HOST_INVARIANTS_PASS ($passes scenarios); NOT_ANDROID_RUNTIME")
}
