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
        )
    }
    test {
        kotlin.srcDirs(
            "../spike002/src/test/kotlin",
            "../spike003/src/test/kotlin",
            "../spike004/src/test/kotlin",
        )
    }
}

val spike002 by tasks.registering(JavaExec::class) {
    group = "verification"
    dependsOn(tasks.testClasses)
    classpath = sourceSets["test"].runtimeClasspath
    mainClass.set("polaris.domain.canonical.SourceRankerTestMainKt")
}

val spike003 by tasks.registering(JavaExec::class) {
    group = "verification"
    dependsOn(tasks.testClasses)
    classpath = sourceSets["test"].runtimeClasspath
    mainClass.set("polaris.domain.matching.AutomaticWorkMatcherTestMainKt")
}

val spike004 by tasks.registering(JavaExec::class) {
    group = "verification"
    dependsOn(tasks.testClasses)
    classpath = sourceSets["test"].runtimeClasspath
    mainClass.set("polaris.domain.chapter.CanonicalChapterResolverTestMainKt")
}

tasks.register("checkSpikes") {
    group = "verification"
    dependsOn(spike002, spike003, spike004)
}
