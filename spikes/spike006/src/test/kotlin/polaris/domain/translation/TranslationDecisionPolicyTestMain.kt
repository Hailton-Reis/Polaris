package polaris.domain.translation

private fun input(
    source: String,
    cached: Boolean = false,
    enabled: Boolean = true,
    available: Boolean = true,
) = TranslationDecisionInput(
    canonicalWorkId = "work-1",
    canonicalTitle = "Canonical Work",
    sourceLanguage = source,
    targetLanguage = "pt-BR",
    cachedTranslationAvailable = cached,
    translationEnabled = enabled,
    translatorAvailable = available,
)

fun main() {
    run {
        val decision = TranslationDecisionPolicy.decide(input("pt-BR"))
        check(decision.mode == TranslationOpenMode.READ_ORIGINAL)
        check(!decision.requiresTranslation)
    }

    run {
        val decision = TranslationDecisionPolicy.decide(input("pt"))
        check(decision.mode == TranslationOpenMode.READ_ORIGINAL)
        check(!decision.requiresTranslation)
    }

    run {
        val decision = TranslationDecisionPolicy.decide(input("en", cached = true))
        check(decision.mode == TranslationOpenMode.READ_TRANSLATED_CACHE)
    }

    run {
        val decision = TranslationDecisionPolicy.decide(input("en"))
        check(decision.mode == TranslationOpenMode.QUEUE_TRANSLATION)
        check(decision.requiresTranslation)
        check(decision.context.canonicalWorkId == "work-1")
    }

    run {
        val decision = TranslationDecisionPolicy.decide(input("ko", available = false))
        check(decision.mode == TranslationOpenMode.READ_FOREIGN_UNTRANSLATED)
        check(decision.reason == "no_translator_available")
    }

    run {
        val englishVariant = TranslationDecisionPolicy.decide(
            input("en").copy(canonicalTitle = "The Beginning After the End"),
        )
        val portugueseNamedVariant = TranslationDecisionPolicy.decide(
            input("ko").copy(canonicalTitle = "The Beginning After the End"),
        )
        check(englishVariant.context == portugueseNamedVariant.context)
    }

    println("SPIKE006_TRANSLATION_POLICY_TESTS_PASS")
}
