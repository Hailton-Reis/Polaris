package kotlinx.serialization.json

sealed class JsonElement
data class JsonPrimitive(val content: String, val isString: Boolean = true) : JsonElement()
class JsonObject(private val items: Map<String, JsonElement> = emptyMap()) : JsonElement(), Map<String, JsonElement> by items

// This stand-in is ONLY for a fast host Kotlin API/behavior test, never a
// replacement for the actual kotlinx.serialization.json runtime.
