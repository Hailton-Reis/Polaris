"""Regenerate the self-contained Windows CMD from the maintained PowerShell source.

Only developers need this script. End users download and run one .cmd file.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CMD = ROOT / "00_POLARIS_TUDO_EM_UM.cmd"
PS1 = ROOT / "Polaris_Setup.ps1"
MARKER = "\n:POLARIS_PS1_BEGIN\n"


def expected_contents() -> str:
    existing = CMD.read_text(encoding="utf-8")
    if existing.count(MARKER) != 1:
        raise ValueError("Unique embedded-PowerShell marker missing from CMD")
    header = existing.split(MARKER, 1)[0]
    maintained_source = PS1.read_text(encoding="utf-8")
    return header + MARKER + maintained_source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify CMD embeds exactly the maintained .ps1")
    args = parser.parse_args()
    expected = expected_contents()
    original = CMD.read_text(encoding="utf-8")
    if args.check:
        if original != expected:
            print("FAIL: CMD embedded PowerShell differs from maintained source")
            return 1
        print("PASS: CMD embeds the complete maintained PowerShell source")
        return 0
    if original != expected:
        CMD.write_text(expected, encoding="utf-8", newline="\n")
        print("Regenerated 00_POLARIS_TUDO_EM_UM.cmd")
    else:
        print("CMD already synchronized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
