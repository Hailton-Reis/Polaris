package polaris.domain.cache

fun main() {
    val page = "same-page-image-bytes".encodeToByteArray()
    val a = TranslationArtifactKey.fromBytes(page, "pt-BR", "ocr-v1", "gemini", "model-a", 3, 1)
    val b = TranslationArtifactKey.fromBytes(page, "pt_br", "ocr-v1", "GEMINI", "model-a", 3, 1)
    check(a.contentSha256 == b.contentSha256)
    check(a.stableKey() == b.stableKey())

    val changedGlossary = b.copy(glossaryRevision = 4)
    check(changedGlossary.stableKey() != b.stableKey())

    val changedModel = b.copy(translatorModel = "model-b")
    check(changedModel.stableKey() != b.stableKey())

    val differentPage = TranslationArtifactKey.fromBytes("other-page".encodeToByteArray(), "pt-BR", "ocr-v1", "gemini", "model-a", 3, 1)
    check(differentPage.stableKey() != a.stableKey())

    println("SPIKE015_TRANSLATION_ARTIFACT_KEY_TESTS_PASS")
}
