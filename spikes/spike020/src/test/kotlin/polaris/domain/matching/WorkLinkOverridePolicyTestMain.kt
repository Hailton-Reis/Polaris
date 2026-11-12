package polaris.domain.matching

fun main() {
    val a = WorkIdentityRef(10L, "/tbate")
    val b = WorkIdentityRef(20L, "/comeco")

    check(WorkPairKey.of(a, b) == WorkPairKey.of(b, a))
    check(WorkLinkOverridePolicy.resolve(a, b, emptyList()) == EffectiveMatchDecision.USE_AUTOMATIC_MATCHER)

    val same = WorkLinkOverride(WorkPairKey.of(a, b), ManualLinkDecision.FORCE_SAME_WORK, 1000)
    check(WorkLinkOverridePolicy.resolve(a, b, listOf(same)) == EffectiveMatchDecision.SAME_WORK)

    val laterDifferent = WorkLinkOverride(WorkPairKey.of(a, b), ManualLinkDecision.FORCE_DIFFERENT_WORK, 2000)
    check(WorkLinkOverridePolicy.resolve(b, a, listOf(same, laterDifferent)) == EffectiveMatchDecision.DIFFERENT_WORK)

    check(runCatching { WorkPairKey.of(a, a) }.isFailure)

    println("SPIKE020_WORK_LINK_OVERRIDE_TESTS_PASS")
}
