import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from gradle_build_profile import GIB, linux_limits, select_profile


class BuildProfileTests(unittest.TestCase):
    def test_ryzen_3700x_32g_profile_bounds_memory_and_parallelism(self):
        profile = select_profile('auto', 16, 32 * GIB)
        self.assertEqual((8, 8), (profile['max_workers'], profile['gradle_heap_gib']))
        for argument in ('--parallel', '--build-cache', '--daemon', '-Pkotlin.incremental=true',
                         '-Pkotlin.compiler.execution.strategy=in-process'):
            self.assertIn(argument, profile['gradle_arguments'])

    def test_memory_and_cpu_limits_both_constrain_workers(self):
        for cpu, memory, expected in ((2, 8, (2, 3)), (16, 4, (1, 2)), (4, 16, (4, 4)),
                                      (2, 32, (2, 8)), (64, 64, (12, 10))):
            with self.subTest(cpu=cpu, memory=memory):
                profile = select_profile('auto', cpu, memory * GIB)
                self.assertEqual(expected, (profile['max_workers'], profile['gradle_heap_gib']))

    def test_unknown_memory_does_not_assume_a_workstation(self):
        profile = select_profile('auto', 128, None)
        self.assertEqual((2, 3), (profile['max_workers'], profile['gradle_heap_gib']))

    def test_conservative_is_an_explicit_serial_uncached_fallback(self):
        profile = select_profile('conservative', 16, 32 * GIB)
        self.assertEqual((1, 3), (profile['max_workers'], profile['gradle_heap_gib']))
        for argument in ('--no-parallel', '--no-build-cache', '--no-daemon', '-Pkotlin.incremental=false'):
            self.assertIn(argument, profile['gradle_arguments'])

    def test_cgroup_quotas_override_large_host_resources(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'cpu.max').write_text('200000 100000\n')
            (root / 'memory.max').write_text(str(8 * GIB))
            self.assertEqual((2, 8 * GIB), linux_limits(root))
            (root / 'cpu.max').write_text('max 100000\n')
            (root / 'memory.max').write_text('max\n')
            self.assertEqual((None, None), linux_limits(root))

    def test_v1_and_missing_or_malformed_limits(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertEqual((None, None), linux_limits(root))
            (root / 'cpu').mkdir()
            (root / 'memory').mkdir()
            (root / 'cpu/cpu.cfs_quota_us').write_text('50000')
            (root / 'cpu/cpu.cfs_period_us').write_text('100000')
            (root / 'memory/memory.limit_in_bytes').write_text(str(4 * GIB))
            self.assertEqual((1, 4 * GIB), linux_limits(root))
            (root / 'cpu/cpu.cfs_quota_us').write_text('-1')
            self.assertEqual((None, 4 * GIB), linux_limits(root))

    def test_unknown_profile_cannot_inject_gradle_arguments(self):
        with self.assertRaises(ValueError):
            select_profile('auto --max-workers=999', 16, 32 * GIB)

    def test_cli_emits_lf_separated_atomic_arguments_even_with_jvm_spaces(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            report, arguments = root / 'report.json', root / 'arguments.txt'
            subprocess.run([sys.executable, str(Path(__file__).with_name('gradle_build_profile.py')),
                            '--profile', 'conservative', '--output', str(report), '--args-file', str(arguments)],
                           check=True, capture_output=True)
            raw = arguments.read_bytes()
            self.assertNotIn(b'\r', raw)
            lines = raw.decode().splitlines()
            self.assertEqual(json.loads(report.read_text())['gradle_arguments'], lines)
            jvm = [line for line in lines if line.startswith('-Dorg.gradle.jvmargs=')]
            self.assertEqual(['-Dorg.gradle.jvmargs=-Xmx3g -XX:MaxMetaspaceSize=1g -Dfile.encoding=UTF-8'], jvm)


if __name__ == '__main__':
    unittest.main()
