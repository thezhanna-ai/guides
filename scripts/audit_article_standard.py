#!/usr/bin/env python3
"""Браузерная сверка H1/шаринга и доказательные скриншоты корпуса статей."""

import argparse
import json
import random
import re
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
REFERENCE_SLUG = "trellis-2-3d-model-iz-foto"
WIDTHS = (390, 1440)
H1_KEYS = (
    "fontFamily",
    "fontSize",
    "fontWeight",
    "lineHeight",
    "letterSpacing",
    "color",
)
SHARE_KEYS = (
    "fontFamily",
    "fontSize",
    "fontWeight",
    "color",
    "backgroundColor",
    "borderTopColor",
    "borderTopWidth",
    "borderTopStyle",
    "borderRadius",
    "minHeight",
    "paddingLeft",
    "paddingRight",
    "display",
)


def article_urls():
    tree = ET.parse(ROOT / "sitemap.xml")
    return [
        node.text
        for node in tree.findall(".//sm:loc", SITEMAP_NS)
        if node.text and "/claude-ai/" in node.text
    ]


def slug_from_url(url):
    return urllib.parse.urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1]


def computed(locator, keys):
    return locator.evaluate(
        """(element, keys) => {
          const style = getComputedStyle(element);
          return Object.fromEntries(keys.map((key) => [key, style[key]]));
        }""",
        list(keys),
    )


def engine_presence(page_text):
    checks = {
        "canonical": bool(re.search(r'<link[^>]+rel=["\']canonical["\']', page_text, re.I)),
        "description": bool(re.search(r'<meta[^>]+name=["\']description["\']', page_text, re.I)),
        "og": 'property="og:title"' in page_text and 'property="og:image"' in page_text,
        "article_schema": '"@type": "Article"' in page_text or '"@type":"Article"' in page_text,
        "breadcrumbs_schema": "BreadcrumbList" in page_text,
        "quick_answer": bool(re.search(r'class=["\'][^"\']*\bquick-answer\b', page_text, re.I)),
        "sources": 'id="istochniki"' in page_text,
        "checklist": 'id="checklist"' in page_text,
        "faq_visible": 'id="faq"' in page_text,
        "faq_schema": "FAQPage" in page_text,
        "author": bool(re.search(r'class=["\'][^"\']*\bauthor-(?:card|box)\b', page_text, re.I)),
        "related": 'id="related"' in page_text,
    }
    return [name for name, present in checks.items() if not present]


def write_comparison_html(evidence_dir, width, samples):
    cards = []
    for slug in [REFERENCE_SLUG] + samples:
        label = "Эталон: Trellis 2" if slug == REFERENCE_SLUG else slug
        cards.append(
            f'''<article><h2>{label}</h2>
            <img src="{slug}-{width}-top.png" alt="Верх {label}">
            <h3>Поделиться</h3>
            <img class="share" src="{slug}-{width}-share.png" alt="Поделиться {label}"></article>'''
        )
    page = f'''<!doctype html><html lang="ru"><meta charset="utf-8"><title>Сверка {width}px</title>
    <style>
      *{{box-sizing:border-box}}body{{margin:0;padding:28px;background:#FAF6EF;color:#102F30;font:16px/1.45 Arial,sans-serif}}
      h1{{margin:0 0 22px;font-size:28px}}main{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:18px;align-items:start}}
      article{{min-width:0;padding:14px;border:1px solid #D5C9B7;border-radius:12px;background:white}}
      h2{{min-height:44px;margin:0 0 12px;font-size:16px;overflow-wrap:anywhere}}h3{{margin:14px 0 8px;font-size:13px}}
      img{{display:block;width:100%;height:auto;border:1px solid #D5C9B7}}img.share{{width:auto;max-width:100%}}
    </style><body><h1>Сверка старых статей с Trellis 2, viewport {width}px</h1><main>{''.join(cards)}</main></body></html>'''
    path = evidence_dir / f"comparison-{width}.html"
    path.write_text(page, encoding="utf-8")
    return path


