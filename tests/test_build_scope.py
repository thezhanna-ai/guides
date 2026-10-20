"""Regressions for lossless shared blocks and isolated article builds."""
import contextlib
import io
import re
import tempfile
import unittest
from unittest.mock import patch

import test_indexing
from test_indexing import generator


class BuildScopeTests(unittest.TestCase):
    def run_build(self, root, *args):
        module = generator()
        with patch.multiple(module, KORNI=root, REESTR=root / 'data/statyi.json',
                            OBLOZHKI=root / 'data/OBLOZHKI.json', GLAVNAYA=root / 'index.html'), \
                patch('sys.argv', ['sobrat_glavnuyu.py', *args]), \
                contextlib.redirect_stdout(io.StringIO()):
            return module.main()

    def snapshot(self, root):
        return {p.relative_to(root): (p.read_bytes(), p.stat().st_mtime_ns)
                for p in root.rglob('*') if p.is_file()}

    def test_single_article_build_never_writes_other_article_files(self):
        for args in [(), ('--statya', 'podklyuchenie-iz-rossii')]:
            with self.subTest(args=args), tempfile.TemporaryDirectory() as directory:
                root = test_indexing.IndexingTest().fixture(directory)
                target = root / 'claude-ai/podklyuchenie-iz-rossii/index.html'
                other = root / 'claude-ai/shest-skillov/index.html'
                other.write_text(other.read_text().replace('</head>', '<meta name="robots" content="noindex, nofollow"></head>'))
                asset = other.parent / 'assets/original.txt'
                asset.parent.mkdir(exist_ok=True)
                asset.write_text('Чужой исходник')
                target.write_text(target.read_text().replace('</head>', '<meta name="robots" content="noindex, nofollow"></head>'))
                before = self.snapshot(root / 'claude-ai')
                self.assertEqual(self.run_build(root, *args), 0)
                after = self.snapshot(root / 'claude-ai')
                allowed = target.relative_to(root / 'claude-ai') if args else None
                self.assertEqual({p: v for p, v in before.items() if p != allowed},
                                 {p: v for p, v in after.items() if p != allowed})
                if args:
                    self.assertNotEqual(before[allowed][0], after[allowed][0])
                    stable = self.snapshot(root)
                    self.assertEqual(self.run_build(root, *args), 0)
                    self.assertEqual(stable, self.snapshot(root))

    def test_invalid_or_unknown_scope_fails_before_writing(self):
        for slug in ['../shest-skillov', 'missing-article', '/tmp/outside']:
            with self.subTest(slug=slug), tempfile.TemporaryDirectory() as directory:
                root = test_indexing.IndexingTest().fixture(directory)
                before = self.snapshot(root)
                with self.assertRaises(SystemExit):
                    self.run_build(root, '--statya', slug)
                self.assertEqual(before, self.snapshot(root))

    def test_privacy_rebuild_preserves_independent_faq_script_position(self):
        module = generator()
        source = module.sobrat_politiku()
        script = '<script type="application/ld+json" id="faq-schema">{}</script>'
        source = source.replace('</head>', script + '</head>')
        result = module.seo_for_page(module.dobavit_privacy(source), 'politika/index.html')
        self.assertEqual(source, result)

    def test_palette_update_preserves_custom_styles_inside_old_markers(self):
        module = generator()
        source = module.sobrat_politiku()
        custom = '<style id="custom">p{color:var(--guide-color-ink)}</style>\n'
        source = source.replace('<!-- palette:end -->', custom + '<!-- palette:end -->')
        self.assertEqual(source, module.dobavit_palette(source))

    def test_matching_faq_metadata_preserves_existing_section_design(self):
        module = generator()
        source = '<html><head><title>Тест</title></head><body><header><h1>Тест</h1></header><main></main></body></html>'
        meta = {'search_faq': [{'question': 'Вопрос?', 'answer': 'Ответ'}]}
        source = module.dobavit_seo(source, module.DOMEN + 'claude-ai/test/', meta)
        source = source.replace('<section class="seo-faq"', '<section id="faq" class="content-section seo-faq"')
        self.assertEqual(source, module.dobavit_seo(source, module.DOMEN + 'claude-ai/test/', meta))
        updated = module.dobavit_seo(source, module.DOMEN + 'claude-ai/test/',
                                     {'search_faq': [{'question': 'Новый?', 'answer': 'Новый ответ'}]})
        self.assertIn('Новый ответ', updated)
        self.assertNotIn('<summary>Вопрос?</summary>', updated)


if __name__ == '__main__':
    unittest.main()
