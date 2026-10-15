package polaris.spike001.backup.uuid

import java.util.UUID
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import tachiyomi.domain.manga.model.MangaUpdate
import tachiyomi.domain.manga.repository.MangaRepository

/**
 * Pinned-Yomotsu adapter candidate: save a durable virtual parent identity in
 * the existing mangas.memo JSON column, without schema migration 15.
 *
 * The pinned MangaRepository.update(MangaUpdate(id, memo)) returns Boolean and
 * getMangaById rereads the persisted row. There is NO compare-and-swap here;
 * a concurrent conflicting writer makes the readback fail closed, but an
 * external process can still race after this method returns.
 */
class YomotsuMergedWorkUuidStore(
    private val mangaRepository: MangaRepository,
    private val generate: () -> UUID = { UUID.randomUUID() },
) {
    companion object {
        const val MEMO_KEY = "polaris.merge.work.uuid"
        const val VIRTUAL_SOURCE_ID = 6969L
    }

    suspend fun ensure(parentId: Long): String {
        require(parentId > 0) { "Virtual manga must have a persisted positive local ID" }
        val parent = mangaRepository.getMangaById(parentId)
        require(parent.source == VIRTUAL_SOURCE_ID) { "Cannot attach Polaris UUID to real source manga" }
        readUuid(parent.memo)?.let { return it }

        val newUuid = generate().toString()
        val amended = JsonObject(parent.memo + (MEMO_KEY to JsonPrimitive(newUuid)))
        check(mangaRepository.update(MangaUpdate(id = parentId, memo = amended))) {
            "Virtual UUID was not committed: refusing incomplete backup"
        }
        val persisted = mangaRepository.getMangaById(parentId)
        check(persisted.source == VIRTUAL_SOURCE_ID) { "Virtual parent type changed during backup" }
        check(readUuid(persisted.memo) == newUuid) {
            "UUID changed or disappeared during write; abort backup and retry from a fresh read"
        }
        return newUuid
    }

    /**
     * Restore the SAME durable identity from another device. Do not regenerate
     * a new archive key or replace a different identity already persisted here.
     * Caller still owns parent creation, uniqueness checks and DB transactions.
     */
    suspend fun assignArchived(parentId: Long, archivedUuid: String): String {
        require(parentId > 0) { "Virtual manga must have a persisted positive local ID" }
        val parsed = runCatching { UUID.fromString(archivedUuid) }.getOrNull()
        require(parsed != null && parsed.toString() == archivedUuid) {
            "Invalid or noncanonical UUID in incoming Polaris backup"
        }
        val parent = mangaRepository.getMangaById(parentId)
        require(parent.source == VIRTUAL_SOURCE_ID) { "Cannot assign virtual identity to real manga" }
        val existing = readUuid(parent.memo)
        require(existing == null || existing == archivedUuid) {
            "Conflicting UUID already belongs to this virtual parent; refusing destructive restore"
        }
        if (existing != null) return existing

        val amended = JsonObject(parent.memo + (MEMO_KEY to JsonPrimitive(archivedUuid)))
        check(mangaRepository.update(MangaUpdate(id = parentId, memo = amended))) {
            "Imported work identity could not be persisted"
        }
        val persisted = mangaRepository.getMangaById(parentId)
        check(persisted.source == VIRTUAL_SOURCE_ID && readUuid(persisted.memo) == archivedUuid) {
            "Imported UUID changed or disappeared during write; abort parent relinking"
        }
        return archivedUuid
    }

    /** Reject collisions across favorite virtual parents before generating archive keys. */
    suspend fun ensureDistinct(parentIds: List<Long>): Map<Long, String> {
        require(parentIds.size == parentIds.distinct().size) { "Same virtual parent listed twice" }
        val resolved = linkedMapOf<Long, String>()
        for (id in parentIds) {
            resolved[id] = ensure(id)
        }
        require(resolved.values.distinct().size == resolved.size) {
            "Two merged works share one UUID; refusing to conflate separate virtual parents"
        }
        return resolved
    }

    private fun readUuid(memo: JsonObject): String? {
        val element = memo[MEMO_KEY] ?: return null
        val primitive = element as? JsonPrimitive
        require(primitive != null && primitive.isString) {
            "Polaris virtual UUID memo has an invalid JSON type"
        }
        val candidate = primitive.content
        val parsed = runCatching { UUID.fromString(candidate) }.getOrNull()
        require(parsed != null && parsed.toString() == candidate) {
            "Invalid/noncanonical Polaris virtual UUID; refusing to replace silently"
        }
        return candidate
    }
}
