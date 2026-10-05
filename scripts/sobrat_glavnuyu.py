#!/usr/bin/env python3
"""Сборка index.html из реестра data/statyi.json.

Руками index.html НЕ править: любая правка затрётся следующей сборкой.
Новая статья = запись в реестре, потом `python3 scripts/sobrat_glavnuyu.py`.
Краткое содержание карточек и подписи обложек = kratko и podpis в реестре.
Сборка также обновляет figcaption обложки cover-v2 и robots-метатеги статей,
sitemap.xml и robots.txt. Индексация: status=live без noindex_reason.
Обложки статей = data/OBLOZHKI.json (slug, путь, alt и размер).
Нет соответствия или файла картинки = тёмная заглушка с названием статьи.

Текст шапки, названия разделов и описания трасс лежат ниже в РАЗДЕЛЫ -
это содержание, которого нет в реестре, оно правится здесь.

Проверка без записи: `python3 scripts/sobrat_glavnuyu.py --proverit`
Возвращает код 1, если любой результат сборки расходится с реестром
"""

import json
import re
import sys
from pathlib import Path

KORNI = Path(__file__).resolve().parent.parent
REESTR = KORNI / "data" / "statyi.json"
OBLOZHKI = KORNI / "data" / "OBLOZHKI.json"
GLAVNAYA = KORNI / "index.html"
DOMEN = "https://pronovoe.com/"

SHAPKA = {
    "nadzagolovok": "Инструкции по нейросетям",
    "h1": "Нейросети работают",
    "h1_akcent": "на тебя",
    "lead": "Надо только научиться ставить задачу. Здесь инструкции и разборы - от первой кнопки до собранных проектов",
    "intro": "Начни с простого: отдай нейросети рутину, которая съедает твой день - посчитать, написать, разобрать, оформить. Дальше научишься собирать свои проекты, находить решения для своего дела и делать то, что раньше отдавали на сторону",
    "title": "Нейросети работают на тебя",
    "description": "Инструкции, разборы и гайды по нейросетям для не-программистов: от первой кнопки до собственных проектов",
    "podval": "Гайды обновляются регулярно - если нужной инструкции ещё нет, она уже готовится",
}

UROVNI = {
    "green": ("Сможет любой", "если открываешь нейросеть впервые"),
    "blue": ("Нужен опыт", "если уже работаешь и хочешь собирать своё"),
}

# Метки поиска: код в реестре (поле metki) -> название в выпадающем списке и подпись.
# Порядок здесь = порядок в списке. «Другое» добавляется последним и открывает свободное поле
METKI = {
    "claude-chat": ("Claude", "чат"),
    "claude-code": ("Claude Code", "код"),
    "chatgpt": ("ChatGPT", "чат"),
    "codex": ("Codex", "код"),
    "sravnenie": ("Сравнение моделей", ""),
    "kartinki": ("Картинки", ""),
    "video": ("Видео", ""),
    "sayt": ("Сайт", ""),
    "bot": ("Бот", ""),
    "fayly": ("Файлы и документы", ""),
    "poisk": ("Поиск в интернете", ""),
    "golos": ("Голос", ""),
    "pochta": ("Почта и календарь", ""),
    "raspisanie": ("Расписание", ""),
    "proekty": ("Проекты", ""),
    "artefakty": ("Артефакты", ""),
    "pamyat": ("Память и настройки", ""),
    "privatnost": ("Приватность", ""),
    "modeli": ("Модели и лимиты", ""),
    "skilly": ("Скиллы и плагины", ""),
    "dostup": ("Доступ из России", ""),
    "oplata": ("Оплата", ""),
    "besplatno": ("Бесплатные сервисы", ""),
}

TIPY = {
    "instr": ("Инструкция", "kind-instr"),
    "razbor": ("Разбор", "kind-razbor"),
    "obzor": ("Обзор", "kind-obzor"),
}

ZNACHKI = {
    "dostup": "Металлический ключ как образ доступа и первых настроек",
    "claude": "Перо ручки как образ ежедневной работы с нейросетью",
    "kartinki": "Объектив как образ создания картинок и видео",
    "proekty": "Штангенциркуль как образ собственных проектов",
    "gpt": "Микросхема как образ полезных сервисов",
}

