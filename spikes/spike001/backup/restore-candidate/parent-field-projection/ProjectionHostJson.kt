package kotlinx.serialization.json
sealed interface JsonElement
class JsonPrimitive(val content:String):JsonElement { override fun equals(other:Any?)=other is JsonPrimitive&&other.content==content; override fun hashCode()=content.hashCode(); override fun toString()="\"$content\"" }
class JsonObject(map:Map<String,JsonElement>): Map<String,JsonElement> by map, JsonElement { override fun toString()= entries.joinToString(",", "{", "}"){(k,v)->"\"$k\":$v"} }
