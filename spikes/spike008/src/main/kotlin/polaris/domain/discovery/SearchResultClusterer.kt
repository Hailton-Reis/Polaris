package polaris.domain.discovery

import polaris.domain.matching.AutomaticWorkMatcher
import polaris.domain.matching.WorkCandidate
import polaris.domain.matching.WorkMatchDecision
import polaris.domain.matching.WorkMatchResult

data class SearchResultCluster(
    val members: List<WorkCandidate>,
)

data class SemanticReviewPair(
    val left: WorkCandidate,
    val right: WorkCandidate,
    val match: WorkMatchResult,
)

data class SearchClusteringResult(
    val clusters: List<SearchResultCluster>,
    val semanticReviewPairs: List<SemanticReviewPair>,
)

class SearchResultClusterer(
    private val matcher: AutomaticWorkMatcher = AutomaticWorkMatcher(),
) {
    fun cluster(candidates: List<WorkCandidate>): SearchClusteringResult {
        if (candidates.isEmpty()) return SearchClusteringResult(emptyList(), emptyList())

        val parent = IntArray(candidates.size) { it }
        val reviewPairs = mutableListOf<SemanticReviewPair>()

        fun find(index: Int): Int {
            var cursor = index
            while (parent[cursor] != cursor) {
                parent[cursor] = parent[parent[cursor]]
                cursor = parent[cursor]
            }
            return cursor
        }

        fun union(a: Int, b: Int) {
            val rootA = find(a)
            val rootB = find(b)
            if (rootA != rootB) parent[rootB] = rootA
        }

        for (leftIndex in candidates.indices) {
            for (rightIndex in leftIndex + 1 until candidates.size) {
                val left = candidates[leftIndex]
                val right = candidates[rightIndex]

                // Results from the same exact source/work key are duplicates from discovery,
                // not independent evidence.
                if (left.sourceId == right.sourceId && left.sourceWorkKey == right.sourceWorkKey) {
                    union(leftIndex, rightIndex)
                    continue
                }

                val match = matcher.compare(left, right)
                when (match.decision) {
                    WorkMatchDecision.AUTO_MATCH -> union(leftIndex, rightIndex)
                    WorkMatchDecision.REVIEW -> if (match.shouldAskSemanticProvider) {
                        reviewPairs += SemanticReviewPair(left, right, match)
                    }
                    WorkMatchDecision.DIFFERENT -> Unit
                }
            }
        }

        val grouped = candidates.indices
            .groupBy(::find)
            .values
            .map { indexes ->
                SearchResultCluster(
                    members = indexes
                        .map(candidates::get)
                        .distinctBy { it.sourceId to it.sourceWorkKey },
                )
            }
            .sortedByDescending { it.members.size }

        return SearchClusteringResult(
            clusters = grouped,
            semanticReviewPairs = reviewPairs.distinctBy {
                setOf(
                    it.left.sourceId to it.left.sourceWorkKey,
                    it.right.sourceId to it.right.sourceWorkKey,
                )
            },
        )
    }
}
