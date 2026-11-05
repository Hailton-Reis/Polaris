pluginManagement {
 repositories { google(); mavenCentral(); gradlePluginPortal() }
 resolutionStrategy { eachPlugin { if (requested.id.id == "com.android.application") useModule("com.android.tools.build:gradle:9.3.1") } }
}
dependencyResolutionManagement { repositories { google(); mavenCentral() } }
rootProject.name = "PolarisOcrBench"
include(":app")
