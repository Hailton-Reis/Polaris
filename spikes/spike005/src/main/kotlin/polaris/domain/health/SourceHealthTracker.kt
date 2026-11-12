package polaris.domain.health

import polaris.domain.canonical.SourceHealthSnapshot
import polaris.domain.canonical.SourceHealthState
import kotlin.math.roundToLong

sealed interface SourceAccessEvent {
    data class Success(val latencyMs: Long) : SourceAccessEvent

    data class Failure(
        val kind: FailureKind,
        val retryAfterMs: Long? = null,
    ) : SourceAccessEvent
}

enum class FailureKind {
    NETWORK,
    TIMEOUT,
    SERVER_5XX,
    RATE_LIMIT,
    AUTH_REQUIRED,
    AUTH_EXPIRED,
    CHALLENGE,
    PARSE_OR_CONTRACT,
    SOURCE_REMOVED,
}

data class SourceHealthRecord(
    val snapshot: SourceHealthSnapshot,
    val totalSuccesses: Long = 0,
    val totalFailures: Long = 0,
    val lastFailureKind: FailureKind? = null,
    val lastFailureEpochMs: Long? = null,
)

class SourceHealthTracker(
    private val defaultRateLimitCooldownMs: Long = 5 * 60_000L,
) {
    fun initial(): SourceHealthRecord = SourceHealthRecord(
        snapshot = SourceHealthSnapshot(
            state = SourceHealthState.HEALTHY,
            successRate = 1.0,
        ),
    )

    fun apply(
        current: SourceHealthRecord,
        event: SourceAccessEvent,
        nowEpochMs: Long,
    ): SourceHealthRecord = when (event) {
        is SourceAccessEvent.Success -> onSuccess(current, event, nowEpochMs)
        is SourceAccessEvent.Failure -> onFailure(current, event, nowEpochMs)
    }

    private fun onSuccess(
        current: SourceHealthRecord,
        event: SourceAccessEvent.Success,
        nowEpochMs: Long,
    ): SourceHealthRecord {
        val successes = current.totalSuccesses + 1
        val failures = current.totalFailures
        val successRate = ratio(successes, failures)
        val previousLatency = current.snapshot.averageLatencyMs
        val latency = event.latencyMs.coerceAtLeast(0)
        val smoothedLatency = if (previousLatency <= 0L) {
            latency
        } else {
            (previousLatency * 0.70 + latency * 0.30).roundToLong()
        }

        return current.copy(
            snapshot = current.snapshot.copy(
                state = if (successRate >= 0.70) SourceHealthState.HEALTHY else SourceHealthState.DEGRADED,
                successRate = successRate,
                averageLatencyMs = smoothedLatency,
                consecutiveFailures = 0,
                lastSuccessEpochMs = nowEpochMs,
                cooldownUntilEpochMs = null,
            ),
            totalSuccesses = successes,
            lastFailureKind = null,
            lastFailureEpochMs = null,
        )
    }

    private fun onFailure(
        current: SourceHealthRecord,
        event: SourceAccessEvent.Failure,
        nowEpochMs: Long,
    ): SourceHealthRecord {
        val successes = current.totalSuccesses
        val failures = current.totalFailures + 1
        val consecutive = current.snapshot.consecutiveFailures + 1
        val successRate = ratio(successes, failures)

        val state = when (event.kind) {
            FailureKind.AUTH_REQUIRED -> SourceHealthState.AUTH_REQUIRED
            FailureKind.AUTH_EXPIRED -> SourceHealthState.AUTH_EXPIRED
            FailureKind.CHALLENGE -> SourceHealthState.CHALLENGED
            FailureKind.RATE_LIMIT -> SourceHealthState.RATE_LIMITED
            FailureKind.SOURCE_REMOVED -> SourceHealthState.BROKEN
            FailureKind.PARSE_OR_CONTRACT ->
                if (consecutive >= 3) SourceHealthState.BROKEN else SourceHealthState.DEGRADED
            FailureKind.NETWORK,
            FailureKind.TIMEOUT,
            FailureKind.SERVER_5XX,
            -> if (consecutive >= 4) SourceHealthState.UNREACHABLE else SourceHealthState.DEGRADED
        }

        val cooldown = if (event.kind == FailureKind.RATE_LIMIT) {
            nowEpochMs + (event.retryAfterMs ?: defaultRateLimitCooldownMs).coerceAtLeast(0L)
        } else {
            null
        }

        return current.copy(
            snapshot = current.snapshot.copy(
                state = state,
                successRate = successRate,
                consecutiveFailures = consecutive,
                cooldownUntilEpochMs = cooldown,
            ),
            totalFailures = failures,
            lastFailureKind = event.kind,
            lastFailureEpochMs = nowEpochMs,
        )
    }

    private fun ratio(successes: Long, failures: Long): Double {
        val total = successes + failures
        return if (total <= 0L) 1.0 else successes.toDouble() / total
    }
}
