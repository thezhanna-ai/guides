import html
import json
import re
import unittest
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def article_urls():
    tree = ET.parse(ROOT / "sitemap.xml")
    return [
        node.text
        for node in tree.findall(".//sm:loc", SITEMAP_NS)
        if node.text and "/claude-ai/" in node.text
    ]


def article_path(url):
    relative = urllib.parse.urlsplit(url).path.strip("/")
    return ROOT / relative / "index.html"


class GlobalArticleStandardTest(unittest.TestCase):
    def test_sitemap_contains_the_complete_article_cohort(self):
        urls = article_urls()
        self.assertEqual(len(urls), sum(a['status'] == 'live' and not a.get('noindex_reason') for a in json.loads((ROOT / 'data/statyi.json').read_text())['statyi']))
        self.assertEqual(len(urls), len(set(urls)))
        for url in urls:
            self.assertTrue(article_path(url).is_file(), url)

    def test_every_article_uses_bold_h1_and_two_canonical_share_blocks(self):
        for canonical in article_urls():
            page = article_path(canonical).read_text(encoding="utf-8")
            slug = urllib.parse.urlsplit(canonical).path.rstrip("/").rsplit("/", 1)[-1]
            with self.subTest(slug=slug):
                h1 = re.search(r"<h1\b([^>]*)>(.*?)</h1>", page, re.I | re.S)
                self.assertIsNotNone(h1)
                self.assertNotIn("article-title-v2", h1.group(1))
                self.assertIn("article-standard-h1", h1.group(1))
                self.assertIn("../../assets/article-sharing.css", page)

                blocks = re.findall(
                    r'<div class="([^"]*\bshare-row\b[^"]*)">(.*?)</div>',
                    page,
                    re.I | re.S,
                )
                self.assertEqual(len(blocks), 2)
                self.assertIn("share-top", blocks[0][0].split())
                self.assertNotIn("share-top", blocks[1][0].split())

                title = html.unescape(re.sub(r"<[^>]+>", "", h1.group(2))).strip()
                encoded_url = urllib.parse.quote(canonical, safe="")
                encoded_title = urllib.parse.quote(title, safe="")
                expected = {
                    "Telegram": f"https://t.me/share/url?url={encoded_url}&text={encoded_title}",
                    "WhatsApp": f"https://wa.me/?text={encoded_title}%20{encoded_url}",
                    "VK": f"https://vk.com/share.php?url={encoded_url}&title={encoded_title}",
                }
                for _, block in blocks:
                    links = {
                        label: html.unescape(href)
                        for href, label in re.findall(
                            r'<a\b[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', block, re.I
                        )
                    }
                    self.assertEqual(links, expected)


if __name__ == "__main__":
    unittest.main()
