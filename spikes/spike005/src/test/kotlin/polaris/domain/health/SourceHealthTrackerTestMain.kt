package polaris.domain.health

import polaris.domain.canonical.SourceHealthState

private const val NOW = 2_000_000_000_000L

fun main() {
    val tracker = SourceHealthTracker()

    run {
        var record = tracker.initial()
        record = tracker.apply(record, SourceAccessEvent.Success(800), NOW)
        record = tracker.apply(record, SourceAccessEvent.Success(200), NOW + 1)
        check(record.snapshot.state == SourceHealthState.HEALTHY)
        check(record.snapshot.averageLatencyMs in 600L..620L) { record.toString() }
        check(record.snapshot.consecutiveFailures == 0)
    }

    run {
        var record = tracker.initial()
        repeat(3) { i ->
            record = tracker.apply(record, SourceAccessEvent.Failure(FailureKind.TIMEOUT), NOW + i)
        }
        check(record.snapshot.state == SourceHealthState.DEGRADED)
        record = tracker.apply(record, SourceAccessEvent.Failure(FailureKind.TIMEOUT), NOW + 4)
        check(record.snapshot.state == SourceHealthState.UNREACHABLE)
    }

    run {
        var record = tracker.initial()
        record = tracker.apply(record, SourceAccessEvent.Failure(FailureKind.CHALLENGE), NOW)
        check(record.snapshot.state == SourceHealthState.CHALLENGED)
        check(!record.snapshot.isUsable(NOW))
        record = tracker.apply(record, SourceAccessEvent.Success(300), NOW + 1000)
        check(record.snapshot.state == SourceHealthState.HEALTHY)
        check(record.snapshot.isUsable(NOW + 1000))
    }

    run {
        var record = tracker.initial()
        record = tracker.apply(record, SourceAccessEvent.Failure(FailureKind.AUTH_EXPIRED), NOW)
        check(record.snapshot.state == SourceHealthState.AUTH_EXPIRED)
        check(!record.snapshot.isUsable(NOW))
        record = tracker.apply(record, SourceAccessEvent.Success(250), NOW + 5000)
        check(record.snapshot.state == SourceHealthState.HEALTHY)
    }

    run {
        var record = tracker.initial()
        record = tracker.apply(
            record,
            SourceAccessEvent.Failure(FailureKind.RATE_LIMIT, retryAfterMs = 60_000),
            NOW,
        )
        check(record.snapshot.state == SourceHealthState.RATE_LIMITED)
        check(!record.snapshot.isUsable(NOW + 59_999))
        check(record.snapshot.isUsable(NOW + 60_000))
    }

    run {
        var record = tracker.initial()
        repeat(2) { i ->
            record = tracker.apply(record, SourceAccessEvent.Failure(FailureKind.PARSE_OR_CONTRACT), NOW + i)
        }
        check(record.snapshot.state == SourceHealthState.DEGRADED)
        record = tracker.apply(record, SourceAccessEvent.Failure(FailureKind.PARSE_OR_CONTRACT), NOW + 3)
        check(record.snapshot.state == SourceHealthState.BROKEN)
    }

    println("SPIKE005_SOURCE_HEALTH_TESTS_PASS")
}
