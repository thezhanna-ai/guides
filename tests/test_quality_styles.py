"""The quality fixes must not add a render-blocking network round trip."""
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import sobrat_glavnuyu as builder


class QualityStylesTests(unittest.TestCase):
    def test_all_shipped_pages_embed_current_styles_without_an_external_request(self):
        css = (ROOT / 'assets/quality.css').read_text().strip()
        pages = [ROOT / 'index.html', ROOT / 'politika/index.html', *ROOT.glob('claude-ai/*/index.html')]
        self.assertEqual(61, len(pages))
        for page in pages:
            with self.subTest(page=page.relative_to(ROOT)):
                source = page.read_text()
                self.assertEqual(1, source.count('<style id="guide-quality">'))
                self.assertIn('\n' + css + '\n</style>', source)
                self.assertNotIn('href="/assets/quality.css"', source)

    def test_rebuild_updates_styles_in_place_and_keeps_surrounding_cascade_order(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'assets').mkdir()
            css = root / 'assets/quality.css'
            before = '<style>before{color:red}</style>\n'
            after = '\n<style>after{color:green}</style>'
            original = before + '<link rel="stylesheet" href="/assets/quality.css">' + after
            with patch.object(builder, 'KORNI', root):
                css.write_text('button{color:#102F30}')
                embedded = builder.dobavit_quality(original)
                self.assertEqual(embedded, builder.dobavit_quality(embedded))
                css.write_text('button{color:#FFFFFF}')
                updated = builder.dobavit_quality(embedded)
            self.assertTrue(updated.startswith(before))
            self.assertTrue(updated.endswith(after))
            self.assertNotIn('button{color:#102F30}', updated)
            self.assertIn('button{color:#FFFFFF}', updated)
            self.assertEqual(1, updated.count('<style id="guide-quality">'))


class CriticalStylesTests(unittest.TestCase):
    def test_every_shipped_page_preserves_complete_font_and_privacy_rules_without_blocking_links(self):
        from urllib.parse import urljoin
        fonts = (ROOT / 'assets/fonts/fonts.css').read_text().strip()
        expected_fonts = re.sub(r'url\(([\'\"])([^\'\"]+)\1\)',
                                lambda m: 'url(' + m[1] + urljoin('/assets/fonts/', m[2]) + m[1] + ')', fonts)
        privacy = (ROOT / 'assets/privacy.css').read_text().strip()
        pages = [ROOT / 'index.html', ROOT / 'politika/index.html', *ROOT.glob('claude-ai/*/index.html')]
        self.assertEqual(61, len(pages))
        for page in pages:
            with self.subTest(page=page.relative_to(ROOT)):
                source = page.read_text()
                for name, css in [('fonts', expected_fonts), ('privacy-style', privacy)]:
                    matches = re.findall(r'<style id="guide-' + name + r'">\n(.*?)\n</style>', source, re.S)
                    self.assertEqual(matches, [css])
                self.assertNotRegex(source, r'<link\b[^>]+(?:fonts/fonts\.css|privacy\.css)')
                faces = re.findall(r'@font-face\s*\{([^}]+)\}', expected_fonts)
                self.assertEqual(8, len(faces))
                for face in faces:
                    path = re.search(r"url\('([^']+)'\)", face)[1]
                    self.assertTrue(path.startswith('/assets/fonts/'))
                    self.assertTrue((ROOT / path.lstrip('/')).is_file())

    def test_rebuild_preserves_each_link_position_and_updates_only_owned_blocks(self):
        original = ('<style>before{color:red}</style>'
                    '<link href="../../assets/fonts/fonts.css" rel="stylesheet">'
                    '<style>middle{color:blue}</style>'
                    '<link rel="stylesheet" href="/assets/privacy.css">'
                    '<style>after{color:green}</style>')
        embedded = builder.dobavit_critical_styles(original)
        self.assertEqual(embedded, builder.dobavit_critical_styles(embedded))
        self.assertLess(embedded.index('before{'), embedded.index('id="guide-fonts"'))
        self.assertLess(embedded.index('id="guide-fonts"'), embedded.index('middle{'))
        self.assertLess(embedded.index('middle{'), embedded.index('id="guide-privacy-style"'))
        self.assertLess(embedded.index('id="guide-privacy-style"'), embedded.index('after{'))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'assets/fonts').mkdir(parents=True)
            (root / 'assets/fonts/fonts.css').write_text("@font-face{font-family:'Same';src:url('same.woff2');font-weight:400;unicode-range:U+0400-045F;font-display:swap}")
            (root / 'assets/privacy.css').write_text('body{padding-bottom:var(--cookie-height,0px)}')
            with patch.object(builder, 'KORNI', root):
                updated = builder.dobavit_critical_styles(embedded)
                self.assertEqual(updated, builder.dobavit_critical_styles(updated))
            self.assertIn("url('/assets/fonts/same.woff2')", updated)
            self.assertIn('font-weight:400;unicode-range:U+0400-045F;font-display:swap', updated)
            self.assertNotIn("url('/assets/fonts/spectral-300.woff2')", updated)
            self.assertEqual(1, updated.count('id="guide-fonts"'))
            self.assertEqual(1, updated.count('id="guide-privacy-style"'))
            for unchanged in ['before{color:red}', 'middle{color:blue}', 'after{color:green}']:
                self.assertIn(unchanged, updated)

    def test_only_owned_stylesheet_links_are_replaced(self):
        original = ('<link rel="preload" href="/assets/fonts/fonts.css" as="style">'
                    '<link rel="stylesheet" href="https://example.com/assets/privacy.css">'
                    '<link rel="stylesheet" href="/other/privacy.css">')
        self.assertEqual(original, builder.dobavit_critical_styles(original))
