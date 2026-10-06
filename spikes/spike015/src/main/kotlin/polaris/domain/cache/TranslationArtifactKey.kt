package polaris.domain.cache

import java.security.MessageDigest

data class TranslationArtifactKey(
    val contentSha256: String,
    val targetLanguage: String,
    val ocrRevision: String,
    val translatorId: String,
    val translatorModel: String,
    val glossaryRevision: Long,
    val renderRevision: Int,
) {
    init {
        require(contentSha256.matches(Regex("[0-9a-fA-F]{64}")))
        require(glossaryRevision >= 0)
        require(renderRevision >= 0)
    }

    fun stableKey(): String = listOf(
        contentSha256.lowercase(),
        normalizeLanguage(targetLanguage),
        ocrRevision.trim(),
        translatorId.trim().lowercase(),
        translatorModel.trim(),
        glossaryRevision.toString(),
        renderRevision.toString(),
    ).joinToString("\u0000").sha256()

    companion object {
        fun fromBytes(
            bytes: ByteArray,
            targetLanguage: String,
            ocrRevision: String,
            translatorId: String,
            translatorModel: String,
            glossaryRevision: Long,
            renderRevision: Int,
        ) = TranslationArtifactKey(
            contentSha256 = bytes.sha256(),
            targetLanguage = targetLanguage,
            ocrRevision = ocrRevision,
            translatorId = translatorId,
            translatorModel = translatorModel,
            glossaryRevision = glossaryRevision,
            renderRevision = renderRevision,
        )

        private fun normalizeLanguage(value: String): String = when (value.trim().lowercase()) {
            "pt-br", "pt_br", "ptbr", "br" -> "pt-br"
            "pt", "pt-pt", "pt_pt" -> "pt"
            "en", "en-us", "en_us", "en-gb", "en_gb" -> "en"
            "ja", "jp", "jpn" -> "ja"
            "ko", "kr", "kor" -> "ko"
            "zh", "zh-cn", "zh_cn", "zh-tw", "zh_tw", "cn" -> "zh"
            else -> value.trim().lowercase()
        }
    }
}

fun ByteArray.sha256(): String = MessageDigest.getInstance("SHA-256")
    .digest(this)
    .joinToString("") { "%02x".format(it) }

fun String.sha256(): String = encodeToByteArray().sha256()
