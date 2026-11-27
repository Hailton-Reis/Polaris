from pathlib import Path
import tempfile
import unittest
from package_internal_beta import package, signer_digest, validate_branding, verify_universal_architectures, validate_update_identity
import zipfile
import hashlib
import struct
import zlib
from package_internal_beta import APPLICATION_ID, VERSION, VERSION_CODE, validate_compiled_build, verify_production_classes, dex_class_descriptors


class UniversalPackagingTests(unittest.TestCase):
    required = ['libimagedecoder.so', 'libarchive-jni.so', 'libsqliteJni.so',
                'libmlkit_google_ocr_pipeline.so', 'libtranslate_jni.so', 'liblanguage_id_l2c_jni.so',
                'libonnxruntime.so', 'libonnxruntime4j_jni.so', 'libopencv_java4.so']

    def check(self, abis, missing=None):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'universal.apk'
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('assets/shared.txt', 'one copy')
                for abi in abis:
                    for name in self.required:
                        if (abi, name) != missing:
                            archive.writestr(f'lib/{abi}/{name}', b'fixture')
            with zipfile.ZipFile(path) as archive:
                return verify_universal_architectures(archive)

    def test_both_arm_architectures_share_one_asset_tree(self):
        self.assertEqual({'arm64-v8a', 'armeabi-v7a'}, set(self.check(['arm64-v8a', 'armeabi-v7a'])))

    def test_a_mislabeled_single_architecture_or_accidental_emulator_build_is_rejected(self):
        for abis in [['arm64-v8a'], ['armeabi-v7a'], ['arm64-v8a', 'armeabi-v7a', 'x86_64']]:
            with self.subTest(abis=abis), self.assertRaisesRegex(ValueError, 'exactly ARM32 and ARM64'):
                self.check(abis)

    def test_missing_32_bit_reader_or_ocr_dependency_is_rejected(self):
        for library in ('libonnxruntime.so', 'liblanguage_id_l2c_jni.so'):
            with self.subTest(library=library), self.assertRaisesRegex(ValueError, 'Missing required'):
                self.check(['arm64-v8a', 'armeabi-v7a'], ('armeabi-v7a', library))

class BetaPackagingTests(unittest.TestCase):
    def test_sdk_36_and_37_certificate_formats_are_accepted(self):
        for prefix in ['Signer #1', 'V2 Signer']:
            self.assertEqual('a'*64, signer_digest(f'{prefix}: certificate SHA-256 digest: '+ 'A'*64))

    def test_missing_or_multiple_signers_are_rejected(self):
        for output in ['', 'certificate SHA-256 digest: invalid',
                       'certificate SHA-256 digest: '+ 'a'*64 +'\ncertificate SHA-256 digest: '+ 'b'*64]:
            with self.assertRaises(ValueError):
                signer_digest(output)

    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'beta'
            output.mkdir()
            sentinel = output / 'keep.txt'
            sentinel.write_text('keep')
            with self.assertRaisesRegex(ValueError, 'never replaced'):
                package(Path('unused'), output, Path('unused'), Path('unused'))
            self.assertEqual('keep', sentinel.read_text())


class CompiledBrandingTests(unittest.TestCase):
    resources = """resource 0x7f100003 mipmap/ic_polaris_launcher
resource 0x7f080101 drawable/ic_polaris_foreground
resource 0x7f080102 drawable/ic_polaris_monochrome
resource 0x7f080103 drawable/ic_polaris_logo
resource 0x7f080104 drawable/ic_polaris_splash"""
    manifest = """E: application
 A: http://schemas.android.com/apk/res/android:icon(0x01010002)=@0x7f100003
 A: http://schemas.android.com/apk/res/android:roundIcon(0x0101052c)=@0x7f100003"""

    def test_compiled_polaris_branding_is_accepted(self):
        result = validate_branding("application-label:'Polaris'\napplication-label-pt-BR:'Polaris'",
                                   self.resources, self.manifest)
        self.assertTrue(result['compiled_resources_verified'])

    def test_upstream_label_is_rejected_even_if_apk_filename_says_polaris(self):
        for label in ["application-label:'Yomotsu'", "application-label:'Polaris'\napplication-label-pt-BR:'Yomotsu'", ""]:
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, 'label'):
                validate_branding(label, self.resources, self.manifest)

    def test_wrong_round_icon_or_missing_splash_is_rejected(self):
        bad_round = self.manifest.replace('roundIcon(0x0101052c)=@0x7f100003',
                                         'roundIcon(0x0101052c)=@0x7f100001')
        with self.assertRaisesRegex(ValueError, 'roundIcon'):
            validate_branding("application-label:'Polaris'", self.resources, bad_round)
        with self.assertRaisesRegex(ValueError, 'splash'):
            validate_branding("application-label:'Polaris'", self.resources.replace('drawable/ic_polaris_splash',
                                                                                   'drawable/ic_yomotsu_splash'),
                              self.manifest)


    def test_reward_launcher_aliases_do_not_replace_application_icons(self):
        manifest = self.manifest + "\n E: activity-alias (line=80)\n  A: http://schemas.android.com/apk/res/android:icon(0x01010002)=@0x7f100009\n  A: http://schemas.android.com/apk/res/android:roundIcon(0x0101052c)=@0x7f100009"
        self.assertTrue(validate_branding("application-label:'Polaris'", self.resources, manifest)['compiled_resources_verified'])

    def test_correct_alias_cannot_hide_missing_application_round_icon(self):
        manifest = self.manifest.split('\n A: http://schemas.android.com/apk/res/android:roundIcon')[0]
        manifest += "\n E: activity-alias\n  A: http://schemas.android.com/apk/res/android:roundIcon(0x0101052c)=@0x7f100003"
        with self.assertRaisesRegex(ValueError, 'roundIcon'):
            validate_branding("application-label:'Polaris'", self.resources, manifest)

    def test_alias_without_application_does_not_establish_branding(self):
        manifest = self.manifest.replace('E: application', 'E: activity-alias')
        with self.assertRaisesRegex(ValueError, 'application'):
            validate_branding("application-label:'Polaris'", self.resources, manifest)


