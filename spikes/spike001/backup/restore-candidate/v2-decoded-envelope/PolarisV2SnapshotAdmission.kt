package polaris.spike001.backup.restore

import java.security.MessageDigest

/**
 * Host-portable fail-closed boundary. The codec must be the *real* serializer
 * for the versioned decoded envelope in Android, never arbitrary caller bytes.
 * No SQLite writes or source IDs are allocated by this class.
 */
interface PolarisV2EnvelopeCodec<T : Any> {
    fun encodeCanonical(value: T): ByteArray
    fun decodeCanonical(bytes: ByteArray): T
}

/**
 * An admission captures the exact canonical serialization of a decoded object.
 * It does not accept a caller-supplied digest or a separately supplied payload.
 * A mutable decoded model is re-encoded and rechecked immediately before use.
 */
class PolarisV2SnapshotAdmission<T : Any> private constructor(
    val decoded: T,
    private val original: ByteArray,
    private val codec: PolarisV2EnvelopeCodec<T>,
) {
    val sha256: String = sha256(original)
    val size: Int get() = original.size

    /** Fresh copy; callers cannot overwrite the sealed bytes in place. */
    fun canonicalBytes(): ByteArray = original.copyOf()

    /** Must be invoked at the trusted Android decoder/restore integration. */
    fun verifyBeforeTransaction(): String {
        val current = canonicalize(codec, decoded)
        check(MessageDigest.isEqual(original, current)) { "POLARIS_V2_SNAPSHOT_CHANGED_SINCE_DECODE" }
        return sha256
    }

    companion object {
        private fun sha256(bytes: ByteArray): String = MessageDigest.getInstance("SHA-256")
            .digest(bytes).joinToString("") { "%02x".format(it) }

        private fun <T : Any> canonicalize(codec: PolarisV2EnvelopeCodec<T>, value: T): ByteArray {
            val first = codec.encodeCanonical(value)
            require(first.isNotEmpty()) { "POLARIS_V2_EMPTY_CANONICAL_ENVELOPE" }
            val roundtripped = codec.decodeCanonical(first)
            val second = codec.encodeCanonical(roundtripped)
            check(MessageDigest.isEqual(first, second)) { "POLARIS_V2_UNSTABLE_CODEC" }
            return first
        }

        fun <T : Any> fromDecoded(decoded: T, codec: PolarisV2EnvelopeCodec<T>): PolarisV2SnapshotAdmission<T> {
            return PolarisV2SnapshotAdmission(decoded, canonicalize(codec, decoded).copyOf(), codec)
        }
    }
}
