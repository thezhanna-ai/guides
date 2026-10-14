#!/usr/bin/env python3
"""Lossless reading images and responsive cover images, with opt-in HTML application.

Generate: python3 scripts/optimize_reading_images.py --generate
Apply articles (after review): python3 scripts/optimize_reading_images.py --apply
Builder: optimize_html(html, 'index.html') after rendering the homepage.
Original files and links to them are retained. Pillow needed only for --generate.
"""
import argparse
import hashlib
import html as html_module
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / 'data' / 'reading-images.json'
IMG = re.compile(r'<img\b[^>]*>', re.I)
ATTR = re.compile(r'\b([\w:-]+)\s*=\s*(["\'])(.*?)\2', re.S)
# Text posters identified by visual inspection; other proba-1-posle are photographs.
TEXT_PATHS = {
 'claude-ai/opus-55-protiv-gpt-6-astra/assets/oblozhka.webp',
 'claude-ai/opus-55-protiv-gpt-6-astra/assets/sravnenie-programmist.webp',
 'claude-ai/postery-iz-odnogo-foto/assets/her/primer-golden-hour.webp',
 'claude-ai/promty-blog-biznes-chatgpt/assets/proba-1-posle.webp',
 'claude-ai/promty-retro-ustroystvo-chatgpt/assets/proba-1-posle.webp',
 'claude-ai/besplatnye-video-iz-teksta/assets/oblozhka.webp',
}
# Existing lossy WebP posters grow when decoded and encoded losslessly. Native
# resolution recompression was inspected on their smallest labels before use.
NATIVE_QUALITY = {
 'claude-ai/postery-iz-odnogo-foto/assets/her/primer-golden-hour.webp': 88,
 'claude-ai/promty-blog-biznes-chatgpt/assets/proba-1-posle.webp': 90,
 'claude-ai/promty-retro-ustroystvo-chatgpt/assets/proba-1-posle.webp': 89,
}
# These video comparison labels were inspected at actual mobile article size.
# Keep at least 960 source pixels; other article screenshots stay native.
RESPONSIVE_ARTICLE_TEXT = {
 'claude-ai/opus-55-protiv-gpt-6-astra/assets/oblozhka.webp',
 'claude-ai/opus-55-protiv-gpt-6-astra/assets/sravnenie-programmist.webp',
}
CARD_LOSSY_TEXT = {'claude-ai/besplatnye-video-iz-teksta/assets/oblozhka.webp'}


def local_path(src, page):
    if urlsplit(src).scheme or src.startswith(('data:', '//', '#')):
        return None
    relative = unquote(urlsplit(html_module.unescape(src)).path)
    path = ROOT / relative.lstrip('/') if relative.startswith('/') else ROOT / Path(page).parent / relative
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return None


def inventory():
    found = {}
    for page in sorted(ROOT.glob('claude-ai/*/index.html')):
        for tag in IMG.findall(page.read_text(encoding='utf-8')):
            attrs = {k.lower(): v for k, _, v in ATTR.findall(tag)}
            src = attrs.get('data-full-src', attrs.get('src', ''))
            key = local_path(src, page.relative_to(ROOT))
            if key and (ROOT / key).is_file() and (ROOT / key).stat().st_size > 300000:
                item = found.setdefault(key, {'article': True, 'cover': False, 'pages': []})
                name = page.relative_to(ROOT).as_posix()
                if name not in item['pages']:
                    item['pages'].append(name)
    for cover in json.loads((ROOT / 'data/OBLOZHKI.json').read_text(encoding='utf-8')).values():
        key = cover['image']
        if (ROOT / key).is_file():
            found.setdefault(key, {'article': False, 'cover': False, 'pages': []})['cover'] = True
    return found