class UpdateIdentityTests(unittest.TestCase):
    def test_same_id_and_original_signer_allow_update_metadata(self):
        old = {'application_id': 'polaris.app', 'signer_sha256': 'A' * 64, 'version': '0.1.0-beta.10', 'version_code': 111}
        self.assertEqual('SAME_ID_AND_SIGNER', validate_update_identity('polaris.app', 'a' * 64, old)['status'])

    def test_rebuilt_apk_with_another_key_is_not_an_update(self):
        old = {'application_id': 'polaris.app', 'signer_sha256': 'a' * 64}
        with self.assertRaisesRegex(ValueError, 'Signing certificate differs'):
            validate_update_identity('polaris.app', 'b' * 64, old)

    def test_different_package_is_not_an_update_even_with_same_key(self):
        old = {'application_id': 'polaris.app', 'signer_sha256': 'a' * 64}
        with self.assertRaisesRegex(ValueError, 'Application ID differs'):
            validate_update_identity('polaris.other', 'a' * 64, old)

    def test_missing_or_invalid_previous_identity_is_rejected(self):
        for old in [{}, {'application_id': ''}, {'application_id': 1},
                    {'application_id': 'polaris.app', 'signer_sha256': 'not-a-hash'}]:
            with self.subTest(old=old), self.assertRaises(ValueError):
                validate_update_identity('polaris.app', 'a' * 64, old)


class CompiledBuildSafetyTests(unittest.TestCase):
    badging = f"package: name='{APPLICATION_ID}' versionCode='{VERSION_CODE}' versionName='{VERSION}'\nsdkVersion:'26'\n"
    manifest = "E: manifest\n E: application\n  A: http://schemas.android.com/apk/res/android:debuggable(0x0101000f)=(type 0x12)0x0\n"

    def test_non_debug_beta_with_the_installed_identity_is_verified(self):
        self.assertFalse(validate_compiled_build(self.badging, self.manifest, APPLICATION_ID)['debuggable'])

    def test_current_aapt_minimum_sdk_label_is_accepted(self):
        actual_badging_format = self.badging.replace('sdkVersion:', 'minSdkVersion:')
        self.assertTrue(validate_compiled_build(actual_badging_format, self.manifest, APPLICATION_ID)['compiled_identity_verified'])

    def test_metadata_cannot_disguise_another_compiled_package_version_or_api(self):
        for text in [self.badging.replace(APPLICATION_ID, 'different.app'), self.badging.replace(f"versionCode='{VERSION_CODE}'", f"versionCode='{VERSION_CODE - 1}'"), self.badging.replace(VERSION, '0.1.0-beta.11'), self.badging.replace("sdkVersion:'26'", "sdkVersion:'28'"), '']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                validate_compiled_build(text, self.manifest, APPLICATION_ID)

    def test_debug_test_only_profileable_and_instrumentation_artifacts_are_rejected(self):
        for text in [self.manifest.replace('0x0', '0xffffffff'), self.manifest+'  A: android:testOnly(0x01010272)=(type 0x12)0xffffffff\n', self.manifest+'  E: profileable\n   A: android:shell(0x01010523)=(type 0x12)0xffffffff\n', self.manifest+' E: instrumentation\n', self.manifest+'  E: activity\n   A: android:name(0x01010003)=".polaris.Spike001DebugActivity"\n', self.manifest+'  E: service\n   A: android:name(0x01010003)="eu.kanade.tachiyomi.extension.sandbox.ExtensionSandboxService"\n']:
            with self.subTest(manifest=text), self.assertRaisesRegex(ValueError, 'Debug, test'):
                validate_compiled_build(self.badging, text, APPLICATION_ID)

    def test_unknown_boolean_reference_cannot_be_assumed_to_be_false(self):
        with self.assertRaisesRegex(ValueError, 'Unverifiable'):
            validate_compiled_build(self.badging, self.manifest.replace('(type 0x12)0x0', '@0x7f000001'), APPLICATION_ID)

    def test_update_code_must_increase_and_cannot_be_bool_or_missing(self):
        base = {'application_id': 'polaris.app', 'signer_sha256': 'a'*64}
        for value in (None, True, 0, VERSION_CODE, VERSION_CODE + 1, str(VERSION_CODE - 1)):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'version code'):
                validate_update_identity('polaris.app', 'a'*64, dict(base, version_code=value))


