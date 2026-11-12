package polaris.spike001.backup.restore

import app.cash.sqldelight.db.QueryResult
import app.cash.sqldelight.db.SqlCursor
import app.cash.sqldelight.db.SqlDriver
import tachiyomi.data.Database
import kotlin.coroutines.Continuation
import kotlin.coroutines.CoroutineContext
import kotlin.coroutines.EmptyCoroutineContext
import kotlin.coroutines.startCoroutine

private var passed = 0
private fun ok(label: String, block: () -> Unit) { block(); passed++; println("PASS $passed $label") }
private fun reject(label: String, block: () -> Unit) = ok(label) {
    check(runCatching(block).isFailure) { "Expected fail-closed: $label" }
}
private fun <T> runSync(block: suspend () -> T): T {
    var finished: Result<T>? = null
    block.startCoroutine(object : Continuation<T> {
        override val context: CoroutineContext = EmptyCoroutineContext
        override fun resumeWith(result: Result<T>) { finished = result }
    })
    return checkNotNull(finished).getOrThrow()
}

/** Only a host double. No Android / real SQLDelight classes execute here. */
class FakePinnedDriver : SqlDriver {
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
private fun port(d: FakePinnedDriver = FakePinnedDriver()) = PolarisDeferredFkTransaction(Database(d), d)

fun main() {
    ok("two writer scoped pragmas are checked before callback") {
        val d=FakePinnedDriver();runSync { port(d).restoreNewParents {
            check(d.transactionActive && d.deferred==1L)
            check(d.statements.first()=="BEGIN IMMEDIATE")
            check(d.statements.take(4)==listOf("BEGIN IMMEDIATE","PRAGMA foreign_keys;",
              "PRAGMA defer_foreign_keys = ON;","PRAGMA defer_foreign_keys;"))
            d.write("parent-last");"ok"
        } };check(d.commitCount==1 && d.rollbackCount==0 && d.deferred==0L)
    }
    ok("returns caller result only after successful transaction") {
        val d=FakePinnedDriver();val n=runSync { port(d).restoreNewParents { d.write("x"); 731 } }
        check(n==731 && d.commitCount==1)
    }
    ok("empty stage body remains valid transaction guard") {
        val d=FakePinnedDriver();runSync { port(d).restoreNewParents { } };check(d.commitCount==1)
    }
    ok("FK integrity check runs after user writes") {
        val d=FakePinnedDriver();runSync { port(d).restoreNewParents { d.write("a") } }
        check(d.statements.indexOf("PRAGMA foreign_key_check;")>d.statements.indexOf("WRITE:a"))
    }
    ok("rolls back exceptions thrown inside stage block") {
        val d=FakePinnedDriver();check(runCatching {runSync { port(d).restoreNewParents {
            d.write("partial");error("injected")
        } }}.isFailure);check(d.rows.isEmpty() && d.commitCount==0 && d.rollbackCount==1)
    }
    reject("read-only FK setting OFF prevents callback") {
        val d=FakePinnedDriver();d.foreignKeys=0L
        runSync { port(d).restoreNewParents { d.write("should-not-write") } }
    }
    ok("FK disabled rejection causes rollback and no writes") {
        val d=FakePinnedDriver();d.foreignKeys=0L
        check(runCatching {runSync {port(d).restoreNewParents {d.write("forbidden")}}}.isFailure)
        check(d.rows.isEmpty() && d.rollbackCount==1 && d.commitCount==0)
    }
    reject("PRAGMA unavailable gives explicit fail-closed") {
        val d=FakePinnedDriver();d.emptyPragma="PRAGMA foreign_keys;"
        runSync {port(d).restoreNewParents {}}
    }
    reject("backend refuses setting deferred foreign keys") {
        val d=FakePinnedDriver();d.rejectPragma=true
        runSync {port(d).restoreNewParents {}}
    }
    reject("deferred PRAGMA returns no rows") {
        val d=FakePinnedDriver();d.emptyPragma="PRAGMA defer_foreign_keys;"
        runSync {port(d).restoreNewParents {}}
    }
    ok("commit always clears defer_foreign_keys in host") {
        val d=FakePinnedDriver();runSync {port(d).restoreNewParents {d.write("z")}}
        check(d.deferred==0L)
    }
    ok("callback exception resets temporary defer flag") {
        val d=FakePinnedDriver();runCatching{runSync{port(d).restoreNewParents {d.write("x");error("x")}}}
        check(d.deferred==0L)
    }
    reject("FK violation detected before commit") {
        val d=FakePinnedDriver();runSync {port(d).restoreNewParents {d.write("invalid");d.violations=true}}
    }
    ok("FK violations rollback all staged rows") {
        val d=FakePinnedDriver();runCatching{runSync{port(d).restoreNewParents {d.write("a");d.write("b");d.violations=true}}}
        check(d.rows.isEmpty()&&d.commitCount==0&&d.rollbackCount==1)
    }
    reject("connection-context loss detected on final PRAGMA probe") {
        val d=FakePinnedDriver();d.switchConnectionMidway=true
        runSync {port(d).restoreNewParents {d.write("a")}}
    }
    ok("context loss rolls back partial writes") {
        val d=FakePinnedDriver();d.switchConnectionMidway=true
        runCatching{runSync{port(d).restoreNewParents {d.write("a")}}}
        check(d.rows.isEmpty() && d.rollbackCount==1)
    }
    ok("all writes share one explicit transaction") {
        val d=FakePinnedDriver();runSync{port(d).restoreNewParents {d.write("a");d.write("b")}}
        check(d.beginCount==1 && d.commitCount==1 && d.statements.count{it=="BEGIN IMMEDIATE"}==1)
    }
    ok("no nested start or background handoff in host protocol") {
        val d=FakePinnedDriver();runSync{port(d).restoreNewParents {d.write("a")}}
        check(d.statements.none {it.contains("withContext")})
    }
    reject("commit exception cannot report result") {
        val d=FakePinnedDriver();d.commitError=true
        runSync{port(d).restoreNewParents {d.write("partial");42}}
    }
    ok("commit exception rolls back all temporary writes") {
        val d=FakePinnedDriver();d.commitError=true
        runCatching{runSync{port(d).restoreNewParents {d.write("partial")}}}
        check(d.rows.isEmpty() && d.rollbackCount==1 && d.commitCount==0)
    }
    ok("PRAGMA checks leave connection's FK enabled") {
        val d=FakePinnedDriver();runSync{port(d).restoreNewParents {}}
        check(d.foreignKeys==1L)
    }
    ok("PRAGMA is not issued before BEGIN IMMEDIATE") {
        val d=FakePinnedDriver();runSync{port(d).restoreNewParents {}}
        check(d.statements.first()=="BEGIN IMMEDIATE")
    }
    ok("stage callback uses suspend contract") {
        val d=FakePinnedDriver();runSync {port(d).restoreNewParents {d.write("suspend-staging")}}
        check(d.statements.contains("WRITE:suspend-staging"))
    }
    ok("query count and SQL strings never depend on user URL") {
        val d=FakePinnedDriver();runSync{port(d).restoreNewParents {d.write("merged://polaris/test")}}
        check(d.statements.filter{it.startsWith("PRAGMA")}.all{!it.contains("merged://")})
    }
    ok("driver is inspected twice after activation") {
        val d=FakePinnedDriver();runSync{port(d).restoreNewParents {}}
        check(d.statements.count{it=="PRAGMA defer_foreign_keys;"}==2)
    }
    ok("fresh-parent stages use strict dependency / parent / readback order") {
        val d = FakePinnedDriver(); val order=mutableListOf<String>()
        val stages = object : PolarisFreshParentStages<String> {
            override suspend fun reserveUnusedParentId(item: String): Long {order.add("reserve");return 900}
            override suspend fun stageAllDependencies(item: String,reservedParentId: Long) {order.add("dependencies");d.write("dependencies")}
            override suspend fun insertFullParentLast(item: String,reservedParentId: Long) {order.add("parent");d.write("parent")}
            override suspend fun assertExactStoredParent(item: String,reservedParentId: Long) {order.add("readback")}
        }
        val ids=runSync {port(d).restoreFreshParents(listOf("one"),stages)}
        check(ids==listOf(900L) && order==listOf("reserve","dependencies","parent","readback"))
    }
    ok("multiple new parents still use one transaction") {
        val d=FakePinnedDriver();var nextId=900L
        val stages = object : PolarisFreshParentStages<String> {
            override suspend fun reserveUnusedParentId(item:String)=nextId++
            override suspend fun stageAllDependencies(item:String,reservedParentId:Long) {d.write("child:$item")}
            override suspend fun insertFullParentLast(item:String,reservedParentId:Long) {d.write("parent:$item")}
            override suspend fun assertExactStoredParent(item:String,reservedParentId:Long) {check(d.rows.last()=="parent:$item")}
        }
        val ids=runSync {port(d).restoreFreshParents(listOf("a","b"),stages)}
        check(ids==listOf(900L,901L) && d.commitCount==1 && d.beginCount==1)
    }
    ok("second-parent metadata failure rolls back first parent and dependencies") {
        val d=FakePinnedDriver();var id=900L
        val stages=object:PolarisFreshParentStages<String> {
            override suspend fun reserveUnusedParentId(item:String)=id++
            override suspend fun stageAllDependencies(item:String,reservedParentId:Long){d.write("child:$item")}
            override suspend fun insertFullParentLast(item:String,reservedParentId:Long){d.write("parent:$item")}
            override suspend fun assertExactStoredParent(item:String,reservedParentId:Long){if(item=="second") error("metadata mismatch")}
        }
        check(runCatching{runSync{port(d).restoreFreshParents(listOf("first","second"),stages)}}.isFailure)
        check(d.rows.isEmpty() && d.commitCount==0 && d.rollbackCount==1)
    }
    reject("batch rejects repeated reserved parent ID") {
        val d=FakePinnedDriver()
        val stages=object:PolarisFreshParentStages<String> {
            override suspend fun reserveUnusedParentId(item:String)=123L
            override suspend fun stageAllDependencies(item:String,reservedParentId:Long){d.write("child:$item")}
            override suspend fun insertFullParentLast(item:String,reservedParentId:Long){d.write("parent:$item")}
            override suspend fun assertExactStoredParent(item:String,reservedParentId:Long){}
        }
        runSync {port(d).restoreFreshParents(listOf("a","b"),stages)}
    }
    ok("repeated ID in batch leaves no rows after rollback") {
        val d=FakePinnedDriver()
        val stages=object:PolarisFreshParentStages<String> {
            override suspend fun reserveUnusedParentId(item:String)=123L
            override suspend fun stageAllDependencies(item:String,reservedParentId:Long){d.write("child:$item")}
            override suspend fun insertFullParentLast(item:String,reservedParentId:Long){d.write("parent:$item")}
            override suspend fun assertExactStoredParent(item:String,reservedParentId:Long){}
        }
        runCatching{runSync {port(d).restoreFreshParents(listOf("a","b"),stages)}}
        check(d.rows.isEmpty() && d.rollbackCount==1)
    }
    reject("zero or negative reservation blocked before child writes") {
        val d=FakePinnedDriver()
        val stages=object:PolarisFreshParentStages<String> {
            override suspend fun reserveUnusedParentId(item:String)=0L
            override suspend fun stageAllDependencies(item:String,reservedParentId:Long){error("should not write")}
            override suspend fun insertFullParentLast(item:String,reservedParentId:Long){}
            override suspend fun assertExactStoredParent(item:String,reservedParentId:Long){}
        }
        runSync {port(d).restoreFreshParents(listOf("x"),stages)}
    }
    reject("empty fresh batch is invalid") {
        val d=FakePinnedDriver()
        val stages=object:PolarisFreshParentStages<String> {
            override suspend fun reserveUnusedParentId(item:String)=123L
            override suspend fun stageAllDependencies(item:String,reservedParentId:Long){}
            override suspend fun insertFullParentLast(item:String,reservedParentId:Long){}
            override suspend fun assertExactStoredParent(item:String,reservedParentId:Long){}
        }
        runSync {port(d).restoreFreshParents(emptyList(),stages)}
    }
    ok("empty fresh batch does not open transaction") {
        val d=FakePinnedDriver()
        val stages=object:PolarisFreshParentStages<String> {
            override suspend fun reserveUnusedParentId(item:String)=123L
            override suspend fun stageAllDependencies(item:String,reservedParentId:Long){}
            override suspend fun insertFullParentLast(item:String,reservedParentId:Long){}
            override suspend fun assertExactStoredParent(item:String,reservedParentId:Long){}
        }
        runCatching{runSync {port(d).restoreFreshParents(emptyList(),stages)}}
        check(d.beginCount==0 && d.rollbackCount==0)
    }
    println("POLARIS_PINNED_DEFERRED_FK_GUARD_PASS $passed")
    check(passed==33)
}
