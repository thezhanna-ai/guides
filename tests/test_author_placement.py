"""Авторский блок принадлежит главной; в статье остаётся только её содержание."""
import unittest
from test_site import HOME, ROOT, ImageDocument


class AuthorPlacementTest(unittest.TestCase):
    def test_home_keeps_one_author_block_and_portrait(self):
        doc = ImageDocument(HOME.read_text(encoding='utf-8'))
        authors = doc.root.all(tag='section', klass='avtor')
        self.assertEqual(len(authors), 1)
        portraits = authors[0].all(tag='img')
        self.assertEqual(len(portraits), 1)
        self.assertEqual(portraits[0].attrs['src'], 'assets/zhanna-3x4.webp')
        self.assertTrue((ROOT / portraits[0].attrs['src']).is_file())

    def test_all_articles_have_no_author_markup_portrait_or_css(self):
        pages = sorted((ROOT / 'claude-ai').glob('*/index.html'))
        self.assertTrue(pages)
        for page in pages:
            with self.subTest(page=page.relative_to(ROOT).as_posix()):
                html = page.read_text(encoding='utf-8')
                doc = ImageDocument(html)
                self.assertEqual(doc.root.all(tag='section', klass='avtor'), [])
                self.assertNotIn('zhanna-3x4', html)
                self.assertNotRegex(html, r'\.avtor(?:[-\s.{:#\[])')


if __name__ == '__main__':
    unittest.main()
