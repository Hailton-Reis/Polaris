package polaris.domain.matching

enum class ManualLinkDecision {
    FORCE_SAME_WORK,
    FORCE_DIFFERENT_WORK,
}

data class WorkIdentityRef(
    val sourceId: Long,
    val sourceWorkKey: String,
) : Comparable<WorkIdentityRef> {
    override fun compareTo(other: WorkIdentityRef): Int =
        compareValuesBy(this, other, WorkIdentityRef::sourceId, WorkIdentityRef::sourceWorkKey)
}

data class WorkPairKey private constructor(
    val first: WorkIdentityRef,
    val second: WorkIdentityRef,
) {
    companion object {
        fun of(a: WorkIdentityRef, b: WorkIdentityRef): WorkPairKey {
            require(a != b) { "Cannot override a work against itself" }
            return if (a <= b) WorkPairKey(a, b) else WorkPairKey(b, a)
        }
    }
}

data class WorkLinkOverride(
    val pair: WorkPairKey,
    val decision: ManualLinkDecision,
    val createdAtEpochMs: Long,
)

enum class EffectiveMatchDecision {
    SAME_WORK,
    DIFFERENT_WORK,
    USE_AUTOMATIC_MATCHER,
}

object WorkLinkOverridePolicy {
    fun resolve(
        left: WorkIdentityRef,
        right: WorkIdentityRef,
        overrides: Collection<WorkLinkOverride>,
    ): EffectiveMatchDecision {
        val key = WorkPairKey.of(left, right)
        val override = overrides
            .filter { it.pair == key }
            .maxByOrNull { it.createdAtEpochMs }
            ?: return EffectiveMatchDecision.USE_AUTOMATIC_MATCHER

        return when (override.decision) {
            ManualLinkDecision.FORCE_SAME_WORK -> EffectiveMatchDecision.SAME_WORK
            ManualLinkDecision.FORCE_DIFFERENT_WORK -> EffectiveMatchDecision.DIFFERENT_WORK
        }
    }
}