def run(base_url, evidence_dir):
    evidence_dir.mkdir(parents=True, exist_ok=True)
    allowed_hostname = urllib.parse.urlsplit(base_url).hostname
    if not allowed_hostname:
        raise ValueError(f"Некорректный base URL: {base_url}")
    urls = article_urls()
    rows = {slug_from_url(url): {"url": url, "widths": {}, "missing_engine": []} for url in urls}
    samples = random.Random(20261018).sample(
        sorted(slug for slug in rows if slug not in {REFERENCE_SLUG, "igry-pro-ii"}), 3
    )
    capture = {REFERENCE_SLUG, *samples}
    mismatches = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for width in WIDTHS:
            context = browser.new_context(viewport={"width": width, "height": 900})
            context.route(
                "**/*",
                lambda route: route.continue_()
                if urllib.parse.urlsplit(route.request.url).hostname == allowed_hostname
                else route.abort(),
            )
            ref_page = context.new_page()
            ref_page.goto(f"{base_url}/claude-ai/{REFERENCE_SLUG}/", wait_until="domcontentloaded")
            ref_page.wait_for_selector("h1")
            reference_h1 = computed(ref_page.locator("h1").first, H1_KEYS)
            reference_share = computed(ref_page.locator(".share-top .share-btn").first, SHARE_KEYS)
            ref_page.close()

            for slug, row in rows.items():
                page = context.new_page()
                page.goto(f"{base_url}/claude-ai/{slug}/", wait_until="domcontentloaded")
                page.wait_for_selector("h1")
                h1 = computed(page.locator("h1").first, H1_KEYS)
                share_count = page.locator(".share-row").count()
                share = (
                    computed(page.locator(".share-top .share-btn").first, SHARE_KEYS)
                    if page.locator(".share-top .share-btn").count()
                    else {}
                )
                h1_ok = h1 == reference_h1
                share_ok = share_count == 2 and share == reference_share
                row["widths"][str(width)] = {
                    "h1_ok": h1_ok,
                    "share_ok": share_ok,
                    "h1": h1,
                    "share": share,
                }
                if not h1_ok or not share_ok:
                    mismatches.append(
                        {
                            "slug": slug,
                            "width": width,
                            "h1_diff": {k: [reference_h1[k], h1.get(k)] for k in H1_KEYS if reference_h1[k] != h1.get(k)},
                            "share_diff": {k: [reference_share[k], share.get(k)] for k in SHARE_KEYS if reference_share[k] != share.get(k)},
                            "share_count": share_count,
                        }
                    )

                if slug in capture:
                    page.screenshot(
                        path=evidence_dir / f"{slug}-{width}-top.png",
                        clip={"x": 0, "y": 0, "width": width, "height": min(900, page.evaluate("document.documentElement.scrollHeight"))},
                    )
                    page.locator(".share-top").screenshot(
                        path=evidence_dir / f"{slug}-{width}-share.png"
                    )
                page.close()
            context.close()

        for slug, row in rows.items():
            path = ROOT / "claude-ai" / slug / "index.html"
            row["missing_engine"] = engine_presence(path.read_text(encoding="utf-8"))

        for width in WIDTHS:
            comparison = write_comparison_html(evidence_dir, width, samples)
            page = browser.new_page(viewport={"width": 1800, "height": 1200})
            page.goto(comparison.as_uri(), wait_until="load")
            page.screenshot(path=evidence_dir / f"comparison-{width}.png", full_page=True)
            page.close()
        browser.close()

    result = {
        "reference": REFERENCE_SLUG,
        "samples": samples,
        "widths": WIDTHS,
        "rows": list(rows.values()),
        "mismatches": mismatches,
    }
    (evidence_dir / "audit.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Статей: {len(rows)}")
    print(f"Случайные старые статьи: {', '.join(samples)}")
    print(f"Несовпадений computed styles: {len(mismatches)}")
    print(f"Доказательства: {evidence_dir}")
    if mismatches:
        print(json.dumps(mismatches[:20], ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8799")
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.base_url.rstrip("/"), args.evidence_dir.resolve())
