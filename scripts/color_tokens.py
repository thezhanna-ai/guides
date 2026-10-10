"""Build-time color tokens, using a lossless CSS declaration lexer.

Only fixed color values are replaced. Selectors, quoted strings, URL contents,
comments, custom-property declarations and immutable advertising blocks stay intact.
The explicit shared palette is reviewed source, never an automatically invented theme.
"""
import re
from decimal import Decimal

# Standard CSS named colors are data, not a dependency on a CSS runtime parser.
NAMED = {'transparent': 'rgba(0,0,0,0)', 'black': '#000000', 'silver': '#c0c0c0', 'gray': '#808080', 'white': '#ffffff', 'maroon': '#800000', 'red': '#ff0000', 'purple': '#800080', 'fuchsia': '#ff00ff', 'green': '#008000', 'lime': '#00ff00', 'olive': '#808000', 'yellow': '#ffff00', 'navy': '#000080', 'blue': '#0000ff', 'teal': '#008080', 'aqua': '#00ffff', 'aliceblue': '#f0f8ff', 'antiquewhite': '#faebd7', 'aquamarine': '#7fffd4', 'azure': '#f0ffff', 'beige': '#f5f5dc', 'bisque': '#ffe4c4', 'blanchedalmond': '#ffebcd', 'blueviolet': '#8a2be2', 'brown': '#a52a2a', 'burlywood': '#deb887', 'cadetblue': '#5f9ea0', 'chartreuse': '#7fff00', 'chocolate': '#d2691e', 'coral': '#ff7f50', 'cornflowerblue': '#6495ed', 'cornsilk': '#fff8dc', 'crimson': '#dc143c', 'cyan': '#00ffff', 'darkblue': '#00008b', 'darkcyan': '#008b8b', 'darkgoldenrod': '#b8860b', 'darkgray': '#a9a9a9', 'darkgreen': '#006400', 'darkgrey': '#a9a9a9', 'darkkhaki': '#bdb76b', 'darkmagenta': '#8b008b', 'darkolivegreen': '#556b2f', 'darkorange': '#ff8c00', 'darkorchid': '#9932cc', 'darkred': '#8b0000', 'darksalmon': '#e9967a', 'darkseagreen': '#8fbc8f', 'darkslateblue': '#483d8b', 'darkslategray': '#2f4f4f', 'darkslategrey': '#2f4f4f', 'darkturquoise': '#00ced1', 'darkviolet': '#9400d3', 'deeppink': '#ff1493', 'deepskyblue': '#00bfff', 'dimgray': '#696969', 'dimgrey': '#696969', 'dodgerblue': '#1e90ff', 'firebrick': '#b22222', 'floralwhite': '#fffaf0', 'forestgreen': '#228b22', 'gainsboro': '#dcdcdc', 'ghostwhite': '#f8f8ff', 'gold': '#ffd700', 'goldenrod': '#daa520', 'greenyellow': '#adff2f', 'grey': '#808080', 'honeydew': '#f0fff0', 'hotpink': '#ff69b4', 'indianred': '#cd5c5c', 'indigo': '#4b0082', 'ivory': '#fffff0', 'khaki': '#f0e68c', 'lavender': '#e6e6fa', 'lavenderblush': '#fff0f5', 'lawngreen': '#7cfc00', 'lemonchiffon': '#fffacd', 'lightblue': '#add8e6', 'lightcoral': '#f08080', 'lightcyan': '#e0ffff', 'lightgoldenrodyellow': '#fafad2', 'lightgray': '#d3d3d3', 'lightgreen': '#90ee90', 'lightgrey': '#d3d3d3', 'lightpink': '#ffb6c1', 'lightsalmon': '#ffa07a', 'lightseagreen': '#20b2aa', 'lightskyblue': '#87cefa', 'lightslategray': '#778899', 'lightslategrey': '#778899', 'lightsteelblue': '#b0c4de', 'lightyellow': '#ffffe0', 'limegreen': '#32cd32', 'linen': '#faf0e6', 'magenta': '#ff00ff', 'mediumaquamarine': '#66cdaa', 'mediumblue': '#0000cd', 'mediumorchid': '#ba55d3', 'mediumpurple': '#9370db', 'mediumseagreen': '#3cb371', 'mediumslateblue': '#7b68ee', 'mediumspringgreen': '#00fa9a', 'mediumturquoise': '#48d1cc', 'mediumvioletred': '#c71585', 'midnightblue': '#191970', 'mintcream': '#f5fffa', 'mistyrose': '#ffe4e1', 'moccasin': '#ffe4b5', 'navajowhite': '#ffdead', 'oldlace': '#fdf5e6', 'olivedrab': '#6b8e23', 'orange': '#ffa500', 'orangered': '#ff4500', 'orchid': '#da70d6', 'palegoldenrod': '#eee8aa', 'palegreen': '#98fb98', 'paleturquoise': '#afeeee', 'palevioletred': '#db7093', 'papayawhip': '#ffefd5', 'peachpuff': '#ffdab9', 'peru': '#cd853f', 'pink': '#ffc0cb', 'plum': '#dda0dd', 'powderblue': '#b0e0e6', 'rosybrown': '#bc8f8f', 'royalblue': '#4169e1', 'saddlebrown': '#8b4513', 'salmon': '#fa8072', 'sandybrown': '#f4a460', 'seagreen': '#2e8b57', 'seashell': '#fff5ee', 'sienna': '#a0522d', 'skyblue': '#87ceeb', 'slateblue': '#6a5acd', 'slategray': '#708090', 'slategrey': '#708090', 'snow': '#fffafa', 'springgreen': '#00ff7f', 'steelblue': '#4682b4', 'tan': '#d2b48c', 'thistle': '#d8bfd8', 'tomato': '#ff6347', 'turquoise': '#40e0d0', 'violet': '#ee82ee', 'wheat': '#f5deb3', 'whitesmoke': '#f5f5f5', 'yellowgreen': '#9acd32', 'rebeccapurple': '#663399'}
COLOR_PROPERTIES = re.compile(r'^(?:color|background(?:-[\w-]+)?|border(?:-[\w-]+)?|outline(?:-[\w-]+)?|(?:box|text)-shadow|fill|stroke|text-decoration(?:-color)?|caret-color|column-rule(?:-color)?|filter|(?:-webkit-)?mask(?:-[\w-]+)?|stop-color|flood-color|lighting-color|accent-color|scrollbar-color|-webkit-(?:tap-highlight-color|text-fill-color|text-stroke(?:-color)?))$', re.I)
PROP = re.compile(r'(?:\s|/\*.*?\*/)*([-\w]+)\s*:', re.S)
WORD = re.compile(r'[-\w]+')
HEX = re.compile(r'#[0-9a-fA-F]+')


