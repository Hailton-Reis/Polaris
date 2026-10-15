package kotlinx.serialization.json
sealed class JsonElement
class JsonPrimitive(val content:String, val isString:Boolean=true):JsonElement()
class JsonObject(private val elements:Map<String,JsonElement>):JsonElement(),Map<String,JsonElement> by elements
