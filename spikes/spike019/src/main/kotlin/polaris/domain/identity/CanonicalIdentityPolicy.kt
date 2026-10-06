package polaris.domain.identity

import java.util.UUID

@JvmInline
value class CanonicalWorkKey(val value: String) {
    init {
        require(value.matches(Regex("[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"))) {
            "Canonical work key must be a normalized UUID"
        }
    }

    override fun toString(): String = value
}

data class CanonicalIdentity(
    val stableKey: CanonicalWorkKey,
    val preferredTitle: String,
    val externalIds: Map<String, String> = emptyMap(),
)

object CanonicalIdentityPolicy {
    fun create(preferredTitle: String, newUuid: () -> UUID = UUID::randomUUID): CanonicalIdentity {
        require(preferredTitle.isNotBlank())
        return CanonicalIdentity(
            stableKey = CanonicalWorkKey(newUuid().toString().lowercase()),
            preferredTitle = preferredTitle.trim(),
        )
    }

    fun rename(identity: CanonicalIdentity, preferredTitle: String): CanonicalIdentity {
        require(preferredTitle.isNotBlank())
        return identity.copy(preferredTitle = preferredTitle.trim())
    }

    fun attachExternalId(identity: CanonicalIdentity, namespace: String, value: String): CanonicalIdentity {
        require(namespace.isNotBlank() && value.isNotBlank())
        return identity.copy(
            externalIds = identity.externalIds + (namespace.trim().lowercase() to value.trim()),
        )
    }

    fun translationScopeKey(identity: CanonicalIdentity): String = "polaris:${identity.stableKey.value}"
}
