package polaris.domain.refresh

enum class RefreshHealthState {
    HEALTHY,
    DEGRADED,
    AUTH_REQUIRED,
    AUTH_EXPIRED,
    CHALLENGED,
    RATE_LIMITED,
    BROKEN,
    UNREACHABLE,
}

enum class RefreshTrigger {
    BACKGROUND_LIBRARY,
    WORK_OPEN,
    MANUAL_REFRESH,
}

data class VariantRefreshCandidate(
    val variantId: String,
    val language: String,
    val health: RefreshHealthState,
    val lastRefreshedEpochMs: Long?,
    val cooldownUntilEpochMs: Long? = null,
    val currentlySelected: Boolean = false,
)

data class VariantRefreshPlan(
    val orderedVariantIds: List<String>,
    val skipped: Map<String, String>,
    val maxConcurrency: Int,
)

data class RefreshPolicy(
    val backgroundTtlMs: Long = 6 * 60 * 60_000L,
    val workOpenTtlMs: Long = 30 * 60_000L,
    val maxConcurrency: Int = 4,
) {
    init {
        require(backgroundTtlMs >= 0)
        require(workOpenTtlMs >= 0)
        require(maxConcurrency in 1..16)
    }
}

class VariantRefreshPlanner(
    private val policy: RefreshPolicy = RefreshPolicy(),
) {
    fun plan(
        candidates: List<VariantRefreshCandidate>,
        trigger: RefreshTrigger,
        nowEpochMs: Long,
    ): VariantRefreshPlan {
        val skipped = linkedMapOf<String, String>()
        val eligible = candidates.filter { candidate ->
            when (candidate.health) {
                RefreshHealthState.AUTH_REQUIRED -> false.also { skipped[candidate.variantId] = "auth_required" }
                RefreshHealthState.AUTH_EXPIRED -> false.also { skipped[candidate.variantId] = "auth_expired" }
                RefreshHealthState.CHALLENGED -> false.also { skipped[candidate.variantId] = "challenge_requires_user" }
                RefreshHealthState.BROKEN -> false.also { skipped[candidate.variantId] = "source_broken" }
                RefreshHealthState.UNREACHABLE -> {
                    if (trigger == RefreshTrigger.MANUAL_REFRESH) true
                    else false.also { skipped[candidate.variantId] = "unreachable_background_skip" }
                }
                RefreshHealthState.RATE_LIMITED -> {
                    val ready = candidate.cooldownUntilEpochMs?.let { it <= nowEpochMs } == true
                    if (!ready) skipped[candidate.variantId] = "rate_limit_cooldown"
                    ready
                }
                RefreshHealthState.HEALTHY,
                RefreshHealthState.DEGRADED,
                -> true
            }
        }.filter { candidate ->
            if (trigger == RefreshTrigger.MANUAL_REFRESH) return@filter true
            val ttl = when (trigger) {
                RefreshTrigger.BACKGROUND_LIBRARY -> policy.backgroundTtlMs
                RefreshTrigger.WORK_OPEN -> policy.workOpenTtlMs
                RefreshTrigger.MANUAL_REFRESH -> 0L
            }
            val fresh = candidate.lastRefreshedEpochMs?.let { nowEpochMs - it < ttl } == true
            if (fresh && !candidate.currentlySelected) skipped[candidate.variantId] = "fresh_within_ttl"
            !fresh || candidate.currentlySelected
        }

        val ordered = eligible.sortedWith(
            compareByDescending<VariantRefreshCandidate> { it.currentlySelected }
                .thenBy { healthPriority(it.health) }
                .thenBy { it.lastRefreshedEpochMs ?: Long.MIN_VALUE }
                .thenBy { it.variantId },
        ).map { it.variantId }

        return VariantRefreshPlan(
            orderedVariantIds = ordered,
            skipped = skipped,
            maxConcurrency = policy.maxConcurrency,
        )
    }

    private fun healthPriority(state: RefreshHealthState): Int = when (state) {
        RefreshHealthState.HEALTHY -> 0
        RefreshHealthState.DEGRADED -> 1
        RefreshHealthState.RATE_LIMITED -> 2
        RefreshHealthState.UNREACHABLE -> 3
        else -> 9
    }
}
