#!/usr/bin/env python3
"""Stage a protobuf-only Polaris diff against the exact pinned Yomotsu Backup.kt.

Deliberately writes into a NEW output directory, not a live Android checkout.
It does not install the exporter/restorer, nor modify SQLDelight or migrations.
"""
from pathlib import Path
import argparse
import hashlib

PINNED_BACKUP_GIT_BLOB = '0c021d34a8426dc0bd5844b4e00f9c13767610bf'
ANCHOR = '    @ProtoNumber(106) var backupExtensionStores: List<BackupExtensionStore> = emptyList(),\n'
NEW_FIELD = '    // Optional: legacy Yomotsu backups have no field 107.\n    @ProtoNumber(107) var polaris: BackupPolarisBundle? = null,\n'


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def stage(pinned_file: Path, model_file: Path, output_dir: Path) -> tuple[Path, Path]:
    data = pinned_file.read_bytes()
    if blob_sha(data) != PINNED_BACKUP_GIT_BLOB:
        raise ValueError('Pinned Yomotsu Backup.kt blob mismatch; refusing to patch a different API')
    text = data.decode('utf-8')
    if text.count(ANCHOR) != 1 or '@ProtoNumber(107)' in text:
        raise ValueError('Backup.kt anchor missing, repeated or new field already exists')
    model = model_file.read_bytes()
    if b'data class BackupPolarisBundle' not in model or b'fun validateForImport()' not in model:
        raise ValueError('Portable protobuf candidate model missing/invalid')
    if output_dir.exists():
        raise FileExistsError(f'Output path exists; refusing to overwrite: {output_dir}')
    output_dir.mkdir(parents=True)
    patched = output_dir / 'Backup.kt'
    added = output_dir / 'BackupPolarisBundle.kt'
    patched.write_text(text.replace(ANCHOR, ANCHOR + NEW_FIELD), encoding='utf-8')
    added.write_bytes(model)
    return patched, added


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pinned-backup', type=Path, required=True, help='Exact upstream pinned Backup.kt')
    p.add_argument('--output-dir', type=Path, required=True, help='New empty directory for the resulting model files')
    p.add_argument('--candidate-model', type=Path, default=Path(__file__).with_name('BackupPolarisBundle.kt'))
    args = p.parse_args()
    for path in stage(args.pinned_backup, args.candidate_model, args.output_dir):
        print(f'STAGED {path}')
    print('BACKUP_PROTO_CANDIDATE_STAGE_ONLY; NOT_ANDROID_RUNTIME')


if __name__ == '__main__':
    main()
