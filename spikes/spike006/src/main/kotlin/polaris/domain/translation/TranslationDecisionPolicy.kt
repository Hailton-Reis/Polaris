package polaris.domain.translation

enum class TranslationOpenMode {
    READ_ORIGINAL,
    READ_TRANSLATED_CACHE,
    QUEUE_TRANSLATION,
    READ_FOREIGN_UNTRANSLATED,
}

data class TranslationDecisionInput(
    val canonicalWorkId: String,
    val canonicalTitle: String,
    val sourceLanguage: String,
    val targetLanguage: String,
    val cachedTranslationAvailable: Boolean,
    val translationEnabled: Boolean,
    val translatorAvailable: Boolean,
)

data class TranslationContextIdentity(
    val canonicalWorkId: String,
    val canonicalTitle: String,
)

data class TranslationOpenDecision(
    val mode: TranslationOpenMode,
    val context: TranslationContextIdentity,
    val requiresTranslation: Boolean,
    val reason: String,
)

object TranslationDecisionPolicy {

    fun decide(input: TranslationDecisionInput): TranslationOpenDecision {
        val context = TranslationContextIdentity(
            canonicalWorkId = input.canonicalWorkId,
            canonicalTitle = input.canonicalTitle,
        )

        val source = normalizeLanguage(input.sourceLanguage)
        val target = normalizeLanguage(input.targetLanguage)

        if (source == target) {
            return TranslationOpenDecision(
                mode = TranslationOpenMode.READ_ORIGINAL,
                context = context,
                requiresTranslation = false,
                reason = "source_already_target_language",
            )
        }

        if (input.cachedTranslationAvailable) {
            return TranslationOpenDecision(
                mode = TranslationOpenMode.READ_TRANSLATED_CACHE,
                context = context,
                requiresTranslation = false,
                reason = "translation_cache_hit",
            )
        }

        if (input.translationEnabled && input.translatorAvailable) {
            return TranslationOpenDecision(
                mode = TranslationOpenMode.QUEUE_TRANSLATION,
                context = context,
                requiresTranslation = true,
                reason = "foreign_variant_requires_translation",
            )
        }

        return TranslationOpenDecision(
            mode = TranslationOpenMode.READ_FOREIGN_UNTRANSLATED,
            context = context,
            requiresTranslation = false,
            reason = if (!input.translationEnabled) {
                "translation_disabled"
            } else {
                "no_translator_available"
            },
        )
    }

    fun normalizeLanguage(language: String): String = when (language.trim().lowercase()) {
        "pt-br", "pt_br", "ptbr", "br", "portuguese-brazil", "portuguese (brazil)" -> "pt-br"
        "pt", "pt-pt", "pt_pt" -> "pt"
        "en", "en-us", "en_us", "en-gb", "en_gb" -> "en"
        "ja", "jp", "jpn" -> "ja"
        "ko", "kr", "kor" -> "ko"
        "zh", "zh-cn", "zh_cn", "zh-tw", "zh_tw", "cn" -> "zh"
        else -> language.trim().lowercase()
    }
}
