package polaris.domain.refresh

private const val NOW = 2_000_000_000_000L
private const val HOUR = 3_600_000L

fun main() {
    val planner = VariantRefreshPlanner(
        RefreshPolicy(
            backgroundTtlMs = 6 * HOUR,
            workOpenTtlMs = 30 * 60_000L,
            maxConcurrency = 4,
        ),
    )

    val candidates = listOf(
        VariantRefreshCandidate("selected-pt", "pt-BR", RefreshHealthState.HEALTHY, NOW - 5 * 60_000L, currentlySelected = true),
        VariantRefreshCandidate("fresh-pt", "pt-BR", RefreshHealthState.HEALTHY, NOW - HOUR),
        VariantRefreshCandidate("stale-en", "en", RefreshHealthState.HEALTHY, NOW - 8 * HOUR),
        VariantRefreshCandidate("challenge", "pt-BR", RefreshHealthState.CHALLENGED, null),
        VariantRefreshCandidate("rate", "en", RefreshHealthState.RATE_LIMITED, NOW - 10 * HOUR, cooldownUntilEpochMs = NOW + HOUR),
    )

    val background = planner.plan(candidates, RefreshTrigger.BACKGROUND_LIBRARY, NOW)
    check(background.orderedVariantIds == listOf("selected-pt", "stale-en"))
    check(background.skipped["fresh-pt"] == "fresh_within_ttl")
    check(background.skipped["challenge"] == "challenge_requires_user")
    check(background.skipped["rate"] == "rate_limit_cooldown")
    check(background.maxConcurrency == 4)

    val manual = planner.plan(candidates, RefreshTrigger.MANUAL_REFRESH, NOW)
    check("fresh-pt" in manual.orderedVariantIds)
    check("challenge" !in manual.orderedVariantIds)

    val unreachable = VariantRefreshCandidate("dead", "pt-BR", RefreshHealthState.UNREACHABLE, NOW - 10 * HOUR)
    check("dead" !in planner.plan(listOf(unreachable), RefreshTrigger.BACKGROUND_LIBRARY, NOW).orderedVariantIds)
    check("dead" in planner.plan(listOf(unreachable), RefreshTrigger.MANUAL_REFRESH, NOW).orderedVariantIds)

    println("SPIKE022_VARIANT_REFRESH_PLANNER_TESTS_PASS")
}
