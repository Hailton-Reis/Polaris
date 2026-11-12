package app.cash.sqldelight.db

sealed class QueryResult<T> {
    class AsyncValue<T>(val supplier: suspend () -> T) : QueryResult<T>()
    @Suppress("UNCHECKED_CAST")
    suspend fun await(): T = (this as AsyncValue<T>).supplier()
}
interface SqlCursor {
    fun next(): QueryResult<Boolean>
    fun getLong(index: Int): Long?
}
interface SqlDriver {
    fun execute(identifier: Int?, sql: String, parameters: Int, binders: Any?): QueryResult<Long>
    fun <R> executeQuery(identifier: Int?, sql: String,
                        mapper: (SqlCursor) -> QueryResult<R>, parameters: Int, binders: Any?): QueryResult<R>
}
