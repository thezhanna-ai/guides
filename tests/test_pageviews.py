"""Сборка независимого счётчика на всех страницах."""
import json
import unittest

from test_indexing import generator
from test_site import ROOT


class PageviewsTest(unittest.TestCase):
    def test_all_registered_pages_receive_one_loader_after_load(self):
        registry = json.loads((ROOT / 'data/statyi.json').read_text())['statyi']
        pages = [ROOT / 'index.html', ROOT / 'politika/index.html']
        pages += [ROOT / 'claude-ai' / item['slug'] / 'index.html' for item in registry]
        block = (ROOT / 'scripts/pageviews-loader.html').read_text().strip()
        for page in pages:
            with self.subTest(page=page.relative_to(ROOT)):
                html = page.read_text()
                self.assertEqual(html.count(block), 1)
                self.assertLess(html.index('<!-- pageviews:start -->'), html.index('</body>'))
                self.assertNotIn('<script src="/assets/pageviews.js"', html)

    def test_shared_insertion_is_idempotent_and_changes_only_its_block(self):
        module = generator()
        source = '<html><head></head><body><p>Статья</p><script>animate()</script></body></html>'
        result = module.dobavit_pageviews(source)
        self.assertEqual(module.dobavit_pageviews(result), result)
        block = (ROOT / 'scripts/pageviews-loader.html').read_text().strip() + '\n'
        self.assertEqual(result.replace(block, ''), source)

    def test_policy_statement_matches_the_disabled_draft(self):
        line = 'После подключения GoatCounter отдельно ведётся обезличенный подсчёт открытий страниц'
        for page in ['scripts/shablon_politiki.html', 'politika/index.html']:
            self.assertEqual((ROOT / page).read_text().count(line), 1)


if __name__ == '__main__':
    unittest.main()
