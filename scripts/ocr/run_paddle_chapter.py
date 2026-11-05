"""Measure prepared local chapter images/crops with the previously reviewed desktop Paddle port.

No downloads. Raw results contain recognized chapter text: keep them private.
Requires the Python dependencies documented in integration/ocr-benchmark/20261102.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import time


def duplicate(a, b):
    width = max(0, min(a['x'] + a['width'], b['x'] + b['width']) - max(a['x'], b['x']))
    height = max(0, min(a['y'] + a['height'], b['y'] + b['height']) - max(a['y'], b['y']))
    intersection = width * height
    first_area, second_area = a['width'] * a['height'], b['width'] * b['height']
    if min(first_area, second_area) <= 0:
        return False
    if intersection / max(1, first_area + second_area - intersection) >= .72:
        return True
    first = ''.join(c for c in a['text'].lower() if c.isalnum())
    second = ''.join(c for c in b['text'].lower() if c.isalnum())
    gap = abs(a['y'] + a['height'] / 2 - b['y'] - b['height'] / 2)
    if (first and first == second and max(a['height'], b['height']) / min(a['height'], b['height']) <= 2
            and intersection / min(first_area, second_area) >= .9
            and gap <= max(a['height'], b['height']) * .25):
        return True
    return bool(first and second and (first in second or second in first)
                and intersection / min(first_area, second_area) >= .9
                and gap <= min(a['height'], b['height']) * .25)


def reconcile(lines):
    kept = []
    for line in sorted(lines, key=lambda row: (-row.get('edge', 0), -len(row['text']))):
        if not line['text'].strip():
            continue
        if not any(other.get('region') != line.get('region') and duplicate(other, line) for other in kept):
            kept.append(line)
    return sorted(kept, key=lambda row: (row['y'], row['x']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--images', type=Path, required=True)
    parser.add_argument('--models', type=Path, required=True)
    parser.add_argument('--regions', type=Path, help='Private manual regions JSON with page, box and id')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a new output file; results are never overwritten')
    files = sorted(p for p in args.images.iterdir() if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'})
    if not files:
        parser.error('No prepared image files')
    os.environ['POLARIS_PADDLE_MODELS'] = str(args.models.resolve())
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        'paddle_pipeline', root / 'integration/ocr-benchmark/20261102/run_paddle_pipeline.py',
    )
    pipeline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pipeline)
    rec = pipeline.ort.InferenceSession(
        str(args.models / 'rec/inference.onnx'), pipeline.opts, providers=['CPUExecutionProvider'],
    )
    dictionary = [''] + pipeline.yaml.safe_load((args.models / 'rec/inference.yml').read_text())['PostProcess']['character_dict'] + [' ']
    cases = json.loads(args.regions.read_text())['cases'] if args.regions else [
        dict(id=file.stem, page=index + 1) for index, file in enumerate(files)
    ]
    rows = []
    for case in cases:
        image = pipeline.cv2.imread(str(files[case['page'] - 1]))
        if image is None:
            raise ValueError('Cannot decode image: ' + case['id'])
        if 'box' in case:
            x, y, width, height = case['box']
            if min(x, y) < 0 or min(width, height) <= 0 or x + width > image.shape[1] or y + height > image.shape[0]:
                raise ValueError('Region outside source: ' + case['id'])
            image = image[y:y + height, x:x + width]
        height, width = image.shape[:2]
        for mode in (['full'] if args.regions else ['full', 'strips']):
            start = time.perf_counter()
            lines, count = [], 0
            regional = mode == 'strips' and width <= 4096 and height > 2048 and height >= 3 * width
            top = 0
            while True:
                tile_height = min(2048, 2_097_152 // width) if regional else height
                bottom = min(top + tile_height, height)
                for line in pipeline.recognize(image[top:bottom], rec, dictionary):
                    line.update(edge=max(0, min(line['y'], bottom - top - line['y'] - line['height'])),
                                region=count, y=line['y'] + top)
                    lines.append(line)
                count += 1
                if bottom == height:
                    break
                top = bottom - min(384, tile_height // 4)
            kept = reconcile(lines)
            rows.append(dict(id=case['id'], page=case['page'], mode=mode, status='OK', width=width, height=height,
                             regions=count, lines=kept, raw_lines=lines, text=' '.join(line['text'] for line in kept),
                             elapsed_ms=(time.perf_counter() - start) * 1000))
            args.output.write_text(json.dumps(dict(runtime='Desktop Paddle port, not Android/ARM', rows=rows),
                                              ensure_ascii=False, indent=2) + '\n')
            print(case['id'], mode, len(kept), 'recognized regions', flush=True)


if __name__ == '__main__':
    main()
