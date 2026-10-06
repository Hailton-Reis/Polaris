package polaris.domain.translation

data class CanonicalTranslationScope(
    val stableWorkKey: String,
    val displayTitle: String,
) {
    init {
        require(stableWorkKey.isNotBlank())
        require(displayTitle.isNotBlank())
    }

    val memoryScopeKey: String
        get() = "polaris:" + stableWorkKey.trim().lowercase()

    fun withDisplayTitle(newTitle: String): CanonicalTranslationScope =
        copy(displayTitle = newTitle)
}
