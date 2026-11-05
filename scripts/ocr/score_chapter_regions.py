"""Score manually transcribed local crops; preserve missing/error cases separately."""
import argparse
import json
from pathlib import Path
import unicodedata


def normalize(text):
    text = text.translate(str.maketrans({'“': '"', '”': '"', '‘': "'", '’': "'"}))
    return ''.join(c for c in unicodedata.normalize('NFKC', text).casefold() if not c.isspace())


def distance(first, second):
    previous = list(range(len(second) + 1))
    for i, a in enumerate(first, 1):
        current = [i]
        for j, b in enumerate(second, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (a != b)))
        previous = current
    return previous[-1]


def score(cases, results):
    if len({c['id'] for c in cases}) != len(cases):
        raise ValueError('Duplicate expected region IDs')
    by_id = {}
    pages = {c.get('benchmark_page', 101 + i): c['id'] for i, c in enumerate(cases)}
    for row in results:
        if row.get('mode', 'full') != 'full':
            continue
        key = row.get('id', pages.get(row.get('page')))
        if key is None:
            raise ValueError('Unmapped result; use the same crop manifest for both engines')
        if key in by_id:
            raise ValueError('Duplicate OCR result: ' + key)
        by_id[key] = row
    output = []
    for case in cases:
        row = by_id.get(case['id'])
        state = 'MISSING' if row is None else row.get('status', 'ERROR')
        result = {'id': case['id'], 'kind': case.get('kind', 'unspecified'), 'status': state}
        if state == 'OK':
            text = row.get('text')
            if text is None:
                text = ' '.join(x['text'] for x in sorted(row.get('lines', []), key=lambda x: (x['y'], x['x'])))
            expected, actual = normalize(case['text']), normalize(text)
            result.update(characters=len(expected), errors=distance(expected, actual), exact=expected == actual)
        output.append(result)
    valid = [row for row in output if row['status'] == 'OK']
    total = sum(row['characters'] for row in valid)
    errors = sum(row['errors'] for row in valid)
    return dict(
        status='COMPLETE' if len(valid) == len(cases) else 'INCOMPLETE',
        requested=len(cases), executed=len(valid), exact=sum(row['exact'] for row in valid),
        errors=errors, characters=total, cer=errors / total if total else None,
        missing=sum(row['status'] == 'MISSING' for row in output),
        execution_errors=sum(row['status'] not in ('MISSING', 'OK') for row in output), regions=output,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected', required=True, type=Path)
    parser.add_argument('--results', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    expected = json.loads(args.expected.read_text())
    results = json.loads(args.results.read_text())
    report = score(expected['cases'], results.get('rows', []) if isinstance(results, dict) else results)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(report['status'], report['exact'], '/', report['requested'], 'exact;', report['errors'], 'character errors')
    return 0 if report['status'] == 'COMPLETE' else 1


if __name__ == '__main__':
    raise SystemExit(main())