def canonical_color(value):
    value = value.strip().lower()
    value = NAMED.get(value, value)
    if value.startswith('#'):
        h = value[1:]
        if len(h) in (3, 4):
            h = ''.join(x * 2 for x in h)
        if len(h) not in (6, 8) or not re.fullmatch(r'[0-9a-f]+', h):
            return None
        rgb = [str(int(h[n:n+2], 16)) for n in (0, 2, 4)]
        alpha = str(Decimal(int(h[6:8], 16)) / Decimal(255)) if len(h) == 8 else '1'
        return ','.join(rgb + [alpha])
    match = re.fullmatch(r'rgba?\(([^()]*)\)', value)
    if match:
        parts = [x.strip() for x in match[1].split(',')]
        if len(parts) not in (3, 4) or any(not re.fullmatch(r'[\d.]+', x) for x in parts):
            return None
        if len(parts) == 3:
            parts.append('1')
        return ','.join(format(Decimal(x).normalize(), 'f') for x in parts)
    return None


def skip_string(source, start):
    quote = source[start]
    i = start + 1
    while i < len(source):
        if source[i] == '\\':
            i += 2
        elif source[i] == quote:
            return i + 1
        else:
            i += 1
    return len(source)


def skip_parens(source, start):
    depth = 0
    i = start
    while i < len(source):
        if source.startswith('/*', i):
            end = source.find('*/', i + 2)
            i = len(source) if end == -1 else end + 2
            continue
        if source[i] in ('"', "'"):
            i = skip_string(source, i)
            continue
        if source[i] == '(':
            depth += 1
        elif source[i] == ')':
            depth -= 1
            if not depth:
                return i + 1
        i += 1
    return len(source)


def value_colors(source, start, end):
    i = start
    while i < end:
        if source.startswith('/*', i):
            close = source.find('*/', i + 2)
            i = end if close == -1 else close + 2
        elif source[i] in ('"', "'"):
            i = skip_string(source, i)
        elif source[i] == '#':
            m = HEX.match(source, i)
            if m and len(m[0]) in (4, 5, 7, 9):
                yield i, m.end(), m[0], canonical_color(m[0])
            i = m.end() if m else i + 1
        elif WORD.match(source, i):
            m = WORD.match(source, i)
            word = m[0].lower()
            if m.end() < end and source[m.end()] == '(' and word in ('url', 'rgb', 'rgba', 'hsl', 'hsla'):
                stop = skip_parens(source, m.end())
                if word != 'url':
                    color = canonical_color(source[i:stop])
                    if color:
                        yield i, stop, source[i:stop], color
                    elif 'var(' not in source[i:stop]:
                        raise ValueError('Add an explicit parser before using this fixed color syntax: ' + source[i:stop])
                i = stop
            else:
                if word in NAMED:
                    yield i, m.end(), m[0], canonical_color(m[0])
                i = m.end()
        else:
            i += 1


