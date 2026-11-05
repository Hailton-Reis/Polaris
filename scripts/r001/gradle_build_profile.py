#!/usr/bin/env python3
"""Process-local Gradle limits. Never edits user/global Gradle configuration."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import sys

GIB = 1024 ** 3


def positive_file(path):
    try:
        value = int(path.read_text().strip())
        return value if value > 0 else None
    except (OSError, ValueError):
        return None


def linux_limits(root=Path('/sys/fs/cgroup')):
    memory = positive_file(root / 'memory.max') or positive_file(root / 'memory/memory.limit_in_bytes')
    quota = period = None
    try:
        raw_quota, raw_period = (root / 'cpu.max').read_text().split()
        quota, period = int(raw_quota), int(raw_period)
    except (OSError, ValueError):
        quota = positive_file(root / 'cpu/cpu.cfs_quota_us')
        period = positive_file(root / 'cpu/cpu.cfs_period_us')
    cpus = max(1, quota // period) if quota and period and quota > 0 and period > 0 else None
    return cpus, memory


def windows_memory():
    from ctypes import wintypes

    class MemoryStatus(ctypes.Structure):
        _fields_ = [('length', wintypes.DWORD), ('load', wintypes.DWORD)] + [
            (name, ctypes.c_ulonglong) for name in (
                'total_physical', 'available_physical', 'total_pagefile', 'available_pagefile',
                'total_virtual', 'available_virtual', 'available_extended',
            )
        ]

    status = MemoryStatus()
    status.length = ctypes.sizeof(status)
    function = ctypes.WinDLL('kernel32', use_last_error=True).GlobalMemoryStatusEx
    function.argtypes = [ctypes.POINTER(MemoryStatus)]
    function.restype = wintypes.BOOL
    return status.total_physical if function(ctypes.byref(status)) else None


def detect_resources():
    cpu_count = getattr(os, 'process_cpu_count', os.cpu_count)() or 1
    if hasattr(os, 'sched_getaffinity'):
        try:
            cpu_count = min(cpu_count, len(os.sched_getaffinity(0)))
        except OSError:
            pass
    memory = None
    try:
        if sys.platform == 'win32':
            memory = windows_memory()
        elif hasattr(os, 'sysconf'):
            memory = os.sysconf('SC_PHYS_PAGES') * os.sysconf('SC_PAGE_SIZE')
    except (OSError, ValueError, AttributeError):
        pass
    if sys.platform.startswith('linux'):
        cpu_limit, memory_limit = linux_limits()
        if cpu_limit:
            cpu_count = min(cpu_count, cpu_limit)
        if memory_limit:
            memory = min(memory, memory_limit) if memory and memory > 0 else memory_limit
    return max(1, cpu_count), memory if memory and memory > 0 else None


def select_profile(name, cpus, memory):
    if name not in ('auto', 'conservative'):
        raise ValueError('Profile must be auto or conservative')
    if name == 'conservative':
        workers, heap = 1, 3
    elif memory is None:
        workers, heap = min(max(1, cpus), 2), 3
    else:
        worker_cap, heap = next(
            (limit, size) for minimum, limit, size in (
                (48 * GIB, 12, 10), (24 * GIB, 8, 8), (12 * GIB, 4, 4),
                (7 * GIB, 2, 3), (0, 1, 2),
            ) if memory >= minimum
        )
        workers = min(max(1, cpus), worker_cap)
    optimized = name == 'auto'
    arguments = [
        '--build-cache' if optimized else '--no-build-cache',
        '--daemon' if optimized else '--no-daemon',
        '--parallel' if optimized and workers > 1 else '--no-parallel',
        f'-Pkotlin.incremental={str(optimized).lower()}',
        '-Pkotlin.compiler.execution.strategy=in-process',
        '--console=plain', '--stacktrace', f'--max-workers={workers}',
        f'-Dorg.gradle.jvmargs=-Xmx{heap}g -XX:MaxMetaspaceSize=1g -Dfile.encoding=UTF-8',
    ]
    return {
        'profile': name, 'detected_cpus': cpus, 'detected_memory_bytes': memory,
        'max_workers': workers, 'gradle_heap_gib': heap, 'cache': optimized,
        'incremental': optimized, 'daemon': optimized, 'parallel': optimized and workers > 1,
        'kotlin_compiler': 'in-process', 'gradle_arguments': arguments,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=('auto', 'conservative'), default='auto')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--args-file', type=Path, required=True)
    options = parser.parse_args()
    profile = select_profile(options.profile, *detect_resources())
    options.output.write_bytes((json.dumps(profile, indent=2) + '\n').encode())
    # One argument per LF line: spaces in the JVM option remain inside a single argument in Bash.
    options.args_file.write_bytes(('\n'.join(profile['gradle_arguments']) + '\n').encode())
    print(f"[BUILD] Perfil {profile['profile']}: {profile['max_workers']} workers, "
          f"heap Gradle {profile['gradle_heap_gib']} GiB, cache={profile['cache']}, "
          f"paralelo={profile['parallel']}, incremental={profile['incremental']}", flush=True)


if __name__ == '__main__':
    main()
