import unittest
from test_indexing import generator

class PromptSeriesTest(unittest.TestCase):
    def test_series_links_follow_live_status_only_and_escape_text(self):
        module = generator()
        registry = {'serii': {'Картинки': [
            {'slug': 'pervaya', 'title': '<Свет>'},
            {'slug': 'vtoraya', 'title': 'Кисть'}]},
            'statyi': [{'slug':'pervaya','status':'gotova'}, {'slug':'vtoraya','status':'draft'}]}
        result = module.spisok_serii(registry, 'Картинки')
        self.assertNotIn('href=', result)
        self.assertIn('&lt;Свет&gt;', result)
        self.assertEqual(result.count('скоро'), 2)
        registry['statyi'][0]['status'] = 'live'
        result = module.spisok_serii(registry, 'Картинки')
        self.assertIn('href="../pervaya/"', result)
        self.assertNotIn('href="../vtoraya/"', result)
        self.assertEqual(result.count('скоро'), 1)