def color_spans(source, inline=False):
    """Yield only colors in declaration values, never selector or custom-property text."""
    start = 0
    i = 0
    depth = 0
    def statement(end):
        m = PROP.match(source, start, end)
        if m and not m[1].startswith('--') and COLOR_PROPERTIES.fullmatch(m[1]):
            yield from value_colors(source, m.end(), end)
    while i < len(source):
        if source.startswith('/*', i):
            close = source.find('*/', i + 2)
            i = len(source) if close == -1 else close + 2
            continue
        if source[i] in ('"', "'"):
            i = skip_string(source, i)
            continue
        if source[i] == '(':
            depth += 1
        elif source[i] == ')':
            depth -= 1
        elif not depth and source[i] in '{};':
            if source[i] in '};':
                yield from statement(i)
            start = i + 1
        i += 1
    if inline:
        yield from statement(len(source))


def palette_entries(css):
    entries = {}
    names = set()
    for name, value in re.findall(r'(--guide-color-[\w-]+)\s*:\s*([^;{}]+);', css):
        canonical = canonical_color(value)
        if canonical is None or canonical in entries or name in names:
            raise ValueError('Invalid or duplicate palette primitive: ' + name)
        names.add(name)
        entries[canonical] = (name, value.strip())
    return entries


def tokenize_css(css, entries, inline=False):
    spans = list(color_spans(css, inline))
    for start, end, literal, canonical in reversed(spans):
        if canonical not in entries:
            raise ValueError('Unknown color ' + literal + '. Add a named primitive to assets/palette.css')
        css = css[:start] + 'var(' + entries[canonical][0] + ')' + css[end:]
    return css


def expand_palette(css, entries):
    names = {name: value for name, value in entries.values()}
    return re.sub(r'var\((--guide-color-[\w-]+)\)', lambda m: names[m[1]], css)


def html_style_chunks(source):
    """Return CSS spans; advertising markup and its canonical erid styles are immutable."""
    protected = [(m.start(), m.end()) for m in re.finditer(r'<!-- erid:style:start -->.*?<!-- erid:style:end -->|<section\b[^>]*class="cta"[^>]*>.*?</section>', source, re.S)]
    def allowed(start):
        return not any(a <= start < b for a, b in protected)
    for m in re.finditer(r'<style\b([^>]*)>(.*?)</style>', source, re.S | re.I):
        if allowed(m.start()) and not re.search(r'id=[\'\"]guide-palette[\'\"]', m[1]):
            yield m.start(2), m.end(2), m[2], False
    for m in re.finditer(r'<[a-z][^>]*\bstyle\s*=\s*([\'\"])(.*?)\1[^>]*>', source, re.S | re.I):
        if allowed(m.start()):
            yield m.start(2), m.end(2), m[2], True


def tokenize_html(source, entries):
    for start, end, css, inline in sorted(html_style_chunks(source), reverse=True):
        source = source[:start] + tokenize_css(css, entries, inline) + source[end:]
    return source


def embed_palette(source, palette_css):
    block = '<!-- palette:start -->\n<style id="guide-palette">\n' + palette_css.strip() + '\n</style>\n<!-- palette:end -->\n'
    source = re.sub(r'<!-- palette:start -->.*?<!-- palette:end -->\s*', '', source, flags=re.S)
    m = re.search(r'<style\b|<link\b(?=[^>]*\brel=[\'\"]stylesheet[\'\"])', source, re.I)
    if not m:
        raise ValueError('Palette requires an existing stylesheet position')
    return source[:m.start()] + block + source[m.start():]


def main():
    """Validate all known primitives before migration, or reject un-tokenized declarations."""
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    entries = palette_entries((root / 'assets/palette.css').read_text(encoding='utf-8'))
    paths = [root / 'index.html', root / 'politika/index.html',
             *sorted(root.glob('claude-ai/*/index.html')),
             root / 'scripts/shablon_glavnoy.html', root / 'scripts/shablon_politiki.html',
             root / 'assets/quality.css', root / 'assets/privacy.css', root / 'assets/promty-foto.css']
    pending = []
    for path in paths:
        old = path.read_text(encoding='utf-8')
        new = tokenize_css(old, entries) if path.suffix == '.css' else tokenize_html(old, entries)
        # Expand validates every referenced primitive, including already tokenized pages.
        expand_palette(new, entries)
        if old != new:
            pending.append((path, new))
    if args.check and pending:
        parser.exit(1, 'Untokenized colors: ' + ', '.join(str(p.relative_to(root)) for p, _ in pending) + '\n')
    if args.apply:
        # Validate the complete batch before writing any file.
        for path, new in pending:
            path.write_text(new, encoding='utf-8')
    print('Palette ' + ('CHECK PASS' if args.check else 'APPLIED')
          + ': ' + str(len(paths)) + ' files, ' + str(len(entries)) + ' reviewed primitives, '
          + str(len(pending)) + ' changed files')


if __name__ == '__main__':
    main()