def generate():
    from PIL import Image
    typography_policy = ROOT / 'data/cover-readability.json'
    typography_keys = ({entry['image'] for entry in json.loads(typography_policy.read_text())['updated'].values()}
                       if typography_policy.exists() else set())
    result = {'version': 1, 'threshold_bytes': 300000,
              'policy': 'Article text uses native-resolution lossless WebP with exact decoded pixels and ICC, except Opus video cover and comparison with inspected lossless960/native candidates and no480 for reading. Three already lossy WebP posters use inspected native-resolution quality88/90/89 recompression when lossless grows the file; exact lossless reference assets retained for validation. Card covers use adaptive WebP quality95 or lossless with original native fallback; every cover label has a visual crop comparison. Originals retained.',
              'images': {}}
    for key, meta in inventory().items():
        original = ROOT / key
        image = Image.open(original).convert('RGBA' if 'A' in Image.open(original).getbands() else 'RGB')
        text = original.suffix.lower() == '.png' or key in TEXT_PATHS or key in typography_keys
        # Text covers also retain native resolution, to avoid blurring tiny letters.
        widths = (sorted(set(min(image.width, n) for n in (480, 960, image.width))) if meta['cover'] else [image.width]) if text else sorted(set(min(image.width, n) for n in (480, 960)))
        if text and key in RESPONSIVE_ARTICLE_TEXT and not meta['cover']:
            widths = sorted(set(min(image.width, n) for n in (960, image.width)))
        variants = []
        for width in widths:
            card_lossy = key in CARD_LOSSY_TEXT and key not in typography_keys and width < image.width
            path = original.with_name(original.stem + ('.reading-card-' if card_lossy else '.reading-') + str(width) + '.webp')
            resized = image if width == image.width else image.resize((width, round(image.height * width / image.width)), Image.Resampling.LANCZOS)
            resized.save(path, 'WEBP', lossless=text and not card_lossy, quality=95, method=6, icc_profile=image.info.get('icc_profile', b''), exact=True)
            identical = None
            if text and not card_lossy:
                decoded = Image.open(path).convert(image.mode)
                matches_encoded_source = resized.size == decoded.size and resized.tobytes() == decoded.tobytes()
                identical = width == image.width and matches_encoded_source
                if not matches_encoded_source:
                    raise ValueError('Lossless pixel mismatch: ' + key)
            variants.append({'path': path.relative_to(ROOT).as_posix(), 'width': resized.width,
                             'height': resized.height, 'bytes': path.stat().st_size,
                             'decoded_pixels_identical': identical, 'native_resolution': width == image.width, 'generated': True})
        if not text and variants[-1]['width'] < image.width:
            variants.append({'path': key, 'width': image.width, 'height': image.height,
                             'bytes': original.stat().st_size, 'decoded_pixels_identical': None,
                             'native_resolution': True, 'generated': False})
        native_path = variants[-1]['path'] if variants[-1]['bytes'] < original.stat().st_size else key
        native_quality = NATIVE_QUALITY.get(key)
        if native_quality:
            path = original.with_name(original.stem + '.reading-native-q' + str(native_quality) + '.webp')
            image.save(path, 'WEBP', quality=native_quality, method=6, icc_profile=image.info.get('icc_profile', b''))
            if path.stat().st_size >= original.stat().st_size:
                raise ValueError('Native recompression must be smaller: ' + key)
            native_path = path.relative_to(ROOT).as_posix()
        result['images'][key] = {**meta, 'original_bytes': original.stat().st_size,
                                'lossless_reference': variants[-1] if text else None,
                                'native_reading_path': native_path,
                                'native_reading_bytes': (ROOT / native_path).stat().st_size,
                                'native_reading_quality': native_quality,
                                'native_reading_pixels_identical': text and not native_quality,
                                'reading_native_only': text,
                                'original_preserved_for_reading': text and native_path == key,
                                'width': image.width, 'height': image.height,
                                'text_or_screenshot': text or meta['cover'],
                                'article_reading_native_only': text and meta['article'] and key not in RESPONSIVE_ARTICLE_TEXT,
                                'article_min_width': 960 if key in RESPONSIVE_ARTICLE_TEXT else None,
                                'lossless': text, 'variants': variants}
        item = result['images'][key]
        if key in typography_keys:
            item['cache_version'] = hashlib.sha256(original.read_bytes()).hexdigest()[:12]
        native = {'path': native_path, 'width': image.width, 'height': image.height,
                  'bytes': item['native_reading_bytes'], 'native_resolution': True,
                  'decoded_pixels_identical': text and not native_quality,
                  'generated': native_path != key}
        item['variants'] = ([v for v in variants[:-1] if v['bytes'] < item['original_bytes']] + [native]) if meta['cover'] or not text or key in RESPONSIVE_ARTICLE_TEXT else [native]
        print(key + ': ' + str(original.stat().st_size) + ' -> ' + str(variants[-1]['bytes']), flush=True)
    MANIFEST.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return result


