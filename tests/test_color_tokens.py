"""Lossless palette migration: preserve semantics and tokenize only actual colors."""
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from color_tokens import (canonical_color, color_spans, embed_palette, expand_palette,
                          html_style_chunks, palette_entries, tokenize_css, tokenize_html)
import sobrat_glavnuyu as builder

PALETTE = (ROOT / 'assets/palette.css').read_text()
ENTRIES = palette_entries(PALETTE)


class PaletteTests(unittest.TestCase):
    def test_lexer_distinguishes_values_from_selectors_strings_urls_and_custom_properties(self):
        css = '''/* color:red */ #fff:hover {
          --paper: #F8F7F2; --semantic: rgba(16,47,48,.42);
          color: #fff; font-family: 'Black', white;
          background: url("icons/#fff.svg") no-repeat linear-gradient(#102f30,rgba(16,47,48,.42));
          content: "color: red; #fff";
          border: 1px solid var(--edge, #102F30);
        } @media (min-width:1px) { @keyframes glow { 0% {box-shadow:0 0 2px #fff8} } }'''
        result = tokenize_css(css, ENTRIES)
        self.assertEqual(5, len(list(color_spans(css))))
        for exact in ['#fff:hover', '--paper: #F8F7F2;', '--semantic: rgba(16,47,48,.42);',
                      "font-family: 'Black', white;", 'url("icons/#fff.svg")', '"color: red; #fff"']:
            self.assertIn(exact, result)
        self.assertIn('var(--edge, var(--guide-color-forest))', result)
        self.assertIn('var(--guide-color-white-alpha-136-of-255)', result)
        self.assertEqual(result, tokenize_css(result, ENTRIES))
        self.assertEqual([x[3] for x in color_spans(css)],
                         [x[3] for x in color_spans(expand_palette(result, ENTRIES))])

    def test_mask_gradients_are_colors_too(self):
        css="p{mask-image:linear-gradient(transparent,#000);-webkit-mask-image:linear-gradient(#fff,transparent)}"
        result=tokenize_css(css,ENTRIES)
        self.assertEqual(4,result.count("var(--guide-color-"))
        self.assertEqual([],list(color_spans(result)))

    def test_exact_aliases_and_transparent_gradient_rgb_are_preserved(self):
        self.assertEqual(canonical_color('#fff'), canonical_color('rgb(255,255,255)'))
        self.assertEqual(canonical_color('white'), canonical_color('#FFFFFF'))
        self.assertEqual(canonical_color('rgba(16,47,48,.10)'), canonical_color('rgba(16, 47, 48, 0.1)'))
        self.assertNotEqual(canonical_color('transparent'), canonical_color('rgba(217,113,31,0)'))
        self.assertNotEqual(canonical_color('#fff8'), canonical_color('rgba(255,255,255,.53)'))
        self.assertIsNone(canonical_color('#palette'))

    def test_unknown_fixed_colors_fail_and_dynamic_values_keep_existing_semantics(self):
        for fixed in ['#abcdef', 'hsl(20,30%,40%)', 'rgb(10% 20% 30%)']:
            with self.subTest(fixed=fixed), self.assertRaises(ValueError):
                tokenize_css('p{color:' + fixed + '}', ENTRIES)
        dynamic = 'p{color:rgba(var(--channels), .5);background:currentColor}'
        self.assertEqual(dynamic, tokenize_css(dynamic, ENTRIES))

    def test_inline_attributes_advertising_and_palette_embedding_are_idempotent(self):
        ad = '<!-- erid:style:start --><style>.cta{color:#fff}</style><!-- erid:style:end --><section class="cta"><a style="color:#fff">Ad</a></section>'
        html = '<html><head><link rel="stylesheet" href="/keep.css"></head><body>' + ad + '<p style="border:1px solid #fff;color:#102F30">Text</p></body></html>'
        result = builder.dobavit_palette(html)
        self.assertIn(ad, result)
        self.assertIn('border:1px solid var(--guide-color-white);color:var(--guide-color-forest)', result)
        self.assertLess(result.index('id="guide-palette"'), result.index('href="/keep.css"'))
        self.assertEqual(result, builder.dobavit_palette(result))
        self.assertEqual(1, result.count('id="guide-palette"'))

    def test_complete_shipped_css_and_templates_use_palette_without_color_literals_in_values(self):
        pages = [ROOT / 'index.html', ROOT / 'politika/index.html', *ROOT.glob('claude-ai/*/index.html')]
        self.assertEqual(66, len(pages))
        for page in pages:
            with self.subTest(page=page.relative_to(ROOT)):
                source = page.read_text()
                self.assertEqual(1, source.count('id="guide-palette"'))
                self.assertEqual(source, builder.dobavit_palette(source))
                for _, _, css, inline in html_style_chunks(source):
                    self.assertEqual([], list(color_spans(css, inline)))
                    for name in re.findall(r'var\((--guide-color-[\w-]+)\)', css):
                        self.assertIn(name, {x[0] for x in ENTRIES.values()})
        for name in ['scripts/shablon_glavnoy.html', 'scripts/shablon_politiki.html']:
            for _, _, css, inline in html_style_chunks((ROOT / name).read_text()):
                self.assertEqual([], list(color_spans(css, inline)))
        for name in ['assets/quality.css', 'assets/privacy.css', 'assets/promty-foto.css']:
            self.assertEqual([], list(color_spans((ROOT / name).read_text())))

    def test_palette_rejects_duplicate_names_and_equivalent_aliases(self):
        for css in ["--guide-color-x:#fff;--guide-color-x:#000;", "--guide-color-x:#fff;--guide-color-y:white;"]:
            with self.subTest(css=css), self.assertRaises(ValueError):
                palette_entries(css)

    def test_existing_paper_and_font_definitions_are_not_rewritten(self):
        source = ':root{--paper:#F8F7F2;--paper-2:#F0E8D8;--forest:#102F30} @font-face{font-family:Black;src:url("black.woff2");font-weight:400} p{color:#102F30}'
        expected = source.replace('p{color:#102F30}', 'p{color:var(--guide-color-forest)}')
        self.assertEqual(expected, tokenize_css(source, ENTRIES))
