package polaris.domain.metadata

fun main() {
    val resolver = CanonicalMetadataResolver()
    val en = MetadataVariant(
        sourceVariantId = "en",
        language = "en",
        title = "The Beginning After the End",
        author = "TurtleMe",
        description = "Long English description",
        coverUrl = "en.jpg",
        genres = setOf("Action", "Fantasy"),
        lastUpdatedEpochMs = 20,
    )
    val pt = MetadataVariant(
        sourceVariantId = "pt",
        language = "pt-BR",
        title = "O Começo Depois do Fim",
        author = "TurtleMe",
        description = "Descrição PT",
        coverUrl = "pt.jpg",
        genres = setOf("Ação", "Fantasia"),
        lastUpdatedEpochMs = 10,
    )

    run {
        val m = resolver.resolve(listOf(en, pt), listOf("pt-BR", "en"))
        check(m.title == "O Começo Depois do Fim")
        check(m.coverUrl == "pt.jpg")
        check(m.author == "TurtleMe")
    }

    run {
        val current = CanonicalMetadata(
            "O Começo Depois do Fim", null, null, null, emptySet(), null, emptyMap(),
        )
        val newerPt = pt.copy(sourceVariantId = "pt2", title = "O Começo Após o Fim", lastUpdatedEpochMs = 30)
        val m = resolver.resolve(listOf(pt, newerPt, en), listOf("pt-BR", "en"), current = current)
        check(m.title == "O Começo Depois do Fim")
        check(m.provenance["title"] == "current_stable")
    }

    run {
        val m = resolver.resolve(
            listOf(en, pt),
            listOf("pt-BR", "en"),
            overrides = CanonicalMetadataOverrides(title = "TBATE", coverUrl = "user.jpg"),
        )
        check(m.title == "TBATE")
        check(m.coverUrl == "user.jpg")
        check(m.provenance["title"] == "user")
    }

    run {
        val blockedPt = pt.copy(usable = false)
        val m = resolver.resolve(listOf(en, blockedPt), listOf("pt-BR", "en"))
        check(m.title == "The Beginning After the End")
    }

    println("SPIKE023_CANONICAL_METADATA_TESTS_PASS")
}
