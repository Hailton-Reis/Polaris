plugins {
    kotlin("jvm") version "2.4.10"
}

repositories {
    mavenCentral()
}

kotlin {
    jvmToolchain(21)
}

dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.10.2")
}

sourceSets {
    main {
        kotlin.srcDirs(
            "../host-tests",
            "../new-files/domain/src/main/java/tachiyomi/domain/chapter/interactor",
            "../new-files/domain/src/main/java/tachiyomi/domain/manga/model",
            "../new-files/domain/src/main/java/tachiyomi/domain/source/model",
        )
    }
}

tasks.register<JavaExec>("hostInvariants") {
    group = "verification"
    description = "Compile and verify the real staged Spike-001 chapter aggregation Kotlin classes"
    dependsOn(tasks.classes)
    classpath = sourceSets["main"].runtimeClasspath
    mainClass.set("polaris.spike001.host.Spike001HostTestKt")
}

tasks.register("checkHost") {
    group = "verification"
    dependsOn(tasks.named("hostInvariants"))
}
