package polaris.domain.matching

import java.text.Normalizer
import java.util.Locale

object TitleNormalizer {
    fun normalize(value: String): String {
        val decomposed = Normalizer.normalize(value, Normalizer.Form.NFKD)
        return decomposed
            .lowercase(Locale.ROOT)
            .replace(Regex("\\p{M}+"), "")
            .replace("&", " and ")
            .replace(Regex("[^\\p{L}\\p{N}]+"), " ")
            .trim()
            .replace(Regex("\\s+"), " ")
    }

    fun similarity(a: String, b: String): Double {
        val left = normalize(a)
        val right = normalize(b)
        if (left.isEmpty() || right.isEmpty()) return 0.0
        if (left == right) return 1.0

        val distance = levenshtein(left, right)
        val maxLength = maxOf(left.length, right.length).coerceAtLeast(1)
        val editSimilarity = 1.0 - distance.toDouble() / maxLength

        val tokenSimilarity = jaccard(tokens(left), tokens(right))
        return maxOf(editSimilarity, tokenSimilarity)
    }

    fun tokens(value: String): Set<String> = normalize(value)
        .split(' ')
        .asSequence()
        .filter { it.length >= 2 }
        .toSet()

    fun jaccard(left: Set<String>, right: Set<String>): Double {
        if (left.isEmpty() || right.isEmpty()) return 0.0
        val intersection = left.intersect(right).size
        val union = left.union(right).size
        return if (union == 0) 0.0 else intersection.toDouble() / union
    }

    private fun levenshtein(a: String, b: String): Int {
        if (a == b) return 0
        if (a.isEmpty()) return b.length
        if (b.isEmpty()) return a.length

        var previous = IntArray(b.length + 1) { it }
        var current = IntArray(b.length + 1)

        for (i in a.indices) {
            current[0] = i + 1
            for (j in b.indices) {
                val substitution = previous[j] + if (a[i] == b[j]) 0 else 1
                val insertion = current[j] + 1
                val deletion = previous[j + 1] + 1
                current[j + 1] = minOf(substitution, insertion, deletion)
            }
            val swap = previous
            previous = current
            current = swap
        }
        return previous[b.length]
    }
}
