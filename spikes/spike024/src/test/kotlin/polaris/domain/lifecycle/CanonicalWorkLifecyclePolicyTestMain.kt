package polaris.domain.lifecycle

fun main() {
    run {
        val d = CanonicalWorkLifecyclePolicy.evaluate(CanonicalWorkLifecycleInput(3, 2, true, true))
        check(d.availability == CanonicalWorkAvailability.ACTIVE)
        check(d.keepCanonicalWork)
    }
    run {
        val d = CanonicalWorkLifecyclePolicy.evaluate(CanonicalWorkLifecycleInput(2, 0, true, true))
        check(d.availability == CanonicalWorkAvailability.DEGRADED)
        check(LifecycleAction.REFRESH_ALTERNATIVES in d.actions)
    }
    run {
        val d = CanonicalWorkLifecyclePolicy.evaluate(CanonicalWorkLifecycleInput(0, 0, true, true))
        check(d.availability == CanonicalWorkAvailability.ORPHANED)
        check(LifecycleAction.REDISCOVER_VARIANTS in d.actions)
        check(LifecycleAction.REQUEST_USER_ATTENTION in d.actions)
        check(d.keepCanonicalWork)
    }
    run {
        val d = CanonicalWorkLifecyclePolicy.evaluate(CanonicalWorkLifecycleInput(0, 0, false, false))
        check(d.keepCanonicalWork)
        check(d.actions == setOf(LifecycleAction.NONE))
    }
    println("SPIKE024_WORK_LIFECYCLE_TESTS_PASS")
}
