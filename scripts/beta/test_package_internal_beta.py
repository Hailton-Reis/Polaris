from pathlib import Path
import tempfile
import unittest
from package_internal_beta import package, signer_digest, validate_branding, verify_universal_architectures, validate_update_identity
import zipfile


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


class UpdateIdentityTests(unittest.TestCase):
    def test_same_id_and_original_signer_allow_update_metadata(self):
        old = {'application_id': 'polaris.app', 'signer_sha256': 'A' * 64, 'version': '0.1.0-beta.10'}
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
