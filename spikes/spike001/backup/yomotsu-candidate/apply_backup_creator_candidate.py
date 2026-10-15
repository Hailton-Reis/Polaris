#!/usr/bin/env python3
"""Recreate the source-only, non-production BackupCreator.kt integration patch.

Only an exact pinned Yomotsu BackupCreator.kt is accepted. No checkout is
modified; creates one new output file, and refuses to overwrite. This patch
alone is NOT Android-ready (restorer + real ProtoBuf must be completed).
"""
import argparse
import hashlib
from pathlib import Path

PINNED_BLOB = "98036c09002b6058a36520a82ac889fbaa9e93cb"
REPLACEMENTS = (
    ("                // Delete older backups\n                dir?.listFiles { _, filename -> FILENAME_REGEX.matches(filename) }\n                    .orEmpty()\n                    .sortedByDescending { it.name }\n                    .drop(MAX_AUTO_BACKUPS - 1)\n                    .forEach { it.delete() }\n\n", ""),
    ("            // Make sure it's a valid backup file (only if readable)\n            runCatching {\n                BackupFileValidator(context).validate(fileUri)\n            }.onFailure { e ->\n                logcat(LogPriority.WARN, e) { \"Validação de backup ignorada: ${e.message}\" }\n            }", "            // For a multifonte archive the validator is a mandatory gate:\n            // never report a successful incomplete or invalid backup.\n            if (polarisBundle != null) {\n                BackupFileValidator(context).validate(fileUri)\n            } else {\n                // Preserve existing Yomotsu handling for legacy backups.\n                runCatching {\n                    BackupFileValidator(context).validate(fileUri)\n                }.onFailure { e ->\n                    logcat(LogPriority.WARN, e) { \"Validação de backup ignorada: ${e.message}\" }\n                }\n            }"),
    ("            if (isAutoBackup) {\n                backupPreferences.lastAutoBackupTimestamp.set(Clock.System.now().toEpochMilliseconds())\n            }", "            if (isAutoBackup) {\n                // Rotate only AFTER new backup bytes have been written and\n                // validated; a failed Polaris export must keep older backups.\n                val dir = UniFile.fromUri(context, uri)\n                dir?.listFiles { _, filename -> FILENAME_REGEX.matches(filename) }\n                    .orEmpty()\n                    .sortedByDescending { it.name }\n                    .drop(MAX_AUTO_BACKUPS)\n                    .forEach { it.delete() }\n                backupPreferences.lastAutoBackupTimestamp.set(Clock.System.now().toEpochMilliseconds())\n            }"),
    (
        "import eu.kanade.tachiyomi.data.backup.models.BackupSourcePreferences\n",
        "import eu.kanade.tachiyomi.data.backup.models.BackupSourcePreferences\n"
        "import polaris.spike001.backup.yomotsu.PolarisYomotsuBackupExporter\n"
        "import polaris.spike001.backup.uuid.YomotsuMergedWorkUuidStore\n"
        "import tachiyomi.domain.manga.repository.MangaMergeRepository\n",
    ),
    (
        "    private val mangaBackupCreator: MangaBackupCreator = MangaBackupCreator(),\n",
        "    private val mangaBackupCreator: MangaBackupCreator = MangaBackupCreator(),\n"
        "    private val polarisBackupExporter: PolarisYomotsuBackupExporter = PolarisYomotsuBackupExporter(\n"
        "        mangaRepository,\n"
        "        Injekt.get<MangaMergeRepository>(),\n"
        "        YomotsuMergedWorkUuidStore(mangaRepository),\n"
        "        mangaBackupCreator,\n"
        "    ),\n",
    ),
    (
        "            val backupManga = backupMangas(getFavorites.await() + nonFavoriteManga, options)\n",
        "            val selectedManga = getFavorites.await() + nonFavoriteManga\n"
        "            val backupManga = backupMangas(selectedManga, options)\n"
        "            // Fail closed if any source child is missing or a virtual link\n"
        "            // changed while full per-source chapters/history were copied.\n"
        "            val polarisBundle = polarisBackupExporter.collect(selectedManga, backupManga, options)\n",
    ),
    (
        "                backupSources = backupSources(backupManga),\n",
        "                // Supplemental source mangas need source mappings too.\n"
        "                backupSources = backupSources(backupManga + polarisBundle?.supplementalManga.orEmpty()),\n",
    ),
    (
        "                backupSourcePreferences = backupSourcePreferences(options),\n",
        "                backupSourcePreferences = backupSourcePreferences(options),\n"
        "                polaris = polarisBundle,\n",
    ),
)


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def render(source: bytes) -> str:
    if git_blob_sha(source) != PINNED_BLOB:
        raise ValueError("Not the pinned Yomotsu BackupCreator.kt; refuse to patch")
    text = source.decode("utf-8")
    for original, replacement in REPLACEMENTS:
        if text.count(original) != 1:
            raise ValueError("Pinned BackupCreator anchor not unique")
        text = text.replace(original, replacement)
    return text


def stage(pinned: Path, output: Path) -> Path:
    content = render(pinned.read_bytes())
    if output.exists():
        raise FileExistsError("Output exists; refusing to overwrite")
    if not output.parent.is_dir():
        raise FileNotFoundError("Create the separate staging directory first")
    output.write_text(content, encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pinned", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(stage(args.pinned, args.output))
    print("PINNED_YOMOTSU_BACKUP_CREATOR_STAGE_ONLY_NOT_ANDROID_RUNTIME")


if __name__ == "__main__":
    main()
