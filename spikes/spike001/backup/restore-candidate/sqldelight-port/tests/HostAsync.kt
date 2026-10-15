package app.cash.sqldelight.async.coroutines
import tachiyomi.data.Query
suspend fun <T> Query<T>.awaitAsList():List<T> = fetch()
suspend fun <T> Query<T>.awaitAsOne():T=fetch().single()
suspend fun <T> Query<T>.awaitAsOneOrNull():T?=fetch().singleOrNull()
