import eu.kanade.tachiyomi.data.backup.models.*
fun customize(backup:Backup) {
 backup.backupManga.single().apply{ notes="Nota preservada";initialized=true;memo="{\"sample\":true}".encodeToByteArray();nextUpdate=1700000000500 }
 backup.backupExtensionStores=listOf(BackupExtensionStore("https://example.invalid/repo/index.pb","Repositório sintético",null,"a".repeat(64),"https://example.invalid",null,false,null))
}
fun verifyExtras(backup:Backup) {
 check(backup.backupManga.single().notes=="Nota preservada")
 check(backup.backupManga.single().memo.decodeToString()=="{\"sample\":true}")
 // Polaris currently has no nextUpdate field. Do not claim preservation of unsupported fields.
 backup.backupManga.single().apply{nextUpdate=0;notes="";initialized=false;memo=byteArrayOf(0x7b,0x7d)}
 check(backup.backupExtensionStores.single().signingKey=="a".repeat(64))
 backup.backupExtensionStores=emptyList()
}

fun sampleCategory() = BackupCategory("Favoritos",7,23,1)
