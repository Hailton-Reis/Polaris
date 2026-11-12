package polaris.domain.lifecycle

enum class CanonicalWorkAvailability { ACTIVE, DEGRADED, ORPHANED }
enum class LifecycleAction { NONE, REFRESH_ALTERNATIVES, REDISCOVER_VARIANTS, REQUEST_USER_ATTENTION }

data class CanonicalWorkLifecycleInput(
    val linkedVariantCount: Int,
    val usableVariantCount: Int,
    val workInLibrary: Boolean,
    val hasKnownAliases: Boolean,
)

data class CanonicalWorkLifecycleDecision(
    val availability: CanonicalWorkAvailability,
    val actions: Set<LifecycleAction>,
    val keepCanonicalWork: Boolean,
)

object CanonicalWorkLifecyclePolicy {
    fun evaluate(input: CanonicalWorkLifecycleInput): CanonicalWorkLifecycleDecision {
        require(input.linkedVariantCount >= 0)
        require(input.usableVariantCount in 0..input.linkedVariantCount)

        if (input.linkedVariantCount == 0) {
            val actions = buildSet {
                if (input.hasKnownAliases) add(LifecycleAction.REDISCOVER_VARIANTS)
                if (input.workInLibrary) add(LifecycleAction.REQUEST_USER_ATTENTION)
                if (isEmpty()) add(LifecycleAction.NONE)
            }
            return CanonicalWorkLifecycleDecision(
                availability = CanonicalWorkAvailability.ORPHANED,
                actions = actions,
                keepCanonicalWork = true,
            )
        }

        if (input.usableVariantCount == 0) {
            return CanonicalWorkLifecycleDecision(
                availability = CanonicalWorkAvailability.DEGRADED,
                actions = setOf(LifecycleAction.REFRESH_ALTERNATIVES),
                keepCanonicalWork = true,
            )
        }

        return CanonicalWorkLifecycleDecision(
            availability = CanonicalWorkAvailability.ACTIVE,
            actions = setOf(LifecycleAction.NONE),
            keepCanonicalWork = true,
        )
    }
}
