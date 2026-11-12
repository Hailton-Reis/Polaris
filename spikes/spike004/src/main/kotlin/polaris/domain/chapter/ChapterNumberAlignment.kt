package polaris.domain.chapter

import kotlin.math.abs

data class ChapterNumberOffset(
    /** Add this value to candidate-source numbers to align with the reference source. */
    val offset: Double,
    val matchedCount: Int,
    val overlapRatio: Double,
)

object ChapterNumberAlignment {
    fun detectOffset(
        referenceNumbers: Collection<Double>,
        candidateNumbers: Collection<Double>,
        minMatches: Int = 8,
        minOverlapRatio: Double = 0.70,
    ): ChapterNumberOffset? {
        val reference = referenceNumbers.filter(::usableNumber).map(::roundHalf).toSet()
        val candidate = candidateNumbers.filter(::usableNumber).map(::roundHalf).toSet()
        if (reference.isEmpty() || candidate.isEmpty()) return null

        val denominator = minOf(reference.size, candidate.size).coerceAtLeast(1)
        val offsets = generateSequence(-5.0) { previous ->
            (previous + 0.5).takeIf { it <= 5.0 }
        }.toList()

        val best = offsets.map { offset ->
            val shifted = candidate.mapTo(mutableSetOf()) { roundHalf(it + offset) }
            val matches = shifted.intersect(reference).size
            ChapterNumberOffset(
                offset = offset,
                matchedCount = matches,
                overlapRatio = matches.toDouble() / denominator,
            )
        }.maxWithOrNull(
            compareBy<ChapterNumberOffset> { it.overlapRatio }
                .thenBy { it.matchedCount }
                .thenByDescending { -abs(it.offset) },
        ) ?: return null

        return best.takeIf {
            it.matchedCount >= minMatches &&
                it.overlapRatio >= minOverlapRatio &&
                (it.offset == 0.0 || it.overlapRatio >= 0.80)
        }
    }

    private fun usableNumber(value: Double): Boolean = value.isFinite() && value >= 0.0
    private fun roundHalf(value: Double): Double = kotlin.math.round(value * 2.0) / 2.0
}
