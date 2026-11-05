package polaris.spike001.backup.restore

import app.cash.sqldelight.db.*

class TestDriver : SqlDriver {
    var foreignKeys = 1L
    var deferred = 0L
    var transactionActive = false
    var commitCount = 0
    var rollbackCount = 0
    var beginCount = 0
    var statements = mutableListOf<String>()
    var rows = mutableListOf<String>()
    var violations = false
    var emptyPragma: String? = null
    var rejectPragma = false
    var switchConnectionMidway = false
    var commitError = false
    fun begin() {
        check(!transactionActive) { "nested transaction not supported in host" }
        beginCount++; transactionActive = true
        statements.add("BEGIN IMMEDIATE")
    }
    fun commit() {
        check(transactionActive)
        statements.add("COMMIT")
        if(commitError || violations) error("SQLite commit FK violation")
        commitCount++; transactionActive = false; deferred = 0
    }
    fun rollback() {
        rollbackCount++; rows.clear(); statements.add("ROLLBACK")
        transactionActive = false; deferred = 0
    }
    override fun execute(identifier: Int?, sql: String, parameters: Int, binders: Any?): QueryResult<Long> =
        QueryResult.AsyncValue {
            check(transactionActive)
            statements.add(sql)
            if(rejectPragma) error("PRAGMA rejected by backend")
            check(sql == "PRAGMA defer_foreign_keys = ON;")
            deferred = 1; 0L
        }
    override fun <R> executeQuery(identifier: Int?, sql: String,
                                  mapper: (SqlCursor) -> QueryResult<R>, parameters: Int,
                                  binders: Any?): QueryResult<R> = QueryResult.AsyncValue {
        check(transactionActive)
        statements.add(sql)
        if(switchConnectionMidway && sql == "PRAGMA defer_foreign_keys;" &&
           statements.count { it == sql } > 1) deferred = 0
        val values: List<Long?> = when(sql) {
            "PRAGMA foreign_keys;" -> if(emptyPragma == sql) emptyList() else listOf(foreignKeys)
            "PRAGMA defer_foreign_keys;" -> if(emptyPragma == sql) emptyList() else listOf(deferred)
            "PRAGMA foreign_key_check;" -> if(violations) listOf(1) else emptyList()
            else -> error("unexpected sql")
        }
        val cursor = object : SqlCursor {
            var index = -1
            override fun next() = QueryResult.AsyncValue { index++; index < values.size }
            override fun getLong(index: Int) = values[this.index]
        }
        mapper(cursor).await()
    }
    fun write(s: String) { check(transactionActive); rows.add(s); statements.add("WRITE:" + s) }
}
