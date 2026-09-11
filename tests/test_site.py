from html.parser import HTMLParser
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "index.html"
ACCESS = ROOT / "claude-ai" / "podklyuchenie-iz-rossii" / "index.html"
PROFILE = ROOT / "claude-ai" / "kak-rasskazat-o-sebe" / "index.html"
MODEL = ROOT / "claude-ai" / "vybor-modeli-i-effort" / "index.html"
PROJECT = ROOT / "claude-ai" / "pervyy-proekt-v-claude" / "index.html"

PAGES = (HOME, ACCESS, PROFILE, MODEL, PROJECT)
GUIDE_PAGES = (ACCESS, PROFILE, MODEL, PROJECT)
PARTNER_LINK = "https://theivansergeev.com/ailager/?utm_source=botgk&utm_content=post1"
# Верхняя ссылка оглавления ведёт на <header>, а не на раздел, и из-под
# критерия дословного совпадения toc-заголовок выведена явно
HEADER_ANCHORS = {"vybor-modeli", "pervyy-proekt", "o-sebe", "podklyuchenie", "guides"}


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
        self._pending_section_id = None

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
        if tag == "section" and values.get("id"):
            self._pending_section_id = values["id"]
        if tag in {"h1", "h2", "h3"}:
            # id может лежать на самом заголовке либо на <section>, которую он
            # открывает: конвенция раздаток - h2-главы держат id на секции
            self._heading = values.get("id") or self._pending_section_id
            self._pending_section_id = None
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
        self.assertIn("ОБНОВЛЕНО 11 СЕНТЯБРЯ 2026", PROFILE.read_text(encoding="utf-8"))
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

    def test_chatgpt_memory_import_is_complete(self):
        html = PROFILE.read_text(encoding="utf-8")
        import_section = html.split('id="import-chatgpt"', 1)[1].split('id="check"', 1)[0]
        self.assertNotIn('href="#import-chatgpt"', import_section)
        for phrase in (
            "Start import",
            "Add to memory",
            "https://chatgpt.com/",
            "chatgpt-memory-export-prompt.png",
            "chatgpt-memory-export-result-redacted.png",
            "claude-memory-import-example.svg",
            "Точный срок Anthropic не указывает",
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
        for page in PAGES:
            self.assertNotIn("sayt-za-vecher", page.read_text(encoding="utf-8"))

    # --- инварианты, общие для всех страниц (цикл по PAGES, без копипасты) ---

    def test_every_page_exists_with_exactly_one_h1(self):
        for page in PAGES:
            with self.subTest(page=page.parent.name):
                self.assertTrue(page.exists(), page)
                self.assertEqual(self.parse(page).h1_count, 1, page)

    def test_every_internal_anchor_resolves(self):
        for page in PAGES:
            parsed = self.parse(page)
            broken = sorted(
                link[1:]
                for link in parsed.links
                if link.startswith("#") and link[1:] not in parsed.ids
            )
            with self.subTest(page=page.parent.name):
                self.assertEqual(broken, [], page)

    def test_toc_entries_repeat_target_headings_word_for_word(self):
        for page in PAGES:
            html = page.read_text(encoding="utf-8")
            parsed = self.parse(page)
            mismatched = []
            for anchor, title in re.findall(r'<a[^>]*href="#([^"]+)"[^>]*>([^<]+)</a>', html):
                if anchor in HEADER_ANCHORS:
                    continue
                heading = parsed.headings.get(anchor)
                if heading is not None and heading != title.strip():
                    mismatched.append((anchor, title.strip(), heading))
            with self.subTest(page=page.parent.name):
                self.assertEqual(mismatched, [], page)

    def tables_of_contents(self, html):
        """Два ОТДЕЛЬНЫХ оглавления страницы: десктопное nav.toc и мобильное
        details.mobile-toc. Раздатки читают с телефона, поэтому пропажа пункта
        из мобильного оглавления делает раздел недостижимым ровно так же, как
        пропажа из десктопного. Сборка одного множества по всему файлу схлопывает
        два оглавления в одно и такую пропажу не видит - отсюда раздельный разбор
        """
        tocs = {}
        desktop = re.search(r'<nav class="toc"[^>]*>.*?</nav>', html, re.S)
        if desktop:
            tocs["desktop nav.toc"] = set(
                re.findall(r'href="#([^"]+)"', desktop.group(0))
            )
        mobile = re.search(r'<details class="mobile-toc"[^>]*>.*?</details>', html, re.S)
        if mobile:
            tocs["mobile details.mobile-toc"] = set(
                re.findall(r'href="#([^"]+)"', mobile.group(0))
            )
        return tocs

    def test_both_tables_of_contents_are_present_on_every_guide_page(self):
        # Страховка от вырожденного зелёного: если оглавление переименуют или
        # снесут, разбор вернёт пустой словарь и проверка ниже станет пустой
        for page in GUIDE_PAGES:
            with self.subTest(page=page.parent.name):
                tocs = self.tables_of_contents(page.read_text(encoding="utf-8"))
                self.assertEqual(
                    sorted(tocs),
                    ["desktop nav.toc", "mobile details.mobile-toc"],
                    page,
                )
                for name, anchors in tocs.items():
                    self.assertTrue(anchors, f"{page}: {name} пусто")

    def test_every_titled_section_has_its_own_entry_in_the_table_of_contents(self):
        # Итерация идёт по РАЗДЕЛАМ, а не по ссылкам оглавления: раздел, которого
        # в оглавлении нет, обязан попасть в список, иначе тест зелёный вхолостую.
        # КАЖДОЕ из двух оглавлений проверяется ОТДЕЛЬНО своим множеством ссылок
        for page in PAGES:
            html = page.read_text(encoding="utf-8")
            parsed = self.parse(page)
            for name, linked in self.tables_of_contents(html).items():
                unreachable = sorted(
                    anchor
                    for anchor in parsed.headings
                    if anchor not in linked and anchor not in HEADER_ANCHORS
                )
                with self.subTest(page=page.parent.name, toc=name):
                    self.assertEqual(unreachable, [], f"{page}: {name}")

    def test_every_local_image_exists_and_carries_alt_text(self):
        for page in PAGES:
            html = page.read_text(encoding="utf-8")
            with self.subTest(page=page.parent.name):
                for tag in re.findall(r"<img\b[^>]*>", html):
                    self.assertIn("alt=", tag, f"{page}: {tag}")
                for source in self.parse(page).images:
                    if source.startswith(("http://", "https://", "data:")):
                        continue
                    self.assertTrue((page.parent / source).exists(), f"{page}: {source}")

    def test_no_long_dashes_and_no_paragraph_ends_with_a_period(self):
        for page in PAGES:
            html = page.read_text(encoding="utf-8")
            with self.subTest(page=page.parent.name):
                self.assertEqual(re.findall(r"[\u2014\u2013]", html), [], page)
                self.assertEqual(re.findall(r"[^.>]\.</p>", html), [], page)

    def test_partner_link_is_canonical_on_every_guide_page(self):
        for page in GUIDE_PAGES:
            html = page.read_text(encoding="utf-8")
            with self.subTest(page=page.parent.name):
                self.assertIn(PARTNER_LINK.replace("&", "&amp;"), html)
                for link in self.parse(page).links:
                    if "theivansergeev.com" in link:
                        self.assertEqual(link, PARTNER_LINK, page)

    def test_no_foreign_specifics_leak_into_public_pages(self):
        for page in PAGES:
            html = page.read_text(encoding="utf-8")
            with self.subTest(page=page.parent.name):
                for leak in ("sayt-za-vecher", "/Users/", "IvanOS"):
                    self.assertNotIn(leak, html, page)

    # --- МОДЕЛЬ и ПРОЕКТ: адресные проверки ---

    def test_model_section_ids_reach_the_headings_through_the_parser(self):
        headings = self.parse(MODEL).headings
        self.assertEqual(headings["tablica"], "Таблица выбора модели")
        self.assertEqual(headings["free"], "Что доступно на бесплатном тарифе")

    def test_model_chapters_open_with_h2_not_h3(self):
        html = MODEL.read_text(encoding="utf-8")
        for chunk in html.split('<section class="content-section"')[1:]:
            head = chunk.split("</section>", 1)[0]
            first = re.search(r"<h([23])\b", head)
            self.assertIsNotNone(first, head[:200])
            self.assertEqual(first.group(1), "2", head[:200])

    def test_model_never_names_a_default_effort_level(self):
        html = MODEL.read_text(encoding="utf-8")
        self.assertNotIn("уровень по умолчанию", html)
        self.assertEqual(html.count('<span class="effort-default">'), 1)
        for line in html.splitlines():
            self.assertFalse("по умолчанию" in line and "растягивает" in line, line)
        self.assertEqual(re.findall(r"Default[^<]{0,40}стоит на High", html), [])
        self.assertEqual(re.findall(r"по умолчанию[^<]{0,40}High", html), [])

    def test_model_screenshot_caption_and_checklist_name_levels_by_name(self):
        html = MODEL.read_text(encoding="utf-8")
        effort_block = html.split('id="urovni"', 1)[1].split("</section>", 1)[0]
        caption = re.search(r"<figcaption>(.*?)</figcaption>", effort_block, re.S).group(1)
        for token in ("Default", "Medium", "High"):
            self.assertIn(token, caption)
        checklist = html.split('class="checklist"', 1)[1].split("</ul>", 1)[0]
        self.assertTrue(
            any(level in checklist for level in ("Low", "Medium", "High", "Extra", "Max")),
            checklist,
        )

    def test_model_low_and_medium_differ_by_a_named_selection_sign(self):
        html = MODEL.read_text(encoding="utf-8")
        table = html.split('<table class="effort-table">', 1)[1].split("</table>", 1)[0]
        cells = {}
        for row in re.findall(r"<tr>(.*?)</tr>", table, re.S):
            name = re.match(r'<th scope="row">([A-Za-z]+)', row).group(1)
            if name in {"Low", "Medium"}:
                cells[name] = re.search(r"<td>(.*?)</td>", row, re.S).group(1)
        self.assertEqual(set(cells), {"Low", "Medium"})
        self.assertIn("Признак выбора", cells["Low"])
        self.assertIn("Признак выбора", cells["Medium"])
        self.assertNotIn(cells["Low"], cells["Medium"])
        self.assertNotIn(cells["Medium"], cells["Low"])

    def test_model_and_project_visible_dates_are_current(self):
        self.assertIn("ОБНОВЛЕНО 11 СЕНТЯБРЯ 2026", MODEL.read_text(encoding="utf-8"))
        self.assertIn("ОБНОВЛЕНО 11 СЕНТЯБРЯ 2026", PROJECT.read_text(encoding="utf-8"))

    def test_project_facts_follow_anthropic_support(self):
        html = PROJECT.read_text(encoding="utf-8")
        for phrase in (
            "до пяти проектов",
            "чаты внутри проекта не видят друг друга",
            "примерно в десять раз",
        ):
            self.assertIn(phrase, html)

    # --- главное правило автора: раздел открывается ситуацией человека ---
    #
    # Проверка идёт по ПРИЗНАКУ первого предложения, а не по списку избранных
    # разделов. Прежняя редакция держала кортеж из четырёх якорей с пришпиленным
    # началом лида: она защищала ровно те разделы, которые создал тот заход, и
    # молчала про остальные шестнадцать. Двадцать пришпиленных констант были бы
    # тем же списком, только длиннее, и ломались бы от любой правки текста.
    #
    # Признак взят из критерия ТЗ «ситуация против описания функции»:
    # описание функции - это первое предложение, где ПОДЛЕЖАЩЕЕ есть название
    # элемента интерфейса (или он же в локативе «в настройках», «в проекте»),
    # а СКАЗУЕМОЕ - связка определения либо расположения («- это», «находится»,
    # «хранится», «задаёт», «есть»). Ситуация таким шаблоном не описывается:
    # в ней подлежащее - читатель или происходящее с ним

    # Элементы интерфейса и сущности продукта, которые в роли подлежащего
    # превращают открытие в определение функции
    INTERFACE_ELEMENT = (
        r"(?:Effort|Thinking|[Ээ]ффорт|[Мм]одел[ьи]|База знаний|[Бб]аза|"
        r"[Пп]оиск|[Пп]амять|[Пп]роект[ыа]?|[Лл]имит[ы]?|[Нн]астройк[аи]|"
        r"[Оо]кно|[Кк]нопк[аи]|[Мм]еню|[Чч]ат[ыа]?|[Пп]ереключатель|"
        r"[Ии]нструкци[ияй]+|[Тт]ариф[ыа]?|[Рр]аздел|[Пп]оле|[Сс]писок)"
    )
    # Связка, которая определяет элемент или сообщает, где он лежит
    DEFINING_PREDICATE = (
        r"(?:- это|это|находится|находятся|лежит|лежат|хранит|хранится|хранятся|"
        r"задаёт|задают|отвечает за|представляет собой|есть|нужен для|нужна для|"
        r"нужно для|служит|позволяет)"
    )

    def function_definition_pattern(self):
        element = self.INTERFACE_ELEMENT
        predicate = self.DEFINING_PREDICATE
        return (
            # подлежащее-элемент плюс связка: «Effort - это настройка…»
            re.compile(rf"^(?:<b>)?{element}\w*\b[^.!?:]{{0,60}}?\b{predicate}\b"),
            # локатив плюс связка: «В настройках хранятся данные…»
            re.compile(
                rf"^(?:<b>)?[ВвНн]о?\s+{element}\w*\b[^.!?:]{{0,60}}?\b{predicate}\b"
            ),
        )

    def section_leads(self, page):
        """Все лиды страницы: (id секции, заголовок, тексты p.purpose).

        Лид - это p.purpose. Он живёт либо внутри section.content-section, либо
        в <header> (вводный лид страницы со ссылками на соседние раздатки).
        Оба вида - открытие текста, которое читает человек, поэтому под правило
        попадают оба. Раздел «Источники» прозы не содержит и лида не имеет по
        построению, поэтому исключается по своему ЗАГОЛОВКУ, а не по имени
        в списке разделов
        """
        html = page.read_text(encoding="utf-8")
        found = []
        # <header> на странице два: верхняя шапка сайта и шапка самой раздатки.
        # Лид живёт во второй, поэтому разбираются ОБА, а не первый попавшийся
        for block in re.findall(r"<header\b.*?</header>", html, re.S):
            # верхняя шапка сайта своего заголовка страницы не несёт и прозы
            # не содержит: признак отбора - наличие h1, а не имя блока
            if not re.search(r"<h1\b", block):
                continue
            header_id = re.search(r'id="([^"]+)"', block.split(">", 1)[0])
            found.append(
                (
                    header_id.group(1) if header_id else "header",
                    "Вводный лид страницы",
                    re.findall(r'<p class="purpose">(.*?)</p>', block, re.S),
                )
            )
        for chunk in html.split('<section class="content-section"')[1:]:
            body = chunk.split("</section>", 1)[0]
            section_id = re.match(r'\s*id="([^"]+)"', chunk)
            section_id = section_id.group(1) if section_id else None
            heading = re.search(r"<h([123])[^>]*>(.*?)</h\1>", body, re.S)
            title = re.sub(r"<[^>]+>", "", heading.group(2)).strip() if heading else ""
            if title == "Источники":
                continue
            leads = re.findall(r'<p class="purpose">(.*?)</p>', body, re.S)
            found.append((section_id, title, leads))
        return found

    def test_every_guide_section_carries_its_own_lead(self):
        """Удаление лида обязано ронять тест в ЛЮБОМ разделе трёх раздаток.

        Итерация идёт по РАЗДЕЛАМ, а не по лидам: раздел, у которого лида не
        стало, попадает в список пустым и валит проверку. Обход по лидам был бы
        зелёным вхолостую - удалённый лид цикл просто не посетил бы
        """
        for page in (MODEL, PROJECT, PROFILE):
            without = [
                (section_id, title)
                for section_id, title, leads in self.section_leads(page)
                if not leads
            ]
            with self.subTest(page=page.parent.name):
                self.assertEqual(without, [], f"{page}: раздел без собственного лида")

    def test_every_guide_section_opens_with_a_situation_not_a_definition(self):
        """Главное правило автора по ВСЕМ разделам трёх раздаток.

        Проверяется каждый лид каждого раздела, а не четыре избранных якоря:
        подмена любого лида описанием функции роняет тест в любом файле
        """
        by_subject, by_locative = self.function_definition_pattern()
        for page in (MODEL, PROJECT, PROFILE):
            definitions = []
            for section_id, _title, leads in self.section_leads(page):
                for lead in leads:
                    text = re.sub(r"<[^>]+>", "", lead).strip()
                    sentence = re.split(r"(?<=[.!?:])\s", text, maxsplit=1)[0]
                    if by_subject.match(sentence) or by_locative.match(sentence):
                        definitions.append((section_id, sentence))
            with self.subTest(page=page.parent.name):
                self.assertEqual(
                    definitions, [], f"{page}: раздел открыт описанием функции"
                )

    def test_the_situation_rule_actually_covers_every_lead_of_three_guides(self):
        """Страховка от вырожденного зелёного у двух проверок выше.

        Если разбор разделов сломается (переименуют класс секции, съедет разметка),
        обе проверки станут пустыми циклами и останутся зелёными, ничего не
        проверив. Поэтому охват объявлен числом: двадцать лидов в трёх файлах
        (6 + 5 + 9), и это ВСЕ p.purpose трёх раздаток, а не выборка из них
        """
        covered = {
            page.parent.name: sum(
                len(leads) for _id, _title, leads in self.section_leads(page)
            )
            for page in (MODEL, PROJECT, PROFILE)
        }
        self.assertEqual(
            covered,
            {
                "vybor-modeli-i-effort": 6,
                "pervyy-proekt-v-claude": 5,
                "kak-rasskazat-o-sebe": 9,
            },
            covered,
        )
        # обход обязан видеть КАЖДЫЙ p.purpose файла: если разбор потеряет хоть
        # один лид, он выпадет из-под правила незаметно
        for page in (MODEL, PROJECT, PROFILE):
            html = page.read_text(encoding="utf-8")
            with self.subTest(page=page.parent.name):
                self.assertEqual(
                    covered[page.parent.name],
                    html.count('<p class="purpose">'),
                    page,
                )

    def test_the_situation_detector_rejects_known_function_descriptions(self):
        """Детектор обязан ловить описание функции, а не быть вечно зелёным.

        Эталоны - формулировки, которыми контролёры круга 3 подменяли лиды,
        и снятый дефект R25 (лид главы #general до правки)
        """
        by_subject, by_locative = self.function_definition_pattern()
        definitions = (
            "Лимит - это ограничение тарифа, которое задаёт число сообщений",
            "В настройках хранятся данные, которые Claude будет использовать",
            "Effort - это настройка, которая задаёт глубину ответа",
            "База знаний находится справа внутри проекта",
            "Поиск по чатам есть в разделе Memory",
            "Память хранит твои проекты и предпочтения",
            "Проект это папка, в которой лежат чаты и документы",
            "В проекте хранятся документы, на которые Claude опирается",
        )
        for sentence in definitions:
            with self.subTest(sentence=sentence):
                self.assertTrue(
                    by_subject.match(sentence) or by_locative.match(sentence),
                    f"детектор пропустил описание функции: {sentence}",
                )

    def test_the_situation_detector_keeps_accepted_openings_green(self):
        """Обратная сторона: детектор не имеет права ронять живые открытия.

        Ложноположительное срабатывание заставило бы переписывать эталонные
        лиды, а решение R3 это прямо запрещает
        """
        by_subject, by_locative = self.function_definition_pattern()
        situations = (
            "Ты открыл Claude, написал задачу и получил ответ, который не устроил:",
            "Это первое, обо что спотыкается новичок:",
            "Обычная ситуация:",
            "Модели идут от самой быстрой к самой основательной.",
            "Настроил всё, а работает ли - непонятно.",
            "Ты дописываешь к каждому запросу одно и то же:",
        )
        for sentence in situations:
            with self.subTest(sentence=sentence):
                self.assertIsNone(by_subject.match(sentence), sentence)
                self.assertIsNone(by_locative.match(sentence), sentence)

    def test_public_deep_links_of_the_profile_guide_stay_alive(self):
        html = PROFILE.read_text(encoding="utf-8")
        for anchor in ("search-chats", "memory", "import-chatgpt"):
            self.assertEqual(html.count(f'id="{anchor}"'), 1, anchor)

    def test_chat_search_block_states_the_paid_plan_limit_first(self):
        html = PROFILE.read_text(encoding="utf-8")
        block = html.split('id="search-settings"', 1)[1].split('id="search-granicy"', 1)[0]
        self.assertLess(
            block.index("только на платных тарифах"),
            block.index("включать ничего не надо"),
        )
        self.assertIn("На платном тарифе включать ничего не надо", block)


if __name__ == "__main__":
    unittest.main()
