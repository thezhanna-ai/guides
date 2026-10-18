#!/usr/bin/env python3
"""Пакетно переводит статьи sitemap на жирный H1 и два блока шаринга."""

import argparse
import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
SHARE_STYLESHEET = '<link rel="stylesheet" href="../../assets/article-sharing.css">'
H1_RE = re.compile(r"<h1\b([^>]*)>(.*?)</h1>", re.I | re.S)
CLASS_RE = re.compile(r"\sclass=([\"'])(.*?)\1", re.I | re.S)
SHARE_RE = re.compile(r'<div class="[^"]*\bshare-row\b[^"]*">.*?</div>', re.I | re.S)


def sitemap_articles():
    tree = ET.parse(ROOT / "sitemap.xml")
    return [
        node.text
        for node in tree.findall(".//sm:loc", SITEMAP_NS)
        if node.text and "/claude-ai/" in node.text
    ]


def article_path(url):
    return ROOT / urllib.parse.urlsplit(url).path.strip("/") / "index.html"


def visible_text(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def canonical_from_page(page):
    match = re.search(
        r'<link\b(?=[^>]*\brel=["\']canonical["\'])(?=[^>]*\bhref=["\']([^"\']+)["\'])[^>]*>',
        page,
        re.I,
    )
    if not match:
        match = re.search(
            r'<link\b(?=[^>]*\bhref=["\']([^"\']+)["\'])(?=[^>]*\brel=["\']canonical["\'])[^>]*>',
            page,
            re.I,
        )
    return html.unescape(match.group(1)) if match else ""


def share_block(canonical, title, top=False):
    url = urllib.parse.quote(canonical, safe="")
    text = urllib.parse.quote(title, safe="")
    cls = "share-row share-top" if top else "share-row"
    return f'''<div class="{cls}">
        <span class="eyebrow">Поделиться</span>
        <a class="share-btn" href="https://t.me/share/url?url={url}&amp;text={text}" target="_blank" rel="noopener">Telegram</a>
        <a class="share-btn" href="https://wa.me/?text={text}%20{url}" target="_blank" rel="noopener">WhatsApp</a>
        <a class="share-btn" href="https://vk.com/share.php?url={url}&amp;title={text}" target="_blank" rel="noopener">VK</a>
      </div>'''


def normalize_h1_class(page):
    match = H1_RE.search(page)
    if not match:
        raise ValueError("нет H1")

    attrs = match.group(1)
    class_match = CLASS_RE.search(attrs)
    tokens = class_match.group(2).split() if class_match else []
    before = list(tokens)
    tokens = [token for token in tokens if token != "article-title-v2"]
    if "article-standard-h1" not in tokens:
        tokens.append("article-standard-h1")
    if tokens == before:
        return page, False

    quote = class_match.group(1) if class_match else '"'
    replacement = f" class={quote}{' '.join(tokens)}{quote}"
    if class_match:
        new_attrs = attrs[: class_match.start()] + replacement + attrs[class_match.end() :]
    else:
        new_attrs = attrs + replacement
    new_h1 = f"<h1{new_attrs}>{match.group(2)}</h1>"
    return page[: match.start()] + new_h1 + page[match.end() :], True


def add_share_blocks(page, canonical, title):
    blocks = list(SHARE_RE.finditer(page))
    count = len(blocks)
    if count == 2:
        relocated = normalize_share_positions(page)
        return relocated, relocated != page
    if count == 1:
        existing = blocks[0].group(0)
        has_top = "share-top" in existing.split('class="', 1)[1].split('"', 1)[0].split()
        missing = share_block(canonical, title, top=not has_top)
        cta = page.find('<section class="cta"')
        if cta < 0:
            raise ValueError("нет хвостового cta")
        page = page[:cta] + "\n" + missing + "\n\n" + page[cta:]
        return normalize_share_positions(page), True
    if count != 0:
        raise ValueError(f"ожидалось не больше 2 блоков шаринга, найдено {count}")

    h1 = H1_RE.search(page)
    first_section = page.find("<section", h1.end() if h1 else 0)
    if first_section < 0:
        raise ValueError("нет первого section после H1")
    top = "\n" + share_block(canonical, title, top=True) + "\n\n"
    page = page[:first_section] + top + page[first_section:]

    bottom = "\n" + share_block(canonical, title) + "\n\n"
    cta = page.find('<section class="cta"', first_section + len(top))
    if cta < 0:
        raise ValueError("нет хвостового cta")
    question = list(re.finditer(r'<p\b[^>]*class=["\'][^"\']*\bcta-question\b[^"\']*["\'][^>]*>', page[:cta], re.I))
    help_banner = page.find('<section class="help-banner"', first_section + len(top), cta)
    bottom_anchor = question[-1].start() if question else help_banner if help_banner >= 0 else cta
    page = page[:bottom_anchor] + bottom + page[bottom_anchor:]
    return normalize_share_positions(page), True


def normalize_share_positions(page):
    blocks = list(SHARE_RE.finditer(page))
    if len(blocks) != 2:
        return page
    top = next((block.group(0) for block in blocks if "share-top" in block.group(0).split('class="', 1)[1].split('"', 1)[0].split()), "")
    bottom = next((block.group(0) for block in blocks if block.group(0) != top), "")
    if not top or not bottom:
        raise ValueError("не удалось отличить верхний и нижний шаринг")

    without = page
    for block in reversed(blocks):
        without = without[: block.start()] + without[block.end() :]

    h1 = H1_RE.search(without)
    if not h1:
        raise ValueError("нет H1 при нормализации шаринга")
    first_section = without.find("<section", h1.end())
    header_open = without.rfind("<header", 0, h1.start())
    previous_header_close = without.rfind("</header>", 0, h1.start())
    header_close = without.find("</header>", h1.end()) if header_open > previous_header_close else -1
    first_is_tail = first_section >= 0 and re.match(
        r'<section\b[^>]*class=["\'][^"\']*\b(?:cta|help-banner|seo-related)\b',
        without[first_section : first_section + 160],
        re.I,
    )
    if header_close >= 0:
        top_anchor = header_close + len("</header>")
    elif first_section >= 0 and not first_is_tail:
        top_anchor = first_section
    else:
        lead = re.search(
            r'<p\b[^>]*class=["\'][^"\']*\b(?:lead|intro-lede)\b[^"\']*["\'][^>]*>.*?</p>',
            without[h1.end() :],
            re.I | re.S,
        )
        if lead:
            top_anchor = h1.end() + lead.end()
        else:
            level_mark = re.match(
                r'\s*<p\b[^>]*class=["\'][^"\']*\buroven-metka\b[^"\']*["\'][^>]*>.*?</p>',
                without[h1.end() :],
                re.I | re.S,
            )
            top_anchor = h1.end() + level_mark.end() if level_mark else h1.end()
    normalized = without[:top_anchor].rstrip() + "\n\n" + top + "\n\n" + without[top_anchor:].lstrip()

    cta = normalized.find('<section class="cta"')
    if cta < 0:
        raise ValueError("нет хвостового cta")
    question = list(re.finditer(r'<p\b[^>]*class=["\'][^"\']*\bcta-question\b[^"\']*["\'][^>]*>', normalized[:cta], re.I))
    help_banner = normalized.rfind('<section class="help-banner"', 0, cta)
    question_anchor = question[-1].start() if question else help_banner if help_banner >= 0 else cta
    related = normalized.rfind("<!-- seo:related:start -->", 0, question_anchor)
    anchor = related if related >= 0 else question_anchor
    normalized = normalized[:anchor].rstrip() + "\n\n" + bottom + "\n\n" + normalized[anchor:].lstrip()
    normalized = re.sub(
        r'(<!-- seo:related:end -->)\s*(?=<p\s+class=["\']cta-question["\'])',
        r'\1\n',
        normalized,
        flags=re.I,
    )
    return re.sub(
        r'(<!-- seo:(?:faq|related):start -->)\s*(?=<section\b)',
        r'\1\n',
        normalized,
        flags=re.I,
    )


def migrate(apply=False):
    urls = sitemap_articles()
    if len(urls) != 61:
        raise SystemExit(f"ОШИБКА: ожидалась 61 статья, в sitemap найдено {len(urls)}")

    changed = []
    for canonical in urls:
        path = article_path(canonical)
        if not path.is_file():
            raise SystemExit(f"ОШИБКА: нет файла для {canonical}: {path}")
        page = path.read_text(encoding="utf-8")
        page_canonical = canonical_from_page(page)
        if page_canonical != canonical:
            raise SystemExit(
                f"ОШИБКА canonical: sitemap={canonical}, page={page_canonical or 'НЕТ'}"
            )
        h1 = H1_RE.search(page)
        if not h1:
            raise SystemExit(f"ОШИБКА: нет H1 в {path}")
        title = visible_text(h1.group(2))

        updated, h1_changed = normalize_h1_class(page)
        stylesheet_changed = False
        if SHARE_STYLESHEET not in updated:
            if "</head>" not in updated:
                raise SystemExit(f"ОШИБКА: нет </head> в {path}")
            updated = updated.replace("</head>", f"{SHARE_STYLESHEET}\n</head>", 1)
            stylesheet_changed = True
        updated, share_changed = add_share_blocks(updated, canonical, title)
        if h1_changed or stylesheet_changed or share_changed:
            changed.append((path, h1_changed, stylesheet_changed, share_changed))
            if apply:
                path.write_text(updated, encoding="utf-8")

    mode = "ИЗМЕНЕНО" if apply else "БУДЕТ ИЗМЕНЕНО"
    print(f"Статей в sitemap: {len(urls)}")
    print(f"{mode}: {len(changed)}")
    print(f"H1: {sum(row[1] for row in changed)}")
    print(f"Stylesheet: {sum(row[2] for row in changed)}")
    print(f"Поделиться: {sum(row[3] for row in changed)}")
    for path, h1_changed, stylesheet_changed, share_changed in changed:
        flags = ", ".join(
            flag
            for flag, enabled in (
                ("H1", h1_changed),
                ("stylesheet", stylesheet_changed),
                ("share", share_changed),
            )
            if enabled
        )
        print(f"{path.relative_to(ROOT)}\t{flags}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="записать изменения")
    args = parser.parse_args()
    migrate(apply=args.apply)
