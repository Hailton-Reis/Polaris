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
        val comparisonCache = mutableMapOf<Pair<Int, Int>, WorkMatchResult>()

        fun find(index: Int): Int {
            var cursor = index
            while (parent[cursor] != cursor) {
                parent[cursor] = parent[parent[cursor]]
                cursor = parent[cursor]
            }
            return cursor
        }

        fun comparison(a: Int, b: Int): WorkMatchResult {
            val key = if (a < b) a to b else b to a
            return comparisonCache.getOrPut(key) {
                matcher.compare(candidates[key.first], candidates[key.second])
            }
        }

        fun clusterMembers(root: Int): List<Int> =
            candidates.indices.filter { find(it) == root }

        fun hasHardConflictAcrossClusters(a: Int, b: Int): Boolean {
            val rootA = find(a)
            val rootB = find(b)
            if (rootA == rootB) return false
            val membersA = clusterMembers(rootA)
            val membersB = clusterMembers(rootB)

            return membersA.any { leftIndex ->
                membersB.any { rightIndex ->
                    val left = candidates[leftIndex]
                    val right = candidates[rightIndex]
                    if (left.sourceId == right.sourceId && left.sourceWorkKey == right.sourceWorkKey) {
                        false
                    } else {
                        comparison(leftIndex, rightIndex).evidence.conflictingExternalNamespaces.isNotEmpty()
                    }
                }
            }
        }

        fun unionIfSafe(a: Int, b: Int) {
            val rootA = find(a)
            val rootB = find(b)
            if (rootA == rootB) return
            if (hasHardConflictAcrossClusters(rootA, rootB)) return
            parent[rootB] = rootA
        }

        for (leftIndex in candidates.indices) {
            for (rightIndex in leftIndex + 1 until candidates.size) {
                val left = candidates[leftIndex]
                val right = candidates[rightIndex]

                if (left.sourceId == right.sourceId && left.sourceWorkKey == right.sourceWorkKey) {
                    unionIfSafe(leftIndex, rightIndex)
                    continue
                }

                val match = comparison(leftIndex, rightIndex)
                when (match.decision) {
                    WorkMatchDecision.AUTO_MATCH -> unionIfSafe(leftIndex, rightIndex)
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
