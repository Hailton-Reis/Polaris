package polaris.domain.metadata

import java.text.Normalizer

data class MetadataVariant(
    val sourceVariantId: String,
    val language: String,
    val title: String,
    val author: String? = null,
    val artist: String? = null,
    val description: String? = null,
    val genres: Set<String> = emptySet(),
    val coverUrl: String? = null,
    val usable: Boolean = true,
    val lastUpdatedEpochMs: Long? = null,
)

data class CanonicalMetadataOverrides(
    val title: String? = null,
    val author: String? = null,
    val artist: String? = null,
    val description: String? = null,
    val coverUrl: String? = null,
)

data class CanonicalMetadata(
    val title: String,
    val author: String?,
    val artist: String?,
    val description: String?,
    val genres: Set<String>,
    val coverUrl: String?,
    val provenance: Map<String, String>,
)

class CanonicalMetadataResolver {
    fun resolve(
        variants: List<MetadataVariant>,
        preferredLanguages: List<String>,
        current: CanonicalMetadata? = null,
        overrides: CanonicalMetadataOverrides = CanonicalMetadataOverrides(),
    ): CanonicalMetadata {
        require(variants.isNotEmpty()) { "At least one metadata variant is required" }

        val usable = variants.filter { it.usable }.ifEmpty { variants }
        val normalizedPrefs = preferredLanguages.map(::normalizeLanguage)
        val ranked = usable.sortedWith(
            compareBy<MetadataVariant> { languageTier(it.language, normalizedPrefs) }
                .thenByDescending { completeness(it) }
                .thenByDescending { it.lastUpdatedEpochMs ?: Long.MIN_VALUE }
                .thenBy { it.sourceVariantId },
        )
        val best = ranked.first()
        val bestTier = languageTier(best.language, normalizedPrefs)
        val bestTierVariants = ranked.filter { languageTier(it.language, normalizedPrefs) == bestTier }

        val provenance = linkedMapOf<String, String>()

        val title = overrides.title?.trim()?.takeIf(String::isNotEmpty)?.also { provenance["title"] = "user" }
            ?: current?.title?.takeIf { currentTitle ->
                bestTierVariants.any { normalizeText(it.title) == normalizeText(currentTitle) }
            }?.also { provenance["title"] = "current_stable" }
            ?: best.title.also { provenance["title"] = best.sourceVariantId }

        val author = overrides.author?.trim()?.takeIf(String::isNotEmpty)?.also { provenance["author"] = "user" }
            ?: consensus(bestTierVariants.mapNotNull { it.author }).also {
                if (it != null) provenance["author"] = "consensus"
            }
            ?: best.author?.also { provenance["author"] = best.sourceVariantId }

        val artist = overrides.artist?.trim()?.takeIf(String::isNotEmpty)?.also { provenance["artist"] = "user" }
            ?: consensus(bestTierVariants.mapNotNull { it.artist }).also {
                if (it != null) provenance["artist"] = "consensus"
            }
            ?: best.artist?.also { provenance["artist"] = best.sourceVariantId }

        val description = overrides.description?.trim()?.takeIf(String::isNotEmpty)?.also { provenance["description"] = "user" }
            ?: bestTierVariants.mapNotNull { v ->
                v.description?.trim()?.takeIf(String::isNotEmpty)?.let { v to it }
            }.maxByOrNull { (_, text) -> text.length }
                ?.let { (v, text) -> provenance["description"] = v.sourceVariantId; text }
            ?: ranked.mapNotNull { v ->
                v.description?.trim()?.takeIf(String::isNotEmpty)?.let { v to it }
            }.maxByOrNull { (_, text) -> text.length }
                ?.let { (v, text) -> provenance["description"] = v.sourceVariantId; text }

        val cover = overrides.coverUrl?.trim()?.takeIf(String::isNotEmpty)?.also { provenance["cover"] = "user" }
            ?: bestTierVariants.firstNotNullOfOrNull { v ->
                v.coverUrl?.trim()?.takeIf(String::isNotEmpty)?.let { v to it }
            }?.let { (v, url) -> provenance["cover"] = v.sourceVariantId; url }
            ?: ranked.firstNotNullOfOrNull { v ->
                v.coverUrl?.trim()?.takeIf(String::isNotEmpty)?.let { v to it }
            }?.let { (v, url) -> provenance["cover"] = v.sourceVariantId; url }

        val genres = usable.flatMap { it.genres }.map(String::trim).filter(String::isNotEmpty).toSet()
        provenance["genres"] = "union"

        return CanonicalMetadata(title, author, artist, description, genres, cover, provenance)
    }

    private fun languageTier(language: String, prefs: List<String>): Int {
        val normalized = normalizeLanguage(language)
        return prefs.indexOf(normalized).takeIf { it >= 0 } ?: Int.MAX_VALUE
    }

    private fun completeness(v: MetadataVariant): Int = listOf(
        v.author, v.artist, v.description, v.coverUrl,
    ).count { !it.isNullOrBlank() } + if (v.genres.isNotEmpty()) 1 else 0

    private fun consensus(values: List<String>): String? {
        if (values.isEmpty()) return null
        val groups = values.groupBy(::normalizeText)
        val winner = groups.entries.maxWithOrNull(
            compareBy<Map.Entry<String, List<String>>> { it.value.size }.thenBy { it.key },
        )
        return winner?.value?.firstOrNull()
    }

    private fun normalizeLanguage(value: String): String = when (value.trim().lowercase()) {
        "pt-br", "pt_br", "ptbr", "br" -> "pt-br"
        "pt", "pt-pt", "pt_pt" -> "pt"
        "en", "en-us", "en_us", "en-gb", "en_gb" -> "en"
        "ja", "jp", "jpn" -> "ja"
        "ko", "kr", "kor" -> "ko"
        "zh", "zh-cn", "zh_cn", "zh-tw", "zh_tw", "cn" -> "zh"
        else -> value.trim().lowercase()
    }

    private fun normalizeText(value: String): String =
        Normalizer.normalize(value.trim().lowercase(), Normalizer.Form.NFKD)
            .replace(Regex("\\p{M}+"), "")
            .replace(Regex("[^\\p{L}\\p{N}]+"), " ")
            .trim()
}
