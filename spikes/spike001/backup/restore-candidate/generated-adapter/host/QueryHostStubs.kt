package app.cash.sqldelight.async.coroutines
import tachiyomi.data.Query
suspend fun <T> Query<T>.awaitAsOne(): T = rows().single()
suspend fun <T> Query<T>.awaitAsOneOrNull(): T? = rows().singleOrNull()
suspend fun <T> Query<T>.awaitAsList(): List<T> = rows()
