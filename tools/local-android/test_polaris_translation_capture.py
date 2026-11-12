import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import polaris_translation_capture as capture


PNG = (b'\x89PNG\r\n\x1a\n' + struct.pack('>I', 13) + b'IHDR' + struct.pack('>II', 1080, 1920) +
       b'\x08\x02\0\0\0' + b'\0' * 4 + b'\0' * 4 + b'IEND' + b'\0' * 4)


class FakeBridge:
    def __init__(self):
        self.visible = False
        self.chapter = 1
        self.scroll = False
        self.fail_image = False
        self.operations = []
        self.commands = []

    def operation(self, operation, **extras):
        self.operations.append((operation, extras))
        if operation == 'status':
            return dict(chapterId=self.chapter, pageIndex=0, sourceReady=True, translationHash='abc',
                        translationBlocks=3, translationsVisible=self.visible, vertical=True,
                        canScrollForward=self.scroll)
        if operation == 'visibility':
            self.visible = extras['visible']
        return {'ok': True}

    def binary(self, *args):
        if self.fail_image:
            raise capture.EmulatorError('Screenshot failed')
        return PNG

    def shell(self, *args):
        self.commands.append(args)
        if args[:2] == ('wm', 'size') and len(args) == 2:
            return 'Physical size: 720x1280\nOverride size: 900x1600\n'
        if args[:2] == ('wm', 'density') and len(args) == 2:
            return 'Physical density: 320\n'
        return ''


def fake_export(bridge, folder, chapter, status):
    sources = folder.parent / 'sources'
    sources.mkdir(exist_ok=True)
    (sources / 'sample.bin').write_bytes(b'original')
    (folder / 'record.json').write_text(json.dumps({'page': {'blocks': []}}), encoding='utf-8')
    return {}, '../sources/sample.bin'


