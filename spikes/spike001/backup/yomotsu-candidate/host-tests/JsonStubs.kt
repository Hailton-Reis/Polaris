package kotlinx.serialization.json
sealed class JsonElement
class JsonPrimitive(val content: String, val isString: Boolean = true) : JsonElement()
class JsonObject(private val contents: Map<String, JsonElement> = emptyMap()) : JsonElement(), Map<String, JsonElement> by contents
