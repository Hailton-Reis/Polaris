package polaris.spike001.backup.restore

import java.nio.charset.StandardCharsets

private var passed = 0
private fun ok(name: String, fn: () -> Unit) { fn(); passed++; println("PASS $passed $name") }
private fun reject(name: String, fn: () -> Unit) = ok(name) {check(runCatching(fn).isFailure) { "Expected refusal: $name" }}

private data class HostEnvelope(var id: String, var title: String, val chapters: MutableList<String>,
    val links: MutableList<String>, var memo: String)

private class StableHostCodec : PolarisV2EnvelopeCodec<HostEnvelope> {
    override fun encodeCanonical(value: HostEnvelope): ByteArray {
        // Unambiguous lengths, deterministic order, no caller-provided bytes.
        val fields = listOf(value.id, value.title, value.memo) +
            listOf(value.chapters.size.toString()) + value.chapters +
            listOf(value.links.size.toString()) + value.links
        return fields.joinToString("") { "${it.toByteArray(StandardCharsets.UTF_8).size}:$it" }.toByteArray(StandardCharsets.UTF_8)
    }
    override fun decodeCanonical(bytes: ByteArray): HostEnvelope {
        val text = String(bytes, StandardCharsets.UTF_8)
        val fields = mutableListOf<String>()
        var i=0
        while (i<text.length) {
            val colon=text.indexOf(':',i);require(colon>=i)
            val len=text.substring(i,colon).toInt();require(len>=0)
            val start=colon+1;val end=start+len;require(end<=text.length)
            fields+=text.substring(start,end);i=end
        }
        val cc=fields[3].toInt();require(cc>=0)
        val lcIndex=4+cc;val lc=fields[lcIndex].toInt();require(lc>=0)
        require(fields.size==lcIndex+1+lc)
        return HostEnvelope(fields[0],fields[1],fields.subList(4,lcIndex).toMutableList(),
            fields.subList(lcIndex+1,fields.size).toMutableList(),fields[2])
    }
}
private fun e()=HostEnvelope("123e4567-e89b-42d3-a456-426614174000","Manga",
    mutableListOf("ch1","ch2"),mutableListOf("77:/a","98:/b"),"{\"other\":1}")
private val codec=StableHostCodec()
fun main() {
    ok("bind decoded envelope without caller supplied hash") {val a=PolarisV2SnapshotAdmission.fromDecoded(e(),codec);check(a.sha256.length==64);check(a.verifyBeforeTransaction()==a.sha256)}
    ok("repeated readback remains stable") {val a=PolarisV2SnapshotAdmission.fromDecoded(e(),codec);repeat(3){check(a.verifyBeforeTransaction()==a.sha256)}}
    ok("canonical bytes are defensive copies") {val a=PolarisV2SnapshotAdmission.fromDecoded(e(),codec);a.canonicalBytes()[0]=0;check(a.verifyBeforeTransaction()==a.sha256)}
    reject("mutated source title rejected before writing") {val env=e();val a=PolarisV2SnapshotAdmission.fromDecoded(env,codec);env.title="Manga modified";a.verifyBeforeTransaction()}
    reject("mutated source UUID rejected") {val env=e();val a=PolarisV2SnapshotAdmission.fromDecoded(env,codec);env.id="abc";a.verifyBeforeTransaction()}
    reject("chapter removed rejected") {val env=e();val a=PolarisV2SnapshotAdmission.fromDecoded(env,codec);env.chapters.removeAt(0);a.verifyBeforeTransaction()}
    reject("chapter added rejected") {val env=e();val a=PolarisV2SnapshotAdmission.fromDecoded(env,codec);env.chapters.add("third");a.verifyBeforeTransaction()}
    reject("changed chapter order rejected") {val env=e();val a=PolarisV2SnapshotAdmission.fromDecoded(env,codec);env.chapters.reverse();a.verifyBeforeTransaction()}
    reject("changed link url rejected") {val env=e();val a=PolarisV2SnapshotAdmission.fromDecoded(env,codec);env.links[0]="77:/changed";a.verifyBeforeTransaction()}
    reject("removed link rejected") {val env=e();val a=PolarisV2SnapshotAdmission.fromDecoded(env,codec);env.links.removeAt(0);a.verifyBeforeTransaction()}
    reject("new link rejected") {val env=e();val a=PolarisV2SnapshotAdmission.fromDecoded(env,codec);env.links.add("1:/extra");a.verifyBeforeTransaction()}
    reject("memo modified rejected") {val env=e();val a=PolarisV2SnapshotAdmission.fromDecoded(env,codec);env.memo="{}";a.verifyBeforeTransaction()}
    reject("empty encoding forbidden") {PolarisV2SnapshotAdmission.fromDecoded(e(), object:PolarisV2EnvelopeCodec<HostEnvelope> {override fun encodeCanonical(value:HostEnvelope)=byteArrayOf();override fun decodeCanonical(bytes:ByteArray)=e()})}
    reject("nondeterministic codec forbidden") {var n=0;val c=object:PolarisV2EnvelopeCodec<HostEnvelope>{override fun encodeCanonical(value:HostEnvelope):ByteArray=(++n).toString().toByteArray();override fun decodeCanonical(bytes:ByteArray)=e()};PolarisV2SnapshotAdmission.fromDecoded(e(),c)}
    reject("codec changes representation between calls") {var n=0;val c=object:PolarisV2EnvelopeCodec<HostEnvelope>{override fun encodeCanonical(value:HostEnvelope)=codec.encodeCanonical(value).also {n++};override fun decodeCanonical(bytes:ByteArray)=e().also{if(n>2)it.title="changed"}};val a=PolarisV2SnapshotAdmission.fromDecoded(e(),c);a.verifyBeforeTransaction()}
    ok("two independently decoded same envelopes match digest") {val a=PolarisV2SnapshotAdmission.fromDecoded(e(),codec);val b=PolarisV2SnapshotAdmission.fromDecoded(e(),codec);check(a.sha256==b.sha256)}
    ok("changed envelope produces changed digest") {val a=PolarisV2SnapshotAdmission.fromDecoded(e(),codec);val b=PolarisV2SnapshotAdmission.fromDecoded(e().also{it.memo="different"},codec);check(a.sha256!=b.sha256)}
    ok("does not mutate original during admission") {val env=e();val copy=env.copy(chapters=env.chapters.toMutableList(),links=env.links.toMutableList());PolarisV2SnapshotAdmission.fromDecoded(env,codec);check(env==copy)}
    ok("empty chapter list is legal if codec preserves it") {val env=e().also{it.chapters.clear()};val a=PolarisV2SnapshotAdmission.fromDecoded(env,codec);check(a.verifyBeforeTransaction()==a.sha256)}
    ok("empty link list still bound, envelope validation is separate") {val env=e().also{it.links.clear()};val a=PolarisV2SnapshotAdmission.fromDecoded(env,codec);check(a.verifyBeforeTransaction()==a.sha256)}
    println("POLARIS_V2_BOUND_SNAPSHOT_HOST_PASS $passed")
}
