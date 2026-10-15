plugins {
    kotlin("jvm") version "2.4.10"
}

repositories {
    mavenCentral()
}

kotlin {
    jvmToolchain(21)
}

// Self-contained host compilation of actual backup candidate sources alongside
// explicit stub types. Crucially none of these source directories may be
// pulled into domain-lab or Android production: they contain test-only stubs.
sourceSets {
    test {
        kotlin.srcDirs(
            "../spike001/backup",
            "../spike001/backup/proto-candidate",
            "../spike001/backup/proto-candidate/host-tests",
            "../spike001/backup/uuid-candidate",
            "../spike001/backup/uuid-candidate/host-tests",
        )
        // This tree also contains a separate Yomotsu adapter host lab
        // with differently shaped API doubles. Never compile both together.
        kotlin.exclude("**/yomotsu-candidate/**", "**/restore-candidate/**")
    }
}

fun backupMain(name: String, mainClassName: String) =
    tasks.register<JavaExec>(name) {
        group = "verification"
        description = "Host-only backup contract test; NOT Android runtime"
        dependsOn(tasks.testClasses)
        classpath = sourceSets["test"].runtimeClasspath
        mainClass.set(mainClassName)
    }

val backupRestore = backupMain("backupRestore", "polaris.spike001.backup.MergedBackupRestorePlannerTestKt")
val backupExport = backupMain("backupExport", "polaris.spike001.backup.MergedBackupExportPlannerTestKt")
val backupProtoModel = backupMain("backupProtoModel", "eu.kanade.tachiyomi.data.backup.models.BackupPolarisBundleContractTestKt")
val backupProtoBuilder = backupMain("backupProtoBuilder", "polaris.spike001.backup.BackupPolarisBundleBuilderTestKt")
val backupUuidStore = backupMain("backupUuidStore", "polaris.spike001.backup.uuid.YomotsuMergedWorkUuidStoreTestKt")

tasks.register("checkBackup") {
    group = "verification"
    description = "Run five independently compiled backup-host test mains (102 scenarios)"
    dependsOn(backupRestore, backupExport, backupProtoModel, backupProtoBuilder, backupUuidStore)
}
