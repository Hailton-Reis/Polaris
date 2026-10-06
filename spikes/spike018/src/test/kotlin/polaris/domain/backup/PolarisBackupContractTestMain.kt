package polaris.domain.backup

fun main() {
    val stableKey = "123e4567-e89b-12d3-a456-426614174000"
    val work = BackupWork(
        stableKey = stableKey,
        preferredTitle = "The Beginning After the End",
        originalLanguage = "en",
        aliases = listOf(BackupAlias("O Começo Depois do Fim", "pt-BR", provenance = "tracker")),
        externalIds = mapOf("anilist" to "123"),
        variants = listOf(
            BackupSourceVariant(10L, "/tbate", "en", "The Beginning After the End"),
            BackupSourceVariant(20L, "/comeco", "pt-BR", "O Começo Depois do Fim"),
        ),
        chapters = listOf(
            BackupCanonicalChapter(
                number = 84.0,
                kind = "REGULAR",
                read = true,
                bookmarked = false,
                lastVariantHint = BackupVariantHint(10L, "/tbate", "/chapter-84"),
                variants = listOf(BackupChapterVariant(10L, "/tbate", "/chapter-84", "Chapter 84")),
            ),
        ),
    )
    val backup = PolarisBackup(
        exportedAtEpochMs = 1234L,
        works = listOf(work),
        linkOverrides = listOf(
            BackupWorkLinkOverride(
                leftSourceId = 10L,
                leftSourceWorkKey = "/wrong-a",
                rightSourceId = 20L,
                rightSourceWorkKey = "/wrong-b",
                decision = "FORCE_DIFFERENT_WORK",
                createdAtEpochMs = 1200L,
            ),
        ),
    )
    PolarisRestorePolicy.validate(backup)
    check(work.translationScopeKey == "polaris:$stableKey")
    check(backup.linkOverrides.single().decision == "FORCE_DIFFERENT_WORK")

    val duplicate = backup.copy(works = listOf(work.copy(variants = work.variants + work.variants.first())))
    check(runCatching { PolarisRestorePolicy.validate(duplicate) }.isFailure)

    val newer = backup.copy(schemaVersion = PolarisBackup.CURRENT_SCHEMA_VERSION + 1)
    check(runCatching { PolarisRestorePolicy.validate(newer) }.isFailure)

    val invalidOverride = backup.copy(
        linkOverrides = listOf(
            BackupWorkLinkOverride(10L, "/same", 10L, "/same", "FORCE_DIFFERENT_WORK", 1L),
        ),
    )
    check(runCatching { PolarisRestorePolicy.validate(invalidOverride) }.isFailure)

    println("SPIKE018_BACKUP_CONTRACT_TESTS_PASS")
}
