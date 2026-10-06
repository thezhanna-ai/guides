"""Проверка политики и всех точек подключения без браузера."""
import json
import re
import unittest
from pathlib import Path
from test_site import ImageDocument, ROOT
from test_indexing import generator, locations, BASE


class PrivacyTest(unittest.TestCase):
    def pages(self):
        return [ROOT / 'index.html', ROOT / 'politika/index.html'] + sorted((ROOT / 'claude-ai').glob('*/index.html'))

    def test_policy_operator_purposes_rights_and_local_article_design(self):
        page = ROOT / 'politika/index.html'
        self.assertTrue(page.is_file())
        html = page.read_text()
        doc = ImageDocument(html)
        self.assertEqual(len(doc.root.all(tag='h1')), 1)
        self.assertTrue(doc.root.all(klass='masthead'))
        self.assertTrue(doc.root.all(klass='toc'))
        self.assertTrue(doc.root.all(klass='foot'))
        for text in ['Слепова Жанна Константиновна', 'налога на профессиональный доход',
                     'pronovoe.site@yandex.ru', 'Яндекс', 'Вебвизор', '30 дней',
                     'cookie', 'localStorage', 'Согласие', 'обращение', 'Отозвать']:
            self.assertIn(text, html)
        self.assertNotRegex(html, r'\[НУЖНО|\[НУЖНА|\{\{|\u2014|\u2013')
        fonts = [n.attrs['href'] for n in doc.root.all(tag='link') if n.attrs.get('href', '').endswith('fonts.css')]
        self.assertEqual(fonts, ['/assets/fonts/fonts.css'])

    def test_all_content_pages_have_footer_controls_banner_and_local_assets(self):
        registry = json.loads((ROOT / 'data/statyi.json').read_text())['statyi']
        self.assertEqual(len(self.pages()), len(registry) + 2)
        for page in self.pages():
            with self.subTest(page=page.relative_to(ROOT)):
                html = page.read_text()
                doc = ImageDocument(html)
                footers = doc.root.all(tag='footer')
                links = [n for footer in footers for n in footer.all(tag='a') if n.attrs.get('href') == '/politika/']
                self.assertEqual(len(links), 1)
                self.assertEqual(links[0].text_content(), 'Политика данных')
                self.assertTrue(any('data-cookie-settings' in n.attrs for footer in footers for n in footer.all(tag='button')))
                for id in ['cookie-banner', 'cookie-accept', 'cookie-decline']:
                    self.assertEqual(html.count('id="' + id + '"'), 1)
                scripts = [n for n in doc.root.all(tag='script') if n.attrs.get('src') == '/assets/privacy.js']
                self.assertEqual(len(scripts), 1)
                self.assertIn('defer', scripts[0].attrs)
                self.assertEqual(html.count('href="/assets/privacy.css"'), 1)
                self.assertNotRegex(html, r'mc\.yandex\.|metrika/tag|\bym\s*\(')
                self.assertNotRegex(html, r'<(?:script|img|iframe)[^>]+https?://')
                self.assertNotIn('METRIKA_ID', html)

    def test_single_empty_counter_id_and_no_pixel_or_preconnect(self):
        js = (ROOT / 'assets/privacy.js').read_text()
        self.assertIn("const METRIKA_ID = '';", js)
        files = [ROOT / 'scripts/sobrat_glavnuyu.py'] + list((ROOT / 'scripts').glob('*.html')) + self.pages() + [ROOT / 'assets/privacy.js']
        assignments = sum(len(re.findall(r'\bMETRIKA_ID\s*=', p.read_text())) for p in files)
        self.assertEqual(assignments, 1)
        for page in self.pages():
            self.assertNotRegex(page.read_text(), r'<(?:noscript|link)[^>]*mc\.yandex')

    def test_policy_is_generated_and_in_sitemap_without_article_card(self):
        urls = locations((ROOT / 'sitemap.xml').read_text())
        self.assertEqual(urls.count(BASE + 'politika/'), 1)
        self.assertNotIn('noindex', (ROOT / 'politika/index.html').read_text())
        module = generator()
        self.assertEqual(module.sobrat_politiku(), (ROOT / 'politika/index.html').read_text())
        home = ImageDocument((ROOT / 'index.html').read_text())
        self.assertFalse(any(n.attrs.get('href') == '/politika/' for n in home.root.all(klass='guide-link')))

    def test_mobile_banner_space_is_measured_not_hardcoded(self):
        css = (ROOT / 'assets/privacy.css').read_text()
        js = (ROOT / 'assets/privacy.js').read_text()
        self.assertIn('var(--cookie-height', css)
        self.assertIn('ResizeObserver', js)
        self.assertIn('getBoundingClientRect', js)
        self.assertIn('@media (max-width: 600px)', css)
        self.assertIn('flex-wrap: wrap', css)
        self.assertIn('env(safe-area-inset-bottom', css)


if __name__ == '__main__':
    unittest.main()
