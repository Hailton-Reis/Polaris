package polaris.domain.health

enum class RequestFailureCategory {
    NONE,
    CANCELLED,
    NETWORK,
    TIMEOUT,
    PARSE_OR_CONTRACT,
    SOURCE_REMOVED,
    HTTP,
}

data class SourceRequestObservation(
    val failureCategory: RequestFailureCategory,
    val httpStatus: Int? = null,
    val retryAfterMs: Long? = null,
    val challengeDetected: Boolean = false,
    val authenticationExpected: Boolean = false,
    val hadAuthenticatedSession: Boolean = false,
    val endpointRepresentsWholeSource: Boolean = false,
)

object SourceAccessClassifier {

    fun classify(observation: SourceRequestObservation): SourceAccessEvent.Failure? {
        if (observation.failureCategory == RequestFailureCategory.NONE) return null
        if (observation.failureCategory == RequestFailureCategory.CANCELLED) return null

        if (observation.challengeDetected) {
            return SourceAccessEvent.Failure(FailureKind.CHALLENGE)
        }

        return when (observation.failureCategory) {
            RequestFailureCategory.NETWORK ->
                SourceAccessEvent.Failure(FailureKind.NETWORK)

            RequestFailureCategory.TIMEOUT ->
                SourceAccessEvent.Failure(FailureKind.TIMEOUT)

            RequestFailureCategory.PARSE_OR_CONTRACT ->
                SourceAccessEvent.Failure(FailureKind.PARSE_OR_CONTRACT)

            RequestFailureCategory.SOURCE_REMOVED ->
                SourceAccessEvent.Failure(FailureKind.SOURCE_REMOVED)

            RequestFailureCategory.HTTP -> classifyHttp(observation)

            RequestFailureCategory.NONE,
            RequestFailureCategory.CANCELLED,
            -> null
        }
    }

    private fun classifyHttp(observation: SourceRequestObservation): SourceAccessEvent.Failure? {
        val status = observation.httpStatus ?: return SourceAccessEvent.Failure(FailureKind.NETWORK)

        return when {
            status == 429 -> SourceAccessEvent.Failure(
                kind = FailureKind.RATE_LIMIT,
                retryAfterMs = observation.retryAfterMs,
            )

            status == 401 -> SourceAccessEvent.Failure(
                if (observation.hadAuthenticatedSession) FailureKind.AUTH_EXPIRED else FailureKind.AUTH_REQUIRED,
            )

            status == 403 && observation.authenticationExpected -> SourceAccessEvent.Failure(
                if (observation.hadAuthenticatedSession) FailureKind.AUTH_EXPIRED else FailureKind.AUTH_REQUIRED,
            )

            status in 500..599 -> SourceAccessEvent.Failure(FailureKind.SERVER_5XX)

            status == 404 && observation.endpointRepresentsWholeSource ->
                SourceAccessEvent.Failure(FailureKind.SOURCE_REMOVED)

            // A single manga/chapter endpoint can disappear while the source remains healthy.
            status == 404 -> null

            // Other 4xx responses may be request/content specific. Do not poison source health
            // without a more precise adapter signal.
            status in 400..499 -> null

            else -> null
        }
    }
}