def dex_fixture(names):
    # Minimal class-table fixture; this tests inventory decoding, not ART bytecode execution.
    count = len(names)
    strings_at = 112
    types_at = strings_at + 4*count
    classes_at = types_at + 4*count
    payload_at = classes_at + 32*count
    data = bytearray(payload_at)
    data[:8] = b'dex\n038\0'
    struct.pack_into('<II', data, 36, 112, 0x12345678)
    for field, position in [(56, strings_at), (64, types_at), (96, classes_at)]:
        struct.pack_into('<II', data, field, count, position)
    for index, name in enumerate(names):
        raw = name.encode()
        if len(raw) >= 128: raise ValueError('Short fixture names only')
        struct.pack_into('<I', data, strings_at+index*4, len(data))
        struct.pack_into('<I', data, types_at+index*4, index)
        struct.pack_into('<I', data, classes_at+index*32, index)
        data.extend(bytes([len(raw)])+raw+b'\0')
    struct.pack_into('<I', data, 32, len(data))
    data[12:32] = hashlib.sha1(data[32:]).digest()
    struct.pack_into('<I', data, 8, zlib.adler32(data[12:]) & 0xffffffff)
    return bytes(data)


class ProductionDexTests(unittest.TestCase):
    def inspect(self, files):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'classes.apk'
            with zipfile.ZipFile(path,'w') as archive:
                for name, data in files.items(): archive.writestr(name,data)
            with zipfile.ZipFile(path) as archive: return verify_production_classes(archive)

    def test_class_definitions_include_double_digit_multidex_files(self):
        result=self.inspect({'classes.dex':dex_fixture(['Lapp/Main;']), 'classes10.dex':dex_fixture(['Lapp/Reader;'])})
        self.assertEqual(2,result['class_definitions'])
        self.assertEqual(2,result['dex_files'])

    def test_sandbox_test_jdbc_and_debug_harness_classes_are_rejected(self):
        for name in ['Leu/kanade/tachiyomi/extension/sandbox/Worker;', 'Lorg/sqlite/JDBC;', 'Lapp/cash/sqldelight/driver/jdbc/Driver;', 'Lorg/junit/Test;', 'Leu/kanade/tachiyomi/polaris/Spike001DebugActivity;']:
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'production APK'):
                self.inspect({'classes.dex':dex_fixture([name])})

    def test_duplicate_definitions_across_multidex_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate class'):
            self.inspect({'classes.dex':dex_fixture(['Lapp/Main;']), 'classes2.dex':dex_fixture(['Lapp/Main;'])})

    def test_damaged_dex_and_missing_dex_fail_closed(self):
        for files in ({}, {'classes.dex':b'not dex'}, {'classes.dex':dex_fixture(['Lapp/Main;'])[:-1]}):
            with self.subTest(files=files.keys()), self.assertRaises(ValueError): self.inspect(files)

    def test_class_inventory_does_not_mistake_an_incidental_string_for_a_class(self):
        data=bytearray(dex_fixture(['Lapp/Main;']))
        data.extend(b'Leu/kanade/tachiyomi/extension/sandbox/OldName;\0')
        struct.pack_into('<I',data,32,len(data));data[12:32]=hashlib.sha1(data[32:]).digest()
        struct.pack_into('<I',data,8,zlib.adler32(data[12:]) & 0xffffffff)
        self.assertEqual(1,self.inspect({'classes.dex':bytes(data)})['class_definitions'])
