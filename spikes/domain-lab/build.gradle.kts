plugins {
    kotlin("jvm") version "2.4.10"
}

repositories {
    mavenCentral()
}

kotlin {
    jvmToolchain(21)
}

sourceSets {
    main {
        kotlin.srcDirs(
            "../spike002/src/main/kotlin",
            "../spike003/src/main/kotlin",
            "../spike004/src/main/kotlin",
            "../spike005/src/main/kotlin",
            "../spike006/src/main/kotlin",
            "../spike007/src/main/kotlin",
            "../spike008/src/main/kotlin",
            "../spike009/src/main/kotlin",
            "../spike011/src/main/kotlin",
            "../spike012/src/main/kotlin",
            "../spike013/src/main/kotlin",
            "../spike014/src/main/kotlin",
            "../spike015/src/main/kotlin",
            "../spike016/src/main/kotlin",
            "../spike017/src/main/kotlin",
            "../spike018/src/main/kotlin",
        )
    }
    test {
        kotlin.srcDirs(
            "../spike002/src/test/kotlin",
            "../spike003/src/test/kotlin",
            "../spike004/src/test/kotlin",
            "../spike005/src/test/kotlin",
            "../spike006/src/test/kotlin",
            "../spike007/src/test/kotlin",
            "../spike008/src/test/kotlin",
            "../spike009/src/test/kotlin",
            "../spike011/src/test/kotlin",
            "../spike012/src/test/kotlin",
            "../spike013/src/test/kotlin",
            "../spike014/src/test/kotlin",
            "../spike015/src/test/kotlin",
            "../spike016/src/test/kotlin",
            "../spike017/src/test/kotlin",
            "../spike018/src/test/kotlin",
        )
    }
}

fun registerSpikeTask(name: String, mainClassName: String) =
    tasks.register<JavaExec>(name) {
        group = "verification"
        dependsOn(tasks.testClasses)
        classpath = sourceSets["test"].runtimeClasspath
        mainClass.set(mainClassName)
    }

val spike002 = registerSpikeTask("spike002", "polaris.domain.canonical.SourceRankerTestMainKt")
val spike003 = registerSpikeTask("spike003", "polaris.domain.matching.AutomaticWorkMatcherTestMainKt")
val spike004 = registerSpikeTask("spike004", "polaris.domain.chapter.CanonicalChapterResolverTestMainKt")
val spike005 = registerSpikeTask("spike005", "polaris.domain.health.SourceHealthTrackerTestMainKt")
val spike006 = registerSpikeTask("spike006", "polaris.domain.translation.TranslationDecisionPolicyTestMainKt")
val spike007 = registerSpikeTask("spike007", "polaris.domain.open.ChapterOpenPlannerTestMainKt")
val spike008 = registerSpikeTask("spike008", "polaris.domain.discovery.SearchResultClustererTestMainKt")
val spike009 = registerSpikeTask("spike009", "polaris.domain.discovery.AliasSearchPlannerTestMainKt")
val spike011 = registerSpikeTask("spike011", "polaris.domain.semantic.SemanticWorkMatcherTestMainKt")
val spike012 = registerSpikeTask("spike012", "polaris.domain.health.SourceAccessClassifierTestMainKt")
val spike013 = registerSpikeTask("spike013", "polaris.domain.language.LanguageRoutePlannerTestMainKt")
val spike014 = registerSpikeTask("spike014", "polaris.domain.translation.CanonicalTranslationScopeTestMainKt")
val spike015 = registerSpikeTask("spike015", "polaris.domain.cache.TranslationArtifactKeyTestMainKt")
val spike016 = registerSpikeTask("spike016", "polaris.domain.progress.CanonicalProgressPolicyTestMainKt")
val spike017 = registerSpikeTask("spike017", "polaris.domain.diagnostics.SelectionDiagnosticsTestMainKt")
val spike018 = registerSpikeTask("spike018", "polaris.domain.backup.PolarisBackupContractTestMainKt")

tasks.register("checkSpikes") {
    group = "verification"
    dependsOn(
        spike002,
        spike003,
        spike004,
        spike005,
        spike006,
        spike007,
        spike008,
        spike009,
        spike011,
        spike012,
        spike013,
        spike014,
        spike015,
        spike016,
        spike017,
        spike018,
    )
}
