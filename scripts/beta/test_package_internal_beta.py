from pathlib import Path
import tempfile
import unittest
from package_internal_beta import package, signer_digest

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
