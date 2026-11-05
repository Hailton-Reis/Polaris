package polaris.domain.translation

fun main() {
    val original = CanonicalTranslationScope(
        stableWorkKey = "WORK-123",
        displayTitle = "The Beginning After the End",
    )
    val renamed = original.withDisplayTitle("O Começo Depois do Fim")

    check(original.memoryScopeKey == "polaris:work-123")
    check(renamed.memoryScopeKey == original.memoryScopeKey)
    check(renamed.displayTitle != original.displayTitle)

    println("SPIKE014_CANONICAL_TRANSLATION_SCOPE_TESTS_PASS")
}
