package polaris.domain.language

data class LanguageRouteRequest(
    val targetLanguage: String = "pt-BR",
    val bridgeLanguages: List<String> = listOf("en"),
    val originalLanguage: String? = null,
    val extraFallbackLanguages: List<String> = emptyList(),
    val includeBaseLanguageFallback: Boolean = true,
)

object LanguageRoutePlanner {
    fun plan(request: LanguageRouteRequest): List<String> {
        val values = mutableListOf<String>()
        values += request.targetLanguage

        val target = normalize(request.targetLanguage)
        if (request.includeBaseLanguageFallback && target == "pt-br") {
            values += "pt"
        }

        values += request.bridgeLanguages
        request.originalLanguage?.takeIf(String::isNotBlank)?.let(values::add)
        values += request.extraFallbackLanguages

        return values
            .map(::normalize)
            .filter(String::isNotBlank)
            .distinct()
    }

    fun normalize(language: String): String = when (language.trim().lowercase()) {
        "pt-br", "pt_br", "ptbr", "br", "portuguese-brazil", "portuguese (brazil)" -> "pt-br"
        "pt", "pt-pt", "pt_pt" -> "pt"
        "en", "en-us", "en_us", "en-gb", "en_gb" -> "en"
        "ja", "jp", "jpn" -> "ja"
        "ko", "kr", "kor" -> "ko"
        "zh", "zh-cn", "zh_cn", "zh-tw", "zh_tw", "cn" -> "zh"
        else -> language.trim().lowercase()
    }
}