# Рубрики главной по порядку. "trassa" совпадает с полем rubrika в реестре,
# статьи подставляются автоматически. "ikonka" - файл в assets/glavnaya/razdely/
RAZDELY = [
    {
        "tag": "start",
        "ikonka": "dostup",
        "zagolovok": "С чего начать: доступ, оплата и первые настройки",
        "opisanie": "Как открыть Claude и ChatGPT, чем платить и что настроить в первый день",
        "trassy": [{"trassa": "start"}],
    },
    {
        "tag": "kazhdyy-den",
        "ikonka": "claude",
        "zagolovok": "Нейросеть на каждый день: поиск, файлы, голос, проекты",
        "opisanie": "Рутина, которую можно отдать уже сегодня",
        "trassy": [{"trassa": "kazhdyy-den"}],
    },
    {
        "tag": "kartinki",
        "ikonka": "kartinki",
        "zagolovok": "Картинки и видео",
        "opisanie": "Фото, постеры, ролики и честные сравнения моделей",
        "trassy": [{"trassa": "kartinki"}],
    },
    {
        "tag": "vaybkoding",
        "ikonka": "proekty",
        "zagolovok": "Вайбкодинг: свои сайты, боты и инструменты",
        "opisanie": "Собираешь своё руками агента, без программирования",
        "trassy": [{"trassa": "vaybkoding"}],
    },
    {
        "tag": "servisy",
        "ikonka": "gpt",
        "zagolovok": "Полезные сервисы и бесплатные замены",
        "opisanie": "Маленькие сайты и замены платным подпискам",
        "trassy": [{"trassa": "servisy"}],
    },
]


