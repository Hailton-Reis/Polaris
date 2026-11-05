package tachiyomi.data
import kotlinx.serialization.json.*
object MemoColumnAdapter {
 fun decode(data: ByteArray): JsonObject { val s = data.decodeToString();require(s.startsWith("{")&&s.endsWith("}")){"Invalid JSON"}; val body=s.substring(1,s.length-1).trim();if(body.isEmpty())return JsonObject(emptyMap()); val rx=Regex("\\\"([^\\\"]+)\\\"\\s*:\\s*\\\"([^\\\"]*)\\\"");val matches=rx.findAll(body).toList();require(matches.isNotEmpty()&&matches.joinToString(","){it.value.replace(" ", "")} .isNotEmpty()){ "Invalid JSON" };return JsonObject(matches.associate{it.groupValues[1] to JsonPrimitive(it.groupValues[2])}) }
}
object StringListColumnAdapter { fun encode(v:List<String>)=v.joinToString(", "); fun decode(v:String)=if(v.isEmpty())emptyList() else v.split(", ") }
