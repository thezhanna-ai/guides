"""Регрессии SEO по настоящему корпусу и отрицательные проверки сборщика."""
import html as html_lib
import json
import re
import unittest
import xml.etree.ElementTree as ET
from test_site import ImageDocument, ROOT
from test_indexing import generator, NS


def plain(html):
    html = re.sub(r'</?(?:p|div|li|ul|ol|pre|blockquote)\b[^>]*>|<br\b[^>]*>', ' ', html, flags=re.I)
    return ' '.join(html_lib.unescape(re.sub(r'<[^>]+>', '', html)).split())


class SeoTest(unittest.TestCase):
    def test_all_canonical_pages_have_dated_sitemap(self):
        items = ET.fromstring((ROOT / 'sitemap.xml').read_text()).findall('s:url', NS)
        self.assertEqual(len(items), len(json.loads((ROOT / "data/seo.json").read_text())))
        for item in items:
            url = item.find('s:loc', NS).text
            date = item.find('s:lastmod', NS)
            self.assertIsNotNone(date, url)
            self.assertRegex(date.text, r'^\d{4}-\d{2}-\d{2}$')
            path = ROOT / url.removeprefix('https://pronovoe.com/') / 'index.html'
            doc = ImageDocument(path.read_text())
            self.assertEqual([n.attrs.get('href') for n in doc.root.all(tag='link') if n.attrs.get('rel') == 'canonical'], [url])

    def test_article_schema_and_faq_are_visible_and_exact(self):
        for path in ROOT.glob('claude-ai/*/index.html'):
            html = path.read_text()
            doc = ImageDocument(html)
            scripts = [n for n in doc.root.all(tag='script') if n.attrs.get('id') == 'seo-schema']
            self.assertEqual(len(scripts), 1, str(path))
            graph = json.loads(scripts[0].text)['@graph']
            article = next(x for x in graph if x['@type'] == 'Article')
            h1 = plain(re.search(r'<h1\b[^>]*>(.*?)</h1>', html, re.S)[1])
            self.assertEqual(article['headline'], ' '.join(h1.split()))
            answers = doc.root.all(klass='quick-answer')
            self.assertEqual(len(answers), 1, str(path))
            self.assertTrue(40 <= len(answers[0].text_content().split()) <= 60, str(path))
            # Фактическое соседство H1 и ответа, а не наличие где-то в странице
            self.assertRegex(html, r'</h1>\s*(?:<p\b[^>]*uroven-metka[^>]*>.*?</p>\s*)?<!-- seo:answer:start -->\s*<p class="quick-answer"')
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
        self.assertIn('50 инструкций', llms)
        self.assertEqual(llms.count('https://pronovoe.com/claude-ai/'), 3)
        robots = (ROOT / 'robots.txt').read_text()
        for bot in ['GPTBot', 'OAI-SearchBot', 'ClaudeBot', 'Claude-SearchBot', 'Claude-User', 'PerplexityBot']:
            self.assertIn('User-agent: ' + bot + '\nAllow: /', robots)

    def test_schema_serialization_cannot_end_script(self):
        module = generator()
        html = '<html><head><title>x</title></head><body><h1>Текст &lt;/script&gt;</h1></body></html>'
        result = module.dobavit_seo(html, 'https://pronovoe.com/claude-ai/test/', {'lastmod': '2026-10-08', 'quick_answer': ' '.join(['слово'] * 40)})
        self.assertIn('\\u003c/script', result)
        self.assertEqual(len(re.findall(r'</script>', result)), 1)

    def test_missing_or_invalid_lastmod_does_not_get_today(self):
        module = generator()
        self.assertEqual(module.seo_lastmod({}), '')
        with self.assertRaises(ValueError):
            module.seo_lastmod({'lastmod': '2026-99-99'})



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
