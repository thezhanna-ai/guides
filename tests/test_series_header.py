"""Шапка серии принадлежит раздаткам рилзов 01-15, а не категории каталога."""
import unittest

from test_indexing import generator
from test_site import ImageDocument, ROOT

SERIES = 'Claude.ai: кнопка за кнопкой'
GENERAL = 'Инструкции по нейросетям'
# 02-04 и 13 выдают одну статью КЛОД: 15 роликов, 12 уникальных раздаток
PAGES = {
    'podklyuchenie-iz-rossii', 'kak-rasskazat-o-sebe',
    'vybor-modeli-i-effort', 'pervyy-proekt-v-claude',
    'podklyuchit-gmail-drive-calendar', 'web-search-v-claude',
    'golosovoy-vvod-v-claude', 'skrinshot-vmesto-obyasneniy',
    'gotovye-fayly-excel-word-pdf', 'artefakty-v-claude',
    'incognito-chat-v-claude', 'pdf-v-markdown-markitdown',
}
CORRECTED = {
    'svoy-server-dlya-claude', 'claude-iz-rossii-bez-banov',
    'pyat-instrumentov-claude-code', 'urovni-vaybkodera',
    'whatsapp-nomer-dlya-agenta', 'besplatnye-video-iz-teksta',
    '10-besplatnyh-zamen', 'svoy-stil-otvetov',
    'raspisanie-zadach-v-claude', 'zagruzka-faylov-v-claude', 'dannye-v-claude',
}


class SeriesHeaderTest(unittest.TestCase):
    def test_series_header_regression_only_reels_01_15(self):
        found = set()
        reference = ImageDocument((ROOT / 'claude-ai/chetyre-mcp-claude-code/index.html').read_text())
        reference_brand = reference.root.all(klass='brand')[0]
        for page in sorted((ROOT / 'claude-ai').glob('*/index.html')):
            with self.subTest(slug=page.parent.name):
                document = ImageDocument(page.read_text())
                brands = document.root.all(klass='brand')
                series_brands = [b for b in brands if b.text_content().strip() == SERIES]
                if series_brands:
                    found.add(page.parent.name)
                    self.assertEqual(len(series_brands), 1)
                if page.parent.name in CORRECTED:
                    self.assertEqual(len(brands), 1)
                    brand = brands[0]
                    self.assertEqual(brand.text_content().strip(), GENERAL)
                    self.assertEqual((brand.tag, brand.attrs), (reference_brand.tag, reference_brand.attrs))
        self.assertEqual(found, PAGES)

    def test_new_article_copied_header_is_corrected_and_idempotent(self):
        module = generator()
        for container, tag, attrs in [('header', 'div', ''), ('header', 'a', ' href="../wrong/"'),
                                      ('div', 'a', ' href="../../"')]:
            with self.subTest(container=container, tag=tag):
                original = (f'<{container} class="masthead"><div class="masthead-inner">'
                            f'<{tag} class="brand"{attrs}>{SERIES}</{tag}>'
                            f'<button>◐</button></div></{container}>'
                            f'<main><p>{SERIES}</p></main>')
                expected = original.replace(f'<{tag} class="brand"{attrs}>{SERIES}</{tag}>',
                                            f'<a class="brand" href="../../">{GENERAL}</a>')
                result = module.dobavit_shapku(original, 'novaya-statya')
                self.assertEqual(result, expected)
                self.assertEqual(module.dobavit_shapku(result, 'novaya-statya'), result)
                for slug in PAGES:
                    self.assertEqual(module.dobavit_shapku(original, slug), original)
        untouched = f'<main><div class="brand">{SERIES}</div></main>'
        self.assertEqual(module.dobavit_shapku(untouched, 'novaya-statya'), untouched)
        for container in ('header', 'div'):
            html = f'<{container} class="masthead"></{container}>' + untouched
            self.assertEqual(module.dobavit_shapku(html, 'novaya-statya'), html)
