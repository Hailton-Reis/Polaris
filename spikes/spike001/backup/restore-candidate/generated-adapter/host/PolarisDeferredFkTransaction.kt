package polaris.spike001.backup.restore

import app.cash.sqldelight.db.QueryResult
import app.cash.sqldelight.db.SqlDriver
import tachiyomi.data.Database

/**
 * R001 STAGING ONLY: same-connection guard for NEW virtual-parent, parent-LAST restore.
 *
 * Scoped to the pinned Mihon AndroidX SQLite SQLDelight driver at 0637a964a1.
 * That driver uses BEGIN IMMEDIATE, a coroutine TransactionElement and the
 * existing writer SQLiteConnection for all statements during a transaction.
 *
 * This is NOT the full metadata port, an Android-compiled integration or
 * permission to remove PolarisRestoreCoordinator's v2 preflight rejection.
 * SQLDelight codegen / actual driver Android smoke tests are mandatory.
 */
/** All operations are scoped to a NEW, not previously persisted, virtual parent. */
interface PolarisFreshParentStages<T> {
    /** Check a free ID on the physical mangas table, under the writer lock. */
    suspend fun reserveUnusedParentId(item: T): Long
    /** Write all dependent rows with the reserved ID; do not insert mangas yet. */
    suspend fun stageAllDependencies(item: T, reservedParentId: Long)
    /** INSERT exactly one full mangas row; no post-insert UPDATE. */
    suspend fun insertFullParentLast(item: T, reservedParentId: Long)
    /** Compare physical manga + all child relations + ledger; throw on mismatch. */
    suspend fun assertExactStoredParent(item: T, reservedParentId: Long)
}

class PolarisDeferredFkTransaction(
    private val database: Database,
    private val driver: SqlDriver,
) {
    /**
     * Strictly ordered NEW-only write path. Callers supply lossless field
     * mapping, source identity checks and physical readback in [stages].
     * Existing parents/empty placeholders must use another reviewed adapter.
     */
    suspend fun <T> restoreFreshParents(
        items: List<T>,
        stages: PolarisFreshParentStages<T>,
    ): List<Long> {
        require(items.isNotEmpty()) { "POLARIS_V2_EMPTY_FRESH_PARENT_BATCH" }
        return restoreNewParents {
            val ids = mutableListOf<Long>()
            for (item in items) {
                val id = stages.reserveUnusedParentId(item)
                check(id > 0L && id !in ids) { "POLARIS_V2_RESERVED_PARENT_ID_COLLISION" }
                stages.stageAllDependencies(item, id)
                stages.insertFullParentLast(item, id)
                stages.assertExactStoredParent(item, id)
                ids += id
            }
            ids
        }
    }

    /**
     * Calls [stageAndVerify] INSIDE the same transaction as the PRAGMAs.
     * [stageAndVerify] MUST only stage NEW parents: children/categories/history/
     * links/ledger BEFORE inserting a reserved parent row LAST, then compare
     * all archived fields and bindings. Do not call stock MangaRestorer here.
     * Any exception (including COMMIT FK violation) must roll back.
     *
     * Never catch database errors and return success from this block.
     */
    internal suspend fun <T> restoreNewParents(stageAndVerify: suspend () -> T): T =
        database.transactionWithResult {
            check(readSinglePragma("PRAGMA foreign_keys;") == 1L) {
                "POLARIS_V2_FOREIGN_KEYS_DISABLED"
            }
            // This MUST run after the driver has started BEGIN IMMEDIATE and
            // before inserting any referencing rows, on the writer connection.
            driver.execute(null, "PRAGMA defer_foreign_keys = ON;", 0, null).await()
            check(readSinglePragma("PRAGMA defer_foreign_keys;") == 1L) {
                "POLARIS_V2_FK_DEFER_NOT_ACTIVE"
            }
            val result = stageAndVerify()
            // Both PRAGMAs are connection-scoped. Rechecking catches accidental
            // loss of the writer context before commit.
            check(readSinglePragma("PRAGMA foreign_keys;") == 1L &&
                  readSinglePragma("PRAGMA defer_foreign_keys;") == 1L) {
                "POLARIS_V2_FK_TRANSACTION_CONTEXT_LOST"
            }
            val hasViolation = driver.executeQuery(
                identifier = null,
                sql = "PRAGMA foreign_key_check;",
                mapper = { cursor -> QueryResult.AsyncValue { cursor.next().await() } },
                parameters = 0,
                binders = null,
            ).await()
            check(!hasViolation) { "POLARIS_V2_FK_READBACK_VIOLATION" }
            result
            // SQLDelight commits on return and rolls back on throw. SQLite
            // automatically resets defer_foreign_keys on commit / rollback.
        }

    private suspend fun readSinglePragma(sql: String): Long =
        driver.executeQuery(
            identifier = null,
            sql = sql,
            mapper = { cursor -> QueryResult.AsyncValue {
                if (cursor.next().await()) cursor.getLong(0)
                else null
            } },
            parameters = 0,
            binders = null,
        ).await() ?: error("POLARIS_V2_FK_PRAGMA_UNAVAILABLE")
}