class TranslationCaptureTests(unittest.TestCase):
    def test_only_owned_exact_emulator_is_selected(self):
        with tempfile.TemporaryDirectory() as raw, patch.object(capture, 'find_device') as finder:
            root = Path(raw)
            with self.assertRaises(capture.EmulatorError):
                capture.owned_device(root, 'adb')
            finder.assert_not_called()
            avd = capture.AVDS['spike001']
            (root / 'emulador' / 'avd' / (avd + '.avd')).mkdir(parents=True)
            (root / 'emulador' / (avd + '.owner.txt')).write_text(avd + '\n', encoding='utf-8')
            finder.return_value = 'emulator-5554'
            self.assertEqual(capture.owned_device(root, 'adb'), 'emulator-5554')
            finder.assert_called_once_with('adb', avd)

    def test_receiver_failure_and_missing_receiver_are_errors(self):
        self.assertEqual(capture.parse_broadcast('Broadcast completed: result=0, data="{"ok":true}"'), {'ok': True})
        for output in ('Broadcast completed: result=0', 'Broadcast completed: result=1, data="{}"',
                       'Broadcast completed: result=0, data="{"error":"x"}"'):
            with self.assertRaises(capture.EmulatorError):
                capture.parse_broadcast(output)

    def test_png_rejects_truncation_and_non_png_data(self):
        self.assertEqual(capture.png_size(PNG), (1080, 1920))
        for data in (b'permission denied', PNG[:-4], PNG.replace(b'IHDR', b'BAD!')):
            with self.assertRaises(capture.EmulatorError):
                capture.png_size(data)

    def test_failed_screenshot_restores_visibility_and_marks_partial(self):
        bridge = FakeBridge()
        bridge.visible = True
        bridge.fail_image = True
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / 'case'
            with self.assertRaises(capture.EmulatorError):
                capture.capture(bridge, root, pause=lambda _: None)
            self.assertTrue(bridge.visible)
            report = json.loads((root / 'report.json').read_text())
            self.assertEqual(report['collection'], 'PARTIAL_ERROR')
            self.assertEqual(report['quality'], 'PENDING_REVIEW')

    @patch.object(capture, 'export_page', side_effect=fake_export)
    def test_empty_translation_page_is_preserved_as_diagnostic_evidence(self, export):
        bridge = FakeBridge()
        original = bridge.operation
        def operation(name, **extras):
            result = original(name, **extras)
            if name == 'status':
                result['translationBlocks'] = 0
            return result
        bridge.operation = operation
        with tempfile.TemporaryDirectory() as raw:
            report = capture.capture(bridge, Path(raw) / 'case', max_frames=1, pause=lambda _: None)
            self.assertEqual(len(report['frames']), 1)
            self.assertEqual(report['quality'], 'PENDING_REVIEW')

    @patch.object(capture, 'export_page', side_effect=fake_export)
    def test_end_of_scroll_and_frame_budget_have_distinct_statuses(self, export):
        for scroll, expected in ((False, 'REACHED_READER_END'), (True, 'PARTIAL_LIMIT')):
            bridge = FakeBridge()
            bridge.scroll = scroll
            with tempfile.TemporaryDirectory() as raw:
                report = capture.capture(bridge, Path(raw) / 'case', max_frames=1, pause=lambda _: None)
                self.assertEqual(report['collection'], expected)
                self.assertEqual(len(report['frames']), 1)
                self.assertFalse(bridge.visible)

    @patch.object(capture, 'export_page', side_effect=fake_export)
    def test_stops_before_capturing_next_chapter(self, export):
        bridge = FakeBridge()
        bridge.scroll = True
        def pause(_):
            if any(args[:2] == ('input', 'swipe') for args in bridge.commands):
                bridge.chapter = 2
        with tempfile.TemporaryDirectory() as raw:
            report = capture.capture(bridge, Path(raw) / 'case', max_frames=3, pause=pause)
            self.assertEqual(report['collection'], 'STOPPED_AT_CHAPTER_BOUNDARY')
            self.assertEqual(len(report['frames']), 1)
            self.assertFalse(bridge.visible)

    def test_export_clears_app_temporary_files_on_transfer_failure(self):
        bridge = FakeBridge()
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaises(capture.EmulatorError):
                capture.export_page(bridge, Path(raw), 1, bridge.operation('status'))
        self.assertEqual(bridge.operations[-1][0], 'clear')
        self.assertEqual(bridge.operations[-1][1], bridge.operations[-2][1])

    def test_display_backup_survives_repeat_and_restores_original_override(self):
        bridge = FakeBridge()
        with tempfile.TemporaryDirectory() as raw:
            backup = Path(raw) / 'display.json'
            capture.change_display(bridge, backup)
            initial = backup.read_text()
            capture.change_display(bridge, backup)
            self.assertEqual(backup.read_text(), initial)
            capture.change_display(bridge, backup, restore=True)
            self.assertEqual(bridge.commands[-2:], [('wm', 'size', '900x1600'), ('wm', 'density', 'reset')])
            self.assertFalse(backup.exists())

    def test_invalid_display_backup_does_not_run_commands(self):
        bridge = FakeBridge()
        with tempfile.TemporaryDirectory() as raw:
            backup = Path(raw) / 'display.json'
            backup.write_text('{"size":"1080x1920;other","density":"420"}')
            with self.assertRaises(ValueError):
                capture.change_display(bridge, backup, restore=True)
            self.assertEqual(bridge.commands, [])

    def test_failed_density_change_rolls_back_display_and_keeps_backup(self):
        bridge = FakeBridge()
        original = bridge.shell
        def shell(*args):
            if args == ('wm', 'density', '420'):
                raise capture.EmulatorError('density failed')
            return original(*args)
        bridge.shell = shell
        with tempfile.TemporaryDirectory() as raw:
            backup = Path(raw) / 'display.json'
            with self.assertRaises(capture.EmulatorError):
                capture.change_display(bridge, backup)
            self.assertTrue(backup.is_file())
            self.assertEqual(bridge.commands[-2:], [('wm', 'size', '900x1600'), ('wm', 'density', 'reset')])

    @patch.object(capture, 'export_page', side_effect=fake_export)
    def test_single_frame_zip_stays_inside_capture(self, export):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / 'case'
            capture.capture(FakeBridge(), root, max_frames=1, pause=lambda _: None)
            path = capture.package_frame(root, 1)
            self.assertTrue(path.is_file())
            report = json.loads((root / 'report.json').read_text())
            report['frames'][0]['source'] = '../../outside.txt'
            (root / 'report.json').write_text(json.dumps(report))
            (root.parent / 'outside.txt').write_text('outside')
            with self.assertRaises(capture.EmulatorError):
                capture.package_frame(root, 1)


if __name__ == '__main__':
    unittest.main()
