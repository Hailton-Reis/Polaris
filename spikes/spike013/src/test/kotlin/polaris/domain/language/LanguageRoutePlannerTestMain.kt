package polaris.domain.language

fun main() {
    run {
        val route = LanguageRoutePlanner.plan(
            LanguageRouteRequest(originalLanguage = "ko"),
        )
        check(route == listOf("pt-br", "pt", "en", "ko")) { route.toString() }
    }

    run {
        val route = LanguageRoutePlanner.plan(
            LanguageRouteRequest(originalLanguage = "en"),
        )
        check(route == listOf("pt-br", "pt", "en")) { route.toString() }
    }

    run {
        val route = LanguageRoutePlanner.plan(
            LanguageRouteRequest(
                originalLanguage = "KO",
                extraFallbackLanguages = listOf("zh-CN", "en-US"),
            ),
        )
        check(route == listOf("pt-br", "pt", "en", "ko", "zh")) { route.toString() }
    }

    run {
        val route = LanguageRoutePlanner.plan(
            LanguageRouteRequest(
                targetLanguage = "en",
                bridgeLanguages = emptyList(),
                originalLanguage = "ja",
            ),
        )
        check(route == listOf("en", "ja")) { route.toString() }
    }

    println("SPIKE013_LANGUAGE_ROUTE_TESTS_PASS")
}
