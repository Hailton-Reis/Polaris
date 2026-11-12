import unittest
from score_chapter_regions import normalize, score


class ChapterRegionScoringTests(unittest.TestCase):
    def setUp(self):
        self.cases = [{'id': 'caption', 'text': 'HELLO, WORLD!'}]

    def test_typography_and_spacing_normalize_but_punctuation_remains_significant(self):
        self.assertEqual(normalize('“HELLO”\n WORLD'), normalize('"hello" world'))
        self.assertNotEqual(normalize('hello!'), normalize('hello?'))

    def test_android_geometry_maps_to_the_requested_crop_without_reordering_its_lines(self):
        result = score(self.cases, [{'page': 101, 'mode': 'full', 'status': 'OK', 'lines': [
            {'text': 'WORLD!', 'x': 0, 'y': 30}, {'text': 'HELLO,', 'x': 0, 'y': 0},
        ]}])
        self.assertEqual(('COMPLETE', 1, 0), (result['status'], result['exact'], result['errors']))

    def test_execution_failure_is_never_scored_as_perfect_empty_text(self):
        result = score(self.cases, [{'id': 'caption', 'status': 'ERROR'}])
        self.assertEqual(('INCOMPLETE', 0, 1), (result['status'], result['executed'], result['execution_errors']))
        self.assertIsNone(result['cer'])

    def test_missing_cases_fail_closed(self):
        result = score(self.cases, [])
        self.assertEqual(('INCOMPLETE', 1), (result['status'], result['missing']))

    def test_duplicate_results_are_rejected(self):
        row = {'id': 'caption', 'status': 'OK', 'text': 'Hello, world!'}
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            score(self.cases, [row, row])


if __name__ == '__main__':
    unittest.main()
