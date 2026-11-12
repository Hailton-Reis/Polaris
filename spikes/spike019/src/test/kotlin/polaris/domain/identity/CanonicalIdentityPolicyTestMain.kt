package polaris.domain.identity

import java.util.UUID

fun main() {
    val fixed = UUID.fromString("123e4567-e89b-12d3-a456-426614174000")
    val created = CanonicalIdentityPolicy.create("The Beginning After the End") { fixed }
    check(created.stableKey.value == fixed.toString())

    val renamed = CanonicalIdentityPolicy.rename(created, "O Começo Depois do Fim")
    check(renamed.stableKey == created.stableKey)

    val withTracker = CanonicalIdentityPolicy.attachExternalId(renamed, "AniList", "123")
    check(withTracker.stableKey == created.stableKey)
    check(withTracker.externalIds["anilist"] == "123")

    check(CanonicalIdentityPolicy.translationScopeKey(withTracker) == "polaris:$fixed")

    println("SPIKE019_CANONICAL_IDENTITY_TESTS_PASS")
}
