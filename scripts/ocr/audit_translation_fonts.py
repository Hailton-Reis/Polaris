#!/usr/bin/env python3
"""Inspect bundled font coverage without modifying fonts (requires fonttools)."""
import argparse
import hashlib
import json
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

LETTERS = 'CcÇçÃãÁáÉéÊêÍíÓóÔôÕõÚúÀà\u0327\u0301\u0303'


def audit(folder):
    records = []
    for path in sorted(folder.iterdir()):
        if path.suffix.lower() not in {'.ttf', '.otf'}:
            continue
        with TTFont(path) as font:
            cmap = font.getBestCmap()
            glyphs = font.getGlyphSet()
            bounds = {}
            for character in 'CÇcçÁÃg':
                if ord(character) in cmap:
                    pen = BoundsPen(glyphs)
                    glyphs[cmap[ord(character)]].draw(pen)
                    bounds[character] = pen.bounds
            records.append({
                'file': path.name,
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'units_per_em': font['head'].unitsPerEm,
                'weight': font['OS/2'].usWeightClass,
                'coverage': {character: cmap.get(ord(character)) for character in LETTERS},
                'glyph_bounds': bounds,
            })
    return records


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('font_directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    arguments.output.write_text(json.dumps(audit(arguments.font_directory), ensure_ascii=False, indent=2) + '\n')
