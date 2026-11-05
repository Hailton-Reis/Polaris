from pathlib import Path
import tempfile
import unittest
from package_internal_beta import package, signer_digest, validate_branding

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
