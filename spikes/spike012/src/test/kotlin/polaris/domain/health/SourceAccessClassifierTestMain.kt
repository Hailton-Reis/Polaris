package polaris.domain.health

fun main() {
    run {
        check(SourceAccessClassifier.classify(SourceRequestObservation(RequestFailureCategory.CANCELLED)) == null)
    }

    run {
        val event = SourceAccessClassifier.classify(
            SourceRequestObservation(
                failureCategory = RequestFailureCategory.HTTP,
                httpStatus = 403,
                challengeDetected = true,
            ),
        )
        check(event?.kind == FailureKind.CHALLENGE)
    }

    run {
        val event = SourceAccessClassifier.classify(
            SourceRequestObservation(
                failureCategory = RequestFailureCategory.HTTP,
                httpStatus = 401,
                hadAuthenticatedSession = true,
            ),
        )
        check(event?.kind == FailureKind.AUTH_EXPIRED)
    }

    run {
        val event = SourceAccessClassifier.classify(
            SourceRequestObservation(
                failureCategory = RequestFailureCategory.HTTP,
                httpStatus = 429,
                retryAfterMs = 90_000,
            ),
        )
        check(event?.kind == FailureKind.RATE_LIMIT)
        check(event?.retryAfterMs == 90_000L)
    }

    run {
        val ordinary404 = SourceAccessClassifier.classify(
            SourceRequestObservation(
                failureCategory = RequestFailureCategory.HTTP,
                httpStatus = 404,
                endpointRepresentsWholeSource = false,
            ),
        )
        check(ordinary404 == null)

        val source404 = SourceAccessClassifier.classify(
            SourceRequestObservation(
                failureCategory = RequestFailureCategory.HTTP,
                httpStatus = 404,
                endpointRepresentsWholeSource = true,
            ),
        )
        check(source404?.kind == FailureKind.SOURCE_REMOVED)
    }

    run {
        val event = SourceAccessClassifier.classify(
            SourceRequestObservation(
                failureCategory = RequestFailureCategory.PARSE_OR_CONTRACT,
            ),
        )
        check(event?.kind == FailureKind.PARSE_OR_CONTRACT)
    }

    println("SPIKE012_SOURCE_ACCESS_CLASSIFIER_TESTS_PASS")
}
