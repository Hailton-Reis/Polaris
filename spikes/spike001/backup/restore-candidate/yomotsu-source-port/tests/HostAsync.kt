package app.cash.sqldelight.async.coroutines
import tachiyomi.data.Query
suspend fun <T> Query<T>.awaitAsList():List<T> = fetch()