def relative_url(key, page):
    import os
    return Path(os.path.relpath(ROOT / key, (ROOT / page).parent)).as_posix()


def reading_attributes(src, page_path='index.html', manifest=None):
    """Attributes for an image, or {}. page_path is relative to the repository root."""
    if manifest is None:
        manifest = json.loads(MANIFEST.read_text(encoding='utf-8')) if MANIFEST.exists() else {'images': {}}
    key = local_path(src, page_path)
    item = manifest['images'].get(key)
    if not item or (page_path != 'index.html' and not item['article']):
        return {}
    variants = list(item['variants'])
    if item.get('native_reading_quality') and page_path != 'index.html':
        variants[-1] = {'path': item['native_reading_path'], 'width': item['width'],
                        'height': item['height'], 'bytes': item['native_reading_bytes']}
    native = {'path': key, 'width': item['width'], 'height': item['height'], 'bytes': item['original_bytes']}
    if variants[-1]['bytes'] >= item['original_bytes']:
        variants[-1] = native
    # A resized candidate should never cost more than its original fallback.
    variants = [v for v in variants if v['bytes'] < item['original_bytes'] or v['path'] == key]
    if item['lossless'] and page_path != 'index.html':
        variants = ([v for v in variants if v['width'] >= 960]
                    if key in RESPONSIVE_ARTICLE_TEXT else variants[-1:])
    sizes = '(max-width: 860px) calc(100vw - 40px), 320px' if page_path == 'index.html' else '(max-width: 860px) calc(100vw - 40px), 780px'
    # Content-address the revised typography so cached old covers cannot survive
    # a deployment. Keep data-full-src canonical for idempotent rebuilding.
    version = item.get('cache_version')
    def versioned(url):
        return urlsplit(url).path + '?v=' + version if version else url
    return {'src': urlsplit(src).path if version else src,
            'srcset': ', '.join(versioned(relative_url(v['path'], page_path)) + ' ' + str(v['width']) + 'w' for v in variants),
            'sizes': sizes, 'data-full-src': urlsplit(src).path if version else src}


def optimize_html(content, page_path='index.html', manifest=None):
    """Idempotent replacement of img attributes only; captions and ad blocks untouched."""
    if manifest is None:
        manifest = json.loads(MANIFEST.read_text(encoding='utf-8')) if MANIFEST.exists() else {'images': {}}
    def update(match):
        tag = match.group(0)
        attrs = {k.lower(): v for k, _, v in ATTR.findall(tag)}
        original = html_module.unescape(attrs.get('data-full-src', attrs.get('src', '')))
        additions = reading_attributes(original, page_path, manifest)
        if not additions:
            return tag
        if page_path == 'index.html' and 'guide-cover' not in attrs.get('class', '').split():
            additions['sizes'] = '112px'
        for name, value in additions.items():
            rendered = name + '="' + html_module.escape(value, quote=True) + '"'
            pattern = re.compile(r'(?<![\w:-])' + re.escape(name) + r'\s*=\s*(["\']).*?\1', re.S | re.I)
            tag = pattern.sub(lambda _: rendered, tag, count=1) if pattern.search(tag) else re.sub(r'\s*/?>$', lambda m: ' ' + rendered + m.group(0), tag, count=1)
        return tag
    return IMG.sub(update, content)


def apply_articles():
    count = 0
    for page in sorted(ROOT.glob('claude-ai/*/index.html')):
        before = page.read_text(encoding='utf-8')
        after = optimize_html(before, page.relative_to(ROOT).as_posix())
        if after != before:
            page.write_text(after, encoding='utf-8')
            count += 1
    print('Updated article pages: ' + str(count))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generate', action='store_true')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if args.generate:
        generate()
    if args.apply:
        apply_articles()
    if not args.generate and not args.apply:
        print(json.dumps(inventory(), ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
