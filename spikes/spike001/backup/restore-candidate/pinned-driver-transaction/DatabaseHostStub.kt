package tachiyomi.data
import polaris.spike001.backup.restore.FakePinnedDriver
class Database(private val driver: FakePinnedDriver) {
    suspend fun <T> transactionWithResult(block: suspend () -> T): T {
        driver.begin()
        try {
            val result = block()
            driver.commit()
            return result
        } catch (t: Throwable) {
            driver.rollback()
            throw t
        }
    }
}
