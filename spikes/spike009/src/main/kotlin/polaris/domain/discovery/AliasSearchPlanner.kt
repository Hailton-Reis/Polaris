package polaris.domain.discovery

import polaris.domain.canonical.SourceHealthSnapshot

data class WorkAlias(
    val value: String,
    val language: String? = null,
    val confidence: Double = 1.0,
)

data class DiscoveryIdentity(
    val canonicalTitle: String,
    val originalLanguage: String? = null,
    val aliases: List<WorkAlias> = emptyList(),
)

data class DiscoverySource(
    val sourceId: Long,
    val language: String,
    val health: SourceHealthSnapshot,
)

data class SourceSearchTask(
    val sourceId: Long,
    val sourceLanguage: String,
    val queries: List<String>,
)

class AliasSearchPlanner(
    private val maxQueriesPerSource: Int = 2,
) {
    fun plan(
        identity: DiscoveryIdentity,
        sources: List<DiscoverySource>,
        nowEpochMs: Long,
    ): List<SourceSearchTask> {
        require(maxQueriesPerSource >= 1)

        return sources
            .asSequence()
            .filter { it.health.isUsable(nowEpochMs) }
            .map { source ->
                val language = normalizeLanguage(source.language)
                val matchingAliases = identity.aliases
                    .asSequence()
                    .filter { alias ->
                        alias.language == null || normalizeLanguage(alias.language) == language
                    }
                    .sortedByDescending { it.confidence }
                    .map { it.value.trim() }
                    .filter(String::isNotBlank)
                    .toList()

                val originalAliases = if (
                    identity.originalLanguage != null &&
                    normalizeLanguage(identity.originalLanguage) == language
                ) {
                    identity.aliases
                        .filter { it.language != null && normalizeLanguage(it.language) == language }
                        .sortedByDescending { it.confidence }
                        .map { it.value.trim() }
                } else {
                    emptyList()
                }

                val queries = (matchingAliases + originalAliases + identity.canonicalTitle)
                    .filter(String::isNotBlank)
                    .distinctBy(::normalizeQuery)
                    .take(maxQueriesPerSource)

                SourceSearchTask(
                    sourceId = source.sourceId,
                    sourceLanguage = source.language,
                    queries = queries,
                )
            }
            .filter { it.queries.isNotEmpty() }
            .toList()
    }

    private fun normalizeQuery(value: String): String =
        value.lowercase()
            .replace(Regex("[^\\p{L}\\p{N}]+"), " ")
            .trim()
            .replace(Regex("\\s+"), " ")

    private fun normalizeLanguage(language: String): String = when (language.trim().lowercase()) {
        "pt-br", "pt_br", "ptbr", "br" -> "pt-br"
        "pt", "pt-pt", "pt_pt" -> "pt"
        "en", "en-us", "en_us", "en-gb", "en_gb" -> "en"
        "ja", "jp", "jpn" -> "ja"
        "ko", "kr", "kor" -> "ko"
        "zh", "zh-cn", "zh_cn", "zh-tw", "zh_tw", "cn" -> "zh"
        else -> language.trim().lowercase()
    }
}
