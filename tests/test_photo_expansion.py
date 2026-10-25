"""Regression: ten independent edits, matching TOCs, and preserved examples."""
import unittest
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
PAGE = 'claude-ai/promty-pravki-foto-chatgpt/index.html'

class PhotoExpansion(unittest.TestCase):
    def test_nine_sliders_and_one_stacked_pair(self):
        page = BeautifulSoup((ROOT / PAGE).read_text(), 'html.parser')
        self.assertEqual(len(page.select('.comparison-slider')), 9)
        self.assertEqual(len(page.select('.comparison-stacked')), 1)
        pair = page.select_one('#p7 .comparison-stacked')
        self.assertIsNotNone(pair)
        self.assertFalse(pair.select('input, label, .comparison-stage, .comparison-handle'))
        self.assertEqual([x.text for x in pair.select('figcaption')], ['Было', 'Стало'])
        self.assertEqual([(int(i['width']), int(i['height'])) for i in pair.select('img')], [(1067, 1600), (1600, 900)])

    def test_ten_independent_edits_and_matching_tocs(self):
        page = BeautifulSoup((ROOT / PAGE).read_text(), 'html.parser')
        headings = page.select('article > .prompt-section > h2')
        self.assertEqual(len(headings), 10)
        expected = [(f'#prompt-{n:02}', f'{n}. {heading.text}')
                    for n, heading in enumerate(headings, 1)]
        for n, heading in enumerate(headings, 1):
            self.assertEqual(heading['id'], f'prompt-{n:02}')
            self.assertEqual(heading.parent['id'], f'p{n}')
            self.assertEqual(len(heading.parent.select('.comparison')), 1)
        tocs = page.select('.toc-steps')
        self.assertEqual(len(tocs), 2)
        for toc in tocs:
            self.assertFalse(toc.select('ul, .toc-sub'))
            edits = [(a['href'], a.text) for a in toc.select('a[href^="#prompt-"]')]
            self.assertEqual(edits, expected)
            self.assertFalse(toc.select('a[href="#section-19"]'))
            for a in toc.select('a'):
                self.assertIsNotNone(page.select_one(a['href']))
            for target in ['#section-20', '#section-23', '#section-24']:
                self.assertIsNotNone(toc.select_one(f'a[href="{target}"]'))
        self.assertEqual(str(tocs[0]), str(tocs[1]))
        self.assertIsNone(page.select_one('#style'))
        card = page.select_one('#p8 .related-plaque')
        self.assertIsNotNone(card)
        self.assertFalse(card.select('h2, h3, pre, .comparison'))
        self.assertIn('Хочешь, чтобы твоё фото получило свет и цвет другого снимка-образца', card.text)
        link = card.select_one('a')
        self.assertEqual(link['href'], '/claude-ai/kopirovat-stil-foto-v-chatgpt/')
        self.assertTrue((ROOT / link['href'].strip('/') / 'index.html').is_file())

    def test_approved_page_is_preserved_byte_for_byte(self):
        import hashlib
        self.assertEqual(
            hashlib.sha256((ROOT / PAGE).read_bytes()).hexdigest(),
            'd38feda432148004f340ef9f29887aa6a829a9e5439bda06ac2b205b4d61da41',
            'Publication must preserve the approved text, prompts, markup and examples',
        )

if __name__ == '__main__':
    unittest.main(verbosity=2)
