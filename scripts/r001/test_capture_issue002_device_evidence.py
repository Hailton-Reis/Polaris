"""Unit tests with a stub ADB; no emulator or source access required."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from capture_issue002_device_evidence import CaptureError, PNG_MAGIC, capture


def fake_adb(adb, serial, args, timeout=20):
    mapping = {
        "get-state": b"device\n",
        "ro.build.version.sdk": b"31\n",
        "ro.product.cpu.abi": b"arm64-v8a\n",
        "ro.build.fingerprint": b"test/fingerprint\n",
        "exec-out": PNG_MAGIC + b"sample",
        "logcat": b"PolarisSpike001: CREATED ...\n",
    }
    return mapping[args[2] if args[0] == "shell" else args[0]]


class DeviceCaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.apk = self.root / "spike.apk"
        self.apk.write_bytes(b"fake-apk")

    @patch("capture_issue002_device_evidence.adb_call", side_effect=fake_adb)
    def test_evidence_is_never_auto_pass(self, caller):
        out = self.root / "B02A"
        result = capture("adb", "emulator-5554", "B02A", out, self.apk, 11, 22, 33)
        self.assertEqual(result["runtime_verdict"], "CAPTURED_UNVERIFIED")
        self.assertEqual(json.loads((out / "evidence.json").read_text())["merged_manga_id"], 33)
        self.assertTrue((out / "screen.png").read_bytes().startswith(PNG_MAGIC))
        self.assertIn("AndroidRuntime:E", caller.call_args_list[-1].args[2])

    def test_refuses_same_child(self):
        with self.assertRaises(CaptureError):
            capture("adb", None, "B01", self.root / "capture", self.apk, 11, 11, None)

    def test_requires_merge_id_after_B01(self):
        with self.assertRaises(CaptureError):
            capture("adb", None, "B03", self.root / "capture", self.apk, 11, 12, None)

    @patch("capture_issue002_device_evidence.adb_call", side_effect=fake_adb)
    def test_refuses_overwriting_prior_evidence(self, caller):
        target = self.root / "capture"
        target.mkdir()
        (target / "screen.png").write_bytes(b"old")
        with self.assertRaises(CaptureError):
            capture("adb", None, "B01", target, self.apk, 11, 12, None)
        self.assertEqual((target / "screen.png").read_bytes(), b"old")

    @patch("capture_issue002_device_evidence.adb_call", return_value=b"offline\n")
    def test_fails_when_adb_offline(self, caller):
        with self.assertRaises(CaptureError):
            capture("adb", None, "B01", self.root / "out", self.apk, 11, 12, None)

    @patch("capture_issue002_device_evidence.adb_call")
    def test_does_not_save_invalid_png_as_proof(self, caller):
        def bad(adb, serial, args, timeout=20):
            if args[0] == "exec-out": return b"not a png"
            return fake_adb(adb, serial, args, timeout)
        caller.side_effect = bad
        with self.assertRaises(CaptureError):
            capture("adb", None, "B01", self.root / "out", self.apk, 11, 12, None)
        self.assertFalse((self.root / "out" / "evidence.json").exists())


if __name__ == "__main__": unittest.main()
