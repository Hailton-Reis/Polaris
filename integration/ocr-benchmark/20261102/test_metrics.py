import unittest
from score_final import norm,distance,same,deduplicate
class MetricsTest(unittest.TestCase):
 def line(self,**kw):return dict(text='Keep the final line.',x=10,y=100,width=180,height=24,region=0,edge=40,**kw)
 def test_normalization_keeps_punctuation(self):
  self.assertEqual(norm('Ａ B\nC!'),'abc!');self.assertNotEqual(norm('NO!'),norm('NO.'))
 def test_unicode_and_script_are_preserved(self):
  self.assertEqual(norm('가'),norm('가'));self.assertNotEqual(norm('소라'),norm('Sora'))
 def test_distance_counts_edits(self):
  self.assertEqual(distance('kitten','sitting'),3);self.assertEqual(distance('abc',''),3);self.assertEqual(distance('abc','abxc'),1)
 def test_overlap_prefers_clear_edge(self):
  a=self.line();b=dict(a,region=1,edge=80,text='Keep the final line.')
  self.assertEqual(deduplicate([a,b]),[b])
 def test_repeated_sentence_at_other_position_is_retained(self):
  a=self.line();b=dict(a,region=1,y=250)
  self.assertFalse(same(a,b));self.assertEqual(len(deduplicate([a,b])),2)
 def test_same_region_is_not_deduplicated(self):
  a=self.line();b=dict(a,text='Keep the final line.')
  self.assertEqual(len(deduplicate([a,b])),2)
 def test_partial_word_overlap_does_not_merge_adjacent_lines(self):
  a=self.line();b=dict(a,region=1,y=120,text='line.')
  self.assertFalse(same(a,b));self.assertEqual(len(deduplicate([a,b])),2)
if __name__=='__main__':unittest.main()
