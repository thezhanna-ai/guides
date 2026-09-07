from html.parser import HTMLParser
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "index.html"
ACCESS = ROOT / "claude-ai" / "podklyuchenie-iz-rossii" / "index.html"
PROFILE = ROOT / "claude-ai" / "kak-rasskazat-o-sebe" / "index.html"


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1_count = 0
        self.links = []
        self.images = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "h1":
            self.h1_count += 1
        if tag == "a" and values.get("href"):
            self.links.append(values["href"])
        if tag == "img" and values.get("src"):
            self.images.append(values["src"])


class GuidesSiteTest(unittest.TestCase):
    def parse(self, page):
        parser = PageParser()
        parser.feed(page.read_text(encoding="utf-8"))
        return parser

    def test_public_pages_exist_and_have_one_main_heading(self):
        for page in (HOME, ACCESS, PROFILE):
            self.assertTrue(page.exists(), page)
            self.assertEqual(self.parse(page).h1_count, 1, page)

    def test_catalog_links_to_both_claude_guides(self):
        links = self.parse(HOME).links
        self.assertIn("claude-ai/podklyuchenie-iz-rossii/", links)
        self.assertIn("claude-ai/kak-rasskazat-o-sebe/", links)

    def test_profile_guide_links_to_access_guide(self):
        self.assertIn("../podklyuchenie-iz-rossii/", self.parse(PROFILE).links)

    def test_local_images_exist(self):
        for page in (ACCESS, PROFILE):
            for source in self.parse(page).images:
                if source.startswith(("http://", "https://", "data:")):
                    continue
                self.assertTrue((page.parent / source).exists(), f"{page}: {source}")

    def test_new_site_does_not_expose_old_repository_name(self):
        for page in (HOME, ACCESS, PROFILE):
            self.assertNotIn("sayt-za-vecher", page.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
