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
        self.ids = set()
        self.headings = {}
        self._heading = None
        self._heading_text = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "h1":
            self.h1_count += 1
        if tag == "a" and values.get("href"):
            self.links.append(values["href"])
        if tag == "img" and values.get("src"):
            self.images.append(values["src"])
        if values.get("id"):
            self.ids.add(values["id"])
        if tag in {"h1", "h2", "h3"}:
            self._heading = values.get("id")
            self._heading_text = []

    def handle_endtag(self, tag):
        if tag in {"h1", "h2", "h3"} and self._heading:
            self.headings[self._heading] = "".join(self._heading_text).strip()
            self._heading = None
            self._heading_text = []

    def handle_data(self, data):
        if self._heading is not None:
            self._heading_text.append(data)


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

    def test_access_guide_links_to_profile_after_first_chat(self):
        html = ACCESS.read_text(encoding="utf-8")
        self.assertIn("../kak-rasskazat-o-sebe/", self.parse(ACCESS).links)
        self.assertLess(html.index('id="first-chat"'), html.index('href="../kak-rasskazat-o-sebe/"'))

    def test_related_plaques_link_to_the_neighboring_guides(self):
        for page, target in (
            (ACCESS, "../kak-rasskazat-o-sebe/"),
            (PROFILE, "../podklyuchenie-iz-rossii/"),
        ):
            html = page.read_text(encoding="utf-8")
            plaque = html.split('class="related-plaque"', 1)[1]
            self.assertIn(target, plaque)
            self.assertIn("@media (min-width: 1200px)", html)
            self.assertIn("grid-column: 3", html)

    def test_profile_settings_toc_targets_the_matching_heading(self):
        profile = self.parse(PROFILE)
        self.assertEqual(profile.headings["settings"], "1. Где открыть настройки")
        self.assertEqual(profile.headings["memory"], "Зачем включать память")

    def test_access_toc_uses_the_current_section_labels(self):
        html = ACCESS.read_text(encoding="utf-8")
        for title in (
            "Подтвердить телефонный номер для нового аккаунта",
            "Что проверить перед первым сообщением",
        ):
            self.assertEqual(html.count(f">{title}<"), 3)

    def test_visible_revision_dates_match_the_current_review(self):
        self.assertIn("ОБНОВЛЕНО 8 СЕНТЯБРЯ 2026", PROFILE.read_text(encoding="utf-8"))
        access = ACCESS.read_text(encoding="utf-8")
        self.assertIn("ОБНОВЛЕНО 8 СЕНТЯБРЯ 2026", access)
        self.assertIn("Проверено 8 сентября 2026", access)

    def test_mobile_toc_uses_the_same_active_state_script(self):
        for page in (ACCESS, PROFILE):
            html = page.read_text(encoding="utf-8")
            self.assertIn(".toc a, .mobile-toc a", html)
            self.assertIn(".mobile-toc a.active", html)
            self.assertIn("if ((preferHash || hashIsSettling) && location.hash)", html)

    def test_profile_reduced_motion_and_desktop_toc_guard_follow_the_canon(self):
        html = PROFILE.read_text(encoding="utf-8")
        reduced_motion = html.split("@media (prefers-reduced-motion: reduce)", 1)[1].split("</style>", 1)[0]
        self.assertIn(".press-button, .press-button:hover, .press-button:active", reduced_motion)
        self.assertIn(".copy-button, .copy-button:hover, .copy-button:active", reduced_motion)
        self.assertIn("transition: none; transform: none; box-shadow: none; filter: none", reduced_motion)
        for page in (ACCESS, PROFILE):
            html = page.read_text(encoding="utf-8")
            self.assertIn("width: 260px", html)
            self.assertIn("margin-left: -50px", html)
            self.assertIn("@media (min-width: 1200px) and (max-width: 1279px)", html)
            self.assertIn("margin-left: -18px", html)
            self.assertNotIn("@media (min-width: 1280px) and (max-width: 1289px)", html)

    def test_phone_verification_matches_anthropic_flow(self):
        html = ACCESS.read_text(encoding="utf-8")
        for phrase in (
            "нового аккаунта",
            "поддерживаемой локации",
            "шестизначным кодом",
            "Verify code",
        ):
            self.assertIn(phrase, html)
        self.assertIn("Если экран проверки номера не появился, шаг с номером не нужен", html)

    def test_unsupported_service_rules_are_not_presented_as_anthropic_policy(self):
        html = ACCESS.read_text(encoding="utf-8")
        for phrase in (
            "за скачки IP можно получить блокировку",
            "больше 10 лет, проходит стабильнее",
            "не проходят верификацию аккаунта Anthropic",
            "страна номера должна совпадать со страной IP",
        ):
            self.assertNotIn(phrase, html)

    def test_future_import_is_not_a_self_link(self):
        html = PROFILE.read_text(encoding="utf-8")
        import_section = html.split('id="import-chatgpt"', 1)[1].split('id="check"', 1)[0]
        self.assertNotIn('href="#import-chatgpt"', import_section)
        for phrase in (
            "экспериментальная",
            "Claude.ai и Claude Desktop",
            "Free, Pro, Max и Team",
            "импорт может не сработать",
            "Start import",
            "перенеси нужную информацию вручную",
        ):
            self.assertIn(phrase, import_section)

    def test_access_metadata_info_note_and_reduced_motion_follow_the_canon(self):
        html = ACCESS.read_text(encoding="utf-8")
        for tag in (
            '<meta name="robots" content="noindex, nofollow">',
            '<meta property="og:title" content="Как подключить Claude из России">',
            '<meta property="og:description" content="Пошаговый путь к первому чату Claude: подключение, вход и подтверждение номера для нового аккаунта">',
        ):
            self.assertIn(tag, html)
        setup_note = html.split(".setup-note {", 1)[1].split("}", 1)[0]
        self.assertIn("padding: 11px 22px", setup_note)
        self.assertIn("border: 1px solid var(--sage-line)", setup_note)
        self.assertIn("background: var(--sage-note)", setup_note)
        reduced_motion = html.split("@media (prefers-reduced-motion: reduce)", 1)[1].split("</style>", 1)[0]
        self.assertIn(".button, .button:hover, .button:active", reduced_motion)
        self.assertIn("transition: none; transform: none; box-shadow: none", reduced_motion)

    def test_interactive_colors_meet_required_contrast(self):
        for page in (ACCESS, PROFILE):
            html = page.read_text(encoding="utf-8")
            self.assertIn("--accent: #E86F4A", html)
            self.assertIn("--accent-dark: #8F371F", html)
            self.assertIn("background: var(--accent)", html)
            self.assertIn("color: var(--emerald)", html)
            self.assertIn(".toc a.active::before { background: var(--accent) }", html)

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