def ekranirovat(tekst):
    return (
        tekst.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


def zagruzit_statyi():
    reestr = json.loads(REESTR.read_text(encoding="utf-8"))
    po_trassam = {}
    for statya in reestr["statyi"]:
        if statya.get("status") != "live":
            continue
        neizvestnye = [m for m in statya.get("metki", []) if m not in METKI]
        if neizvestnye:
            raise ValueError("%s: неизвестные метки %s" % (statya["slug"], ", ".join(neizvestnye)))
        po_trassam.setdefault(statya["rubrika"], []).append(statya)
    return po_trassam


def zagruzit_oblozhki():
    return json.loads(OBLOZHKI.read_text(encoding="utf-8")) if OBLOZHKI.exists() else {}


def tekst_iz_reestra(statya, pole, limit):
    tekst = statya.get(pole)
    if (not isinstance(tekst, str) or not tekst.strip() or tekst != tekst.strip()
            or len(tekst) > limit or "\n" in tekst or "\r" in tekst):
        raise ValueError("%s: поле %s должно содержать одну строку от 1 до %d знаков"
                         % (statya["slug"], pole, limit))
    return tekst


def sobrat_podpisi():
    reestr = json.loads(REESTR.read_text(encoding="utf-8"))
    oblozhki = zagruzit_oblozhki()
    stranicy = {}
    figura = re.compile(r'<figure\b[^>]*\sclass="(?:[^"]*\s)?cover-v2(?:\s[^"]*)?"[^>]*>.*?</figure>', re.S)
    caption = re.compile(r'(<figcaption>).*?(</figcaption>)', re.S)
    for statya in reestr["statyi"]:
        if statya["slug"] not in oblozhki:
            continue
        podpis = tekst_iz_reestra(statya, "podpis", 100)
        page = (KORNI / "claude-ai" / statya["slug"] / "index.html").resolve()
        if not page.is_relative_to(KORNI) or not page.is_file():
            raise ValueError("%s: страница с обложкой должна находиться внутри сайта" % statya["slug"])
        html = page.read_text(encoding="utf-8")
        figures = list(figura.finditer(html))
        if len(figures) != 1 or len(caption.findall(figures[0].group())) != 1:
            raise ValueError("%s: нужна одна обложка cover-v2 с одной подписью" % statya["slug"])
        match = figures[0]
        cover = caption.sub(lambda m: m[1] + ekranirovat(podpis) + m[2], match.group(), count=1)
        stranicy[page] = html[:match.start()] + cover + html[match.end():]
    return stranicy


def sobrat_kartochku(statya, oblozhki):
    podpis, klass = TIPY[statya["tip"]]
    title = ekranirovat(statya["title"])
    oblozhka = oblozhki.get(statya["slug"])
    put = (KORNI / oblozhka["image"]).resolve() if oblozhka else None
    if put and not Path(oblozhka["image"]).is_absolute() and put.is_relative_to(KORNI) and put.is_file():
        media = (
            '<img class="guide-cover" src="{image}" alt="{alt}" '
            'width="{width}" height="{height}" loading="lazy" decoding="async">'
        ).format(
            image=ekranirovat(oblozhka["image"]),
            alt=ekranirovat(statya["title"] + ". " + oblozhka["alt"]),
            width=int(oblozhka["width"]),
            height=int(oblozhka["height"]),
        )
    else:
        media = '<span class="guide-cover guide-placeholder" aria-hidden="true">%s</span>' % title

    uroven = statya.get("uroven")
    podpis_urovnya = ""
    if uroven in UROVNI:
        podpis_urovnya = (
            '<span class="guide-level {kod}"><span class="track-dot {kod}" aria-hidden="true"></span>'
            '{nazvanie}</span>'
        ).format(kod=uroven, nazvanie=UROVNI[uroven][0])
    metki = statya.get("metki", [])
    return (
        '          <a class="guide-link" data-tags="{tags}" data-metki="{metki}" data-kod="{kod}" '
        'data-poisk="{poisk}" aria-label="{title}" href="claude-ai/{slug}/">'
        '{media}<span class="guide-body"><span class="guide-summary">{summary}</span>'
        '<span class="guide-meta">{uroven}<span class="kind {klass}">{podpis}</span></span>'
        '</span></a>'
    ).format(
        tags=ekranirovat(statya["tags"]),
        metki=ekranirovat(" ".join(metki)),
        slug=ekranirovat(statya["slug"]),
        media=media,
        uroven=podpis_urovnya,
        klass=klass,
        podpis=podpis,
        title=title,
        kod=ekranirovat(statya.get("kod_slovo", "")),
        poisk=ekranirovat(" ".join([statya["title"], *statya.get("ponyatiya", []),
                                    *(METKI[m][0] for m in metki)])),
        summary=ekranirovat(tekst_iz_reestra(statya, "kratko", 85)),
    )


def sobrat_trassu(trassa, po_trassam, oblozhki):
    statyi = po_trassam.get(trassa["trassa"], [])
    uroven = trassa.get("uroven")

    stroki = []
    atribut = ' data-track="%s"' % uroven if uroven else ""
    stroki.append('      <div class="track"%s>' % atribut)

    if uroven:
        podpis_urovnya = UROVNI[uroven][0]
        stroki.append('        <div class="track-head">')
        stroki.append('          <span class="track-dot %s" aria-hidden="true"></span>' % uroven)
        stroki.append('          <h3 class="track-name">%s</h3>' % ekranirovat(trassa["nazvanie"]))
        stroki.append(
            '          <span class="track-tag %s">%s уровень</span>' % (uroven, podpis_urovnya)
        )
        stroki.append("        </div>")
        stroki.append('        <p class="track-desc">%s</p>' % ekranirovat(trassa["opisanie"]))

    if statyi:
        stroki.append('        <div class="guides">')
        stroki.extend(sobrat_kartochku(s, oblozhki) for s in statyi)
        stroki.append("        </div>")
    else:
        stroki.append('        <span class="soon">%s</span>' % ekranirovat(trassa.get("pusto", "Статьи готовятся")))

    stroki.append("      </div>")
    return "\n".join(stroki)


def sobrat_razdel(razdel, po_trassam, oblozhki):
    stroki = [
        '    <section class="tool-block" id="r-%s" data-section="%s" aria-label="%s">'
        % (razdel["tag"], razdel["tag"], ekranirovat(razdel["zagolovok"])),
        '      <div class="tool-head">',
        '        <img class="section-icon" src="assets/glavnaya/razdely/%s.webp" alt="%s" '
        'width="600" height="600" loading="lazy" decoding="async">'
        % (razdel["ikonka"], ekranirovat(ZNACHKI[razdel["ikonka"]])),
        '        <div class="tool-heading">',
        "          <h2>%s</h2>" % ekranirovat(razdel["zagolovok"]),
        "          <p>%s</p>" % ekranirovat(razdel["opisanie"]),
        "        </div>",
        "      </div>",
        "",
    ]
    stroki.append("\n\n".join(sobrat_trassu(t, po_trassam, oblozhki) for t in razdel["trassy"]))
    stroki.append("    </section>")
    return "\n".join(stroki)


def sobrat_filtry():
    punkty = ['        <option value="all">Все метки</option>']
    for kod, (nazvanie, podpis) in METKI.items():
        tekst = nazvanie + (" (%s)" % podpis if podpis else "")
        punkty.append('        <option value="%s">%s</option>' % (kod, ekranirovat(tekst)))
    punkty.append('        <option value="drugoe">Другое: своё слово</option>')
    return "\n".join(punkty)


def sobrat_navigaciyu():
    return "\n".join(
        '        <a href="#r-%s">%s</a>' % (razdel["tag"], ekranirovat(razdel["zagolovok"]))
        for razdel in RAZDELY
    )


def sobrat_urovni():
    stroki = []
    for kod, (nazvanie, poyasnenie) in UROVNI.items():
        stroki.append(
            '      <li><span class="track-dot %s" aria-hidden="true"></span>'
            "<span><b>%s</b> - %s</span></li>" % (kod, nazvanie, poyasnenie)
        )
    return "\n".join(stroki)


def sobrat_stranicu():
    po_trassam = zagruzit_statyi()
    oblozhki = zagruzit_oblozhki()
    shablon = (KORNI / "scripts" / "shablon_glavnoy.html").read_text(encoding="utf-8")
    return shablon.format(
        title=ekranirovat(SHAPKA["title"]),
        description=ekranirovat(SHAPKA["description"]),
        nadzagolovok=ekranirovat(SHAPKA["nadzagolovok"]),
        h1=ekranirovat(SHAPKA["h1"]),
        h1_akcent=ekranirovat(SHAPKA["h1_akcent"]),
        chislo=sum(len(v) for v in po_trassam.values()),
        navigaciya=sobrat_navigaciyu(),
        lead=ekranirovat(SHAPKA["lead"]),
        intro=ekranirovat(SHAPKA["intro"]),
        urovni=sobrat_urovni(),
        filtry=sobrat_filtry(),
        razdely="\n\n".join(sobrat_razdel(r, po_trassam, oblozhki) for r in RAZDELY),
        podval=ekranirovat(SHAPKA["podval"]),
    )


METKA_STIL = {
    "green": "background:#E4F1E8;color:#2F7448",
    "blue": "background:#E4EDF5;color:#2C6FA6",
}


def sobrat_metki_urovnya(stranicy):
    """Метка уровня под заголовком каждой живой статьи, из поля uroven реестра."""
    reestr = json.loads(REESTR.read_text(encoding="utf-8"))
    staraya = re.compile(r'\n?<p class="uroven-metka[^"]*"[^>]*>.*?</p>', re.S)
    for statya in reestr["statyi"]:
        uroven = statya.get("uroven")
        if statya.get("status") != "live" or uroven not in UROVNI:
            continue
        page = (KORNI / "claude-ai" / statya["slug"] / "index.html").resolve()
        if not page.is_relative_to(KORNI) or not page.is_file():
            continue  # путь проверяет сборка индексации и падает с понятной ошибкой
        html = stranicy.get(page, page.read_text(encoding="utf-8"))
        html = staraya.sub("", html)
        if html.count("</h1>") < 1:
            raise ValueError("%s: нет заголовка h1 для метки уровня" % statya["slug"])
        metka = ('\n<p class="uroven-metka %s" style="display:inline-block;margin:16px 0 0;padding:5px 12px;'
                 'border-radius:999px;%s;font:700 13px/1.3 -apple-system,BlinkMacSystemFont,&quot;Segoe UI&quot;,'
                 'Arial,sans-serif">%s</p>' % (uroven, METKA_STIL[uroven], UROVNI[uroven][0]))
        html = html.replace("</h1>", "</h1>" + metka, 1)
        stranicy[page] = html
    return stranicy


def sobrat_indeksaciyu(podpisi):
    """Единая политика noindex и sitemap, поверх уже собранных подписей."""
    reestr = json.loads(REESTR.read_text(encoding="utf-8"))
    stranicy = {}
    adresy = [DOMEN]
    robots_tag = re.compile(r'<meta\b(?=[^>]*\bname\s*=\s*[\'"]robots[\'"])[^>]*>\s*', re.I)
    zapret = '<meta name="robots" content="noindex, nofollow">'
    slugi = set()
    for statya in reestr["statyi"]:
        slug = statya["slug"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) or slug in slugi:
            raise ValueError("Некорректный или повторный slug: %s" % slug)
        slugi.add(slug)
        page = (KORNI / "claude-ai" / slug / "index.html").resolve()
        if not page.is_relative_to(KORNI) or not page.is_file():
            raise ValueError("%s: страница должна находиться внутри сайта" % slug)
        html = podpisi.get(page, page.read_text(encoding="utf-8"))
        indeksirovat = statya.get("status") == "live" and not statya.get("noindex_reason")
        if indeksirovat:
            html = robots_tag.sub(lambda match: "" if re.search(r"\b(noindex|nofollow|none)\b", match.group(), re.I)
                                  else match.group(), html)
            adresy.append(DOMEN + "claude-ai/" + slug + "/")
        elif robots_tag.search(html):
            # Удерживаем запрет и не меняем исходный HTML уже закрытых страниц.
            html = robots_tag.sub(lambda match: zapret + match.group()[match.group().index(">") + 1:], html)
        else:
            if not re.search(r"</head\s*>", html, re.I):
                raise ValueError("%s: отсутствует закрывающий тег head" % slug)
            html = re.sub(r"</head\s*>", zapret + "\n</head>", html, count=1, flags=re.I)
        stranicy[page] = html

    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sitemap.extend("  <url><loc>%s</loc></url>" % ekranirovat(adres) for adres in adresy)
    sitemap.append("</urlset>")
    stranicy[KORNI / "sitemap.xml"] = "\n".join(sitemap) + "\n"
    stranicy[KORNI / "robots.txt"] = "User-agent: *\nAllow: /\n\nSitemap: " + DOMEN + "sitemap.xml\n"
    return stranicy


def main():
    stranica = sobrat_stranicu()
    podpisi = sobrat_metki_urovnya(sobrat_podpisi())
    rezultaty = {GLAVNAYA: stranica, **sobrat_indeksaciyu(podpisi)}
    proverka = "--proverit" in sys.argv

    if proverka:
        razlichiya = [page for page, html in rezultaty.items()
                     if not page.exists() or page.read_text(encoding="utf-8") != html]
        if not razlichiya:
            print("Главная совпадает с реестром")
            print("Подписи %d статей совпадают с реестром" % len(podpisi))
            print("Индексация %d статей, sitemap.xml и robots.txt совпадают с реестром"
                  % (len(rezultaty) - 3))
            return 0
        for page in razlichiya:
            print("РАСХОЖДЕНИЕ: %s не совпадает с реестром" % page.relative_to(KORNI))
        print("Пересобрать: python3 scripts/sobrat_glavnuyu.py")
        return 1

    for page, html in rezultaty.items():
        if not page.exists() or page.read_text(encoding="utf-8") != html:
            page.write_text(html, encoding="utf-8")
    print("Подписи %d статей собраны из реестра" % len(podpisi))
    print("Индексация %d статей, sitemap.xml и robots.txt собраны из реестра" % (len(rezultaty) - 3))
    po_trassam = zagruzit_statyi()
    vsego = sum(len(v) for v in po_trassam.values())
    print("Собрано: %s, статей на главной %d" % (GLAVNAYA.name, vsego))
    for razdel in RAZDELY:
        for trassa in razdel["trassy"]:
            kolvo = len(po_trassam.get(trassa["trassa"], []))
            print("  %-22s %d" % (trassa["trassa"], kolvo))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
