"""Регрессии SEO по настоящему корпусу и отрицательные проверки сборщика."""
import html as html_lib
import json
import re
import unittest
import xml.etree.ElementTree as ET
from test_site import ImageDocument, ROOT
from test_indexing import generator, NS
import test_indexing
import tempfile


def plain(html):
    html = re.sub(r'</?(?:p|div|li|ul|ol|pre|blockquote)\b[^>]*>|<br\b[^>]*>', ' ', html, flags=re.I)
    return ' '.join(html_lib.unescape(re.sub(r'<[^>]+>', '', html)).split())


class SeoTest(unittest.TestCase):
    def test_all_canonical_pages_have_dated_sitemap(self):
        items = ET.fromstring((ROOT / 'sitemap.xml').read_text()).findall('s:url', NS)
        live = [x for x in json.loads((ROOT / 'data/statyi.json').read_text())['statyi'] if x['status'] == 'live' and not x.get('noindex_reason')]
        self.assertEqual(len(items), len(live) + 2)
        for item in items:
            url = item.find('s:loc', NS).text
            date = item.find('s:lastmod', NS)
            self.assertIsNotNone(date, url)
            self.assertRegex(date.text, r'^\d{4}-\d{2}-\d{2}$')
            path = ROOT / url.removeprefix('https://pronovoe.com/') / 'index.html'
            doc = ImageDocument(path.read_text())
            self.assertEqual([n.attrs.get('href') for n in doc.root.all(tag='link') if n.attrs.get('rel') == 'canonical'], [url])

    def test_article_schema_and_faq_are_visible_and_exact(self):
        metadata = json.loads((ROOT / 'data/seo.json').read_text())
        registry = json.loads((ROOT / 'data/statyi.json').read_text())['statyi']
        for row in registry:
            if row['status'] != 'live':
                continue
            path = ROOT / 'claude-ai' / row['slug'] / 'index.html'
            html = path.read_text()
            doc = ImageDocument(html)
            scripts = [n for n in doc.root.all(tag='script') if n.attrs.get('id') == 'seo-schema']
            self.assertEqual(len(scripts), 1, str(path))
            graph = json.loads(scripts[0].text)['@graph']
            article = next(x for x in graph if x['@type'] == 'Article')
            h1 = plain(re.search(r'<h1\b[^>]*>(.*?)</h1>', html, re.S)[1])
            self.assertEqual(article['headline'], ' '.join(h1.split()))
            self.assertEqual(doc.root.all(klass='quick-answer'), [], str(path))
            self.assertNotIn('<!-- seo:answer:start -->', html)
            # Проверяем видимое исходное вступление, без метки уровня и даты
            nodes = doc.root.all()
            heading = doc.root.all(tag='h1')[0]
            following = nodes[nodes.index(heading) + 1:]
            first_section = next((i for i, node in enumerate(following) if node.tag == 'h2'), len(following))
            paragraphs = [p for p in following[:first_section] if p.tag == 'p']
            multipart = doc.root.all(klass='seo-intro')
            intro = multipart[0] if multipart else next((p for p in paragraphs if set(p.attrs.get('class', '').split()) & {'lead', 'intro-lede'}), None)
            if intro is None:
                intro = next(p for p in paragraphs if not set(p.attrs.get('class', '').split()) & {'uroven-metka', 'meta', 'sun-caption'})
            self.assertTrue(40 <= len(intro.text_content().split()) <= 60, str(path))
            self.assertTrue(20 <= len(doc.root.all(tag='title')[0].text_content()) <= 65, str(path))
            self.assertEqual(article['dateModified'], metadata[path.relative_to(ROOT).as_posix()]['lastmod'])
            faq_nodes = doc.root.all(tag='details', klass='faq-item')
            faqs = [x for x in graph if x['@type'] == 'FAQPage']
            self.assertEqual(len(faqs), int(bool(faq_nodes)))
            if faqs:
                details = re.findall(r'<details\b[^>]*class="[^"]*\bfaq-item\b[^"]*"[^>]*>(.*?)</details>', html, re.S)
                for detail, schema in zip(details, faqs[0]['mainEntity'], strict=True):
                    summary = re.search(r'<summary\b[^>]*>(.*?)</summary>', detail, re.S)
                    answer = re.sub(r'<button\b[^>]*>.*?</button>', '', detail[summary.end():], flags=re.S)
                    self.assertEqual(schema['name'], plain(summary[1]))
                    self.assertEqual(schema['acceptedAnswer']['text'], plain(answer))
            crumb = next(x for x in graph if x['@type'] == 'BreadcrumbList')
            self.assertEqual([x['name'] for x in crumb['itemListElement']], ['Инструкции по нейросетям', ' '.join(h1.split())])

    def test_faq_preserves_paragraph_breaks_and_removes_copy_button(self):
        module = generator()
        source = '<html><head><title>Тест</title></head><body><h1>Тест</h1><details class="faq-item"><summary>Как проверить?</summary><p>Первый <strong>абзац</strong>.</p><p>Второй ответ.</p><button>Копировать</button></details></body></html>'
        result = module.dobavit_seo(source, 'https://pronovoe.com/claude-ai/test/', {})
        graph = json.loads(re.search(r'<script[^>]*id="seo-schema">(.*?)</script>', result, re.S)[1])['@graph']
        faq = next(x for x in graph if x['@type'] == 'FAQPage')
        self.assertEqual(faq['mainEntity'][0]['acceptedAnswer']['text'], 'Первый абзац. Второй ответ.')

    def test_llms_and_bot_controls_exist(self):
        llms = (ROOT / 'llms.txt').read_text()
        self.assertIn('51 инструкций', llms)
        self.assertEqual(llms.count('https://pronovoe.com/claude-ai/'), 3)
        robots = (ROOT / 'robots.txt').read_text()
        for bot in ['GPTBot', 'OAI-SearchBot', 'ClaudeBot', 'Claude-SearchBot', 'Claude-User', 'PerplexityBot']:
            self.assertIn('User-agent: ' + bot + '\nAllow: /', robots)

    def test_schema_serialization_cannot_end_script(self):
        module = generator()
        html = '<html><head><title>x</title></head><body><h1>Текст &lt;/script&gt;</h1></body></html>'
        result = module.dobavit_seo(html, 'https://pronovoe.com/claude-ai/test/', {'lastmod': '2026-10-08'})
        self.assertIn('\\u003c/script', result)
        self.assertEqual(len(re.findall(r'</script>', result)), 1)

    def test_missing_or_invalid_lastmod_does_not_get_today(self):
        module = generator()
        self.assertEqual(module.seo_lastmod({}), '')
        with self.assertRaises(ValueError):
            module.seo_lastmod({'lastmod': '2026-99-99'})

    def test_new_live_article_without_seo_blocks_build_without_writing_any_file(self):
        helper = test_indexing.IndexingTest()
        with tempfile.TemporaryDirectory() as directory:
            root = helper.fixture(directory)
            registry_path = root / 'data/statyi.json'
            registry = json.loads(registry_path.read_text())
            row = dict(registry['statyi'][0], slug='new-unconfigured', status='live')
            registry['statyi'].append(row)
            registry_path.write_text(json.dumps(registry))
            page = root / 'claude-ai/new-unconfigured/index.html'
            page.parent.mkdir()
            page.write_bytes((root / 'claude-ai' / registry['statyi'][0]['slug'] / 'index.html').read_bytes())
            before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
            with self.assertRaisesRegex(ValueError, 'data/seo.json'):
                helper.run_generator(root)
            self.assertEqual(before, {p: p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_live_publication_rejects_missing_date_short_title_or_intro(self):
        helper = test_indexing.IndexingTest()
        for problem in ['missing_date', 'invalid_date', 'short_title', 'long_title', 'short_intro', 'long_intro']:
            with self.subTest(problem=problem), tempfile.TemporaryDirectory() as directory:
                root = helper.fixture(directory)
                seo_path = root / 'data/seo.json'
                meta = json.loads(seo_path.read_text())
                rel = 'claude-ai/podklyuchenie-iz-rossii/index.html'
                if problem == 'missing_date':
                    meta[rel].pop('lastmod')
                elif problem == 'invalid_date':
                    meta[rel]['lastmod'] = '2026-02-30'
                elif problem.endswith('title'):
                    meta[rel]['title'] = 'Коротко' if problem == 'short_title' else 'я' * 66
                else:
                    page = root / rel
                    source = page.read_text()
                    a, b, _ = generator().seo_intro(source)
                    value = 'Мало слов' if problem == 'short_intro' else ' '.join(['слово'] * 61)
                    page.write_text(source[:a] + '<p class="lead">' + value + '</p>' + source[b:])
                seo_path.write_text(json.dumps(meta))
                before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
                with self.assertRaises(ValueError):
                    helper.run_generator(root)
                self.assertEqual(before, {p: p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_publication_gate_rejects_deleted_canonical_or_invalid_jsonld(self):
        module = generator()
        rel = 'claude-ai/podklyuchenie-iz-rossii/index.html'
        source = (ROOT / rel).read_text()
        meta = json.loads((ROOT / 'data/seo.json').read_text())[rel]
        url = module.DOMEN + rel.removesuffix('index.html')
        for bad in [re.sub(r'<link rel="canonical"[^>]+>', '', source),
                    re.sub(r'(<script[^>]+id="seo-schema">).*?(</script>)', r'\1{}\2', source, flags=re.S)]:
            with self.assertRaises(ValueError):
                module.proverit_seo_statyi(bad, meta, url)

    def test_intro_reader_skips_dates_badges_captions_and_stops_at_first_section(self):
        module = generator()
        source = '<h1>Название</h1><p class="uroven-metka">Уровень</p><p class="meta">Дата</p><p class="sun-caption">Подпись</p><p class="intro-lede">Вступление</p><h2>Раздел</h2><p class="lead">Не вступление</p>'
        self.assertEqual(module.seo_intro(source)[2], 'Вступление')
        with self.assertRaises(ValueError):
            module.seo_intro('<h1>Название</h1><p class="meta">Дата</p><h2>Раздел</h2><p>Основной текст</p>')

    def test_explicit_multipart_intro_preserves_separate_paragraphs(self):
        module = generator()
        fragment = '<p class="lead">Кто соберёт публикацию?</p><p>Текст уже есть.</p>'
        source = '<h1>Название</h1><div class="seo-intro">' + fragment + '</div><p>Обещание результата.</p><h2>Раздел</h2>'
        start, end, value = module.seo_intro(source)
        self.assertEqual(value, fragment)
        self.assertEqual(source[start:end], '<div class="seo-intro">' + fragment + '</div>')
        self.assertEqual(module.seo_plain(value), 'Кто соберёт публикацию? Текст уже есть.')

    def test_multipart_intro_rejects_ambiguous_or_out_of_scope_wrappers(self):
        module = generator()
        block = '<div class="seo-intro"><p>Текст</p></div>'
        for source in [block + '<h1>Название</h1><p class="lead">Вступление</p>',
                       '<h1>Название</h1><p class="lead">Вступление</p><h2>Раздел</h2>' + block,
                       '<h1>Название</h1>' + block + block,
                       '<h1>Название</h1><div class="seo-intro"><p>Текст</p>',
                       '<h1>Название</h1><div class="seo-intro"><div><p>Текст</p></div></div>']:
            with self.subTest(source=source), self.assertRaises(ValueError):
                module.seo_intro(source)

    def test_multipart_intro_keeps_word_count_publication_gate(self):
        module = generator()
        rel = 'claude-ai/podklyuchenie-iz-rossii/index.html'
        source = (ROOT / rel).read_text()
        meta = json.loads((ROOT / 'data/seo.json').read_text())[rel]
        url = module.DOMEN + rel.removesuffix('index.html')
        start, end, _ = module.seo_intro(source)
        for count in [39, 40, 60, 61]:
            fragment = '<div class="seo-intro"><p class="lead">' + ' '.join(['слово'] * 9) + '</p><p>' + ' '.join(['слово'] * (count - 9)) + '</p></div>'
            page = source[:start] + fragment + source[end:]
            with self.subTest(count=count):
                if count in [40, 60]:
                    module.proverit_seo_statyi(page, meta, url)
                else:
                    with self.assertRaisesRegex(ValueError, '40-60'):
                        module.proverit_seo_statyi(page, meta, url)

    def test_check_mode_detects_removed_seo_markup_without_repairing_files(self):
        helper = test_indexing.IndexingTest()
        with tempfile.TemporaryDirectory() as directory:
            root = helper.fixture(directory)
            page = root / 'claude-ai/podklyuchenie-iz-rossii/index.html'
            original = page.read_text()
            for pattern in [r'<!-- seo:canonical:start -->.*?<!-- seo:canonical:end -->',
                            r'<!-- seo:schema:start -->.*?<!-- seo:schema:end -->']:
                page.write_text(re.sub(pattern, '', original, flags=re.S))
                before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
                self.assertEqual(helper.run_generator(root, check=True), 1)
                self.assertEqual(before, {p: p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_rejects_an_extra_answer_but_allows_discussing_its_class_in_text(self):
        module = generator()
        rel = 'claude-ai/podklyuchenie-iz-rossii/index.html'
        source = (ROOT / rel).read_text()
        metadata = json.loads((ROOT / 'data/seo.json').read_text())[rel]
        url = module.DOMEN + rel.removesuffix('index.html')
        module.proverit_seo_statyi(source.replace('</body>', '<pre>quick-answer</pre></body>'), metadata, url)
        with self.assertRaisesRegex(ValueError, 'отдельный быстрый ответ'):
            module.proverit_seo_statyi(source.replace('</body>', '<p class="quick-answer">Повтор</p></body>'), metadata, url)



class IndexNowPublicationTest(unittest.TestCase):
    def module(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('indexnow', ROOT / 'scripts/indexnow.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_does_not_allow_ping_for_old_live_page(self):
        module = self.module()
        payload = json.loads((ROOT / 'data/indexnow.json').read_text())
        key = payload['key']
        errors = module.publication_errors(payload, lambda u: key if u == payload['keyLocation'] else '<html>old deployment</html>')
        self.assertEqual(len(errors), len(payload["urlList"]))
        self.assertTrue(all('другая версия' in e for e in errors))

    def test_accepts_only_matching_published_key_and_html(self):
        module = self.module()
        payload = json.loads((ROOT / 'data/indexnow.json').read_text())
        def get(url):
            if url == payload['keyLocation']:
                return payload['key'] + '\n'
            return (ROOT / (url.removeprefix('https://pronovoe.com/') + 'index.html')).read_text()
        self.assertEqual(module.publication_errors(payload, get), [])

    def test_rejects_outside_host_and_injected_url_before_network(self):
        module = self.module()
        payload = json.loads((ROOT / 'data/indexnow.json').read_text())
        payload['urlList'][0] = 'https://example.com/private'
        with self.assertRaises(ValueError):
            module.publication_errors(payload, lambda u: self.fail('Network must not run'))


if __name__ == '__main__':
    unittest.main()
