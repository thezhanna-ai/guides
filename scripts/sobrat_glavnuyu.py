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


def privacy_fragment(name):
    return (KORNI / "scripts" / name).read_text(encoding="utf-8").strip()


def dobavit_privacy(html):
    """Один локальный загрузчик и одна плашка, без внешних запросов из HTML."""
    html = ubrat_seo(html)
    html = re.sub(r'<!-- privacy:(head|footer|banner):start -->.*?<!-- privacy:\1:end -->\s*',
                  '', html, flags=re.S)
    head = ('<!-- privacy:head:start -->\n'
            '<link rel="stylesheet" href="/assets/privacy.css">\n'
            '<script defer src="/assets/privacy.js"></script>\n'
            '<!-- privacy:head:end -->\n')
    footer = ('<!-- privacy:footer:start -->\n<div class="privacy-footer">'
              '<a href="/politika/">Политика данных</a>'
              '<button type="button" data-cookie-settings>Настройки аналитики</button>'
              '</div>\n<!-- privacy:footer:end -->\n')
    if not re.search(r'</footer\s*>', html, re.I):
        html = re.sub(r'</body\s*>', '<footer class="privacy-site-footer">\n</footer>\n</body>', html, count=1, flags=re.I)
    for tag in ('head', 'footer', 'body'):
        if len(re.findall(r'</' + tag + r'\s*>', html, re.I)) != 1:
            raise ValueError('Для политики нужен один закрывающий тег ' + tag)
    html = re.sub(r'</head\s*>', lambda _: head + '</head>', html, flags=re.I)
    html = re.sub(r'</footer\s*>', lambda _: footer + '</footer>', html, flags=re.I)
    return re.sub(r'</body\s*>', lambda _: privacy_fragment('privacy-banner.html') + '\n</body>', html, flags=re.I)


def sobrat_politiku():
    return seo_for_page(dobavit_privacy(privacy_fragment('shablon_politiki.html') + '\n'), 'politika/index.html')

SHAPKA = {
    "nadzagolovok": "Инструкции по нейросетям",
    "h1": "Нейросети работают",
    "h1_akcent": "на тебя",
    "lead": "Надо только научиться ставить задачу. Здесь инструкции и разборы - от первой кнопки до собранных проектов",
    "intro": "Начни с простого: отдай нейросети рутину, которая съедает твой день - посчитать, написать, разобрать, оформить. Дальше научишься собирать свои проекты, находить решения для своего дела и делать то, что раньше отдавали на сторону",
    "title": "Нейросети работают на тебя",
    "description": "Инструкции, разборы и гайды по нейросетям для не-программистов: от первой кнопки до собственных проектов",
    "podval": "Гайды обновляются регулярно - если нужной инструкции ещё нет, она уже готовится",
    "avtor_imya": "Жанна Слепова",
    "kontakt": "pronovoe.site@yandex.ru",
    "avtor_tekst": "Более 25 лет в финансах в проектном учёте: Big 4 и российский IT консалтинг. "
                   "Работа, где разные учетные системы интегрируются между собой и работают как единое целое. "
                   "С\u00a02025 года - нейросети и вайбкодинг, обучение у лучших на рынке. "
                   "Тот же системный подход: разобраться, как всё устроено, собрать в работающую связку и объяснить сложное простыми словами",
    "podval_avtor": "Ведёт Жанна Слепова - более 25 лет в финансах, с 2025 года в нейросетях",
}

UROVNI = {
    "green": ("Начальный", "только знакомишься с нейросетью"),
    "blue": ("Средний", "уже уверенно работаешь с нейросетью"),
}

# Метки-инструменты: их названия стоят на карточке над кратким содержанием
INSTRUMENTY = ["claude-chat", "claude-code", "chatgpt", "codex"]

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
        rubriki = [r["tag"] for r in RAZDELY]
        if statya.get("rubrika") not in rubriki:
            raise ValueError("%s: у живой статьи должно быть поле rubrika, одно из: %s"
                             % (statya["slug"], ", ".join(rubriki)))
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
            '{nazvanie} уровень</span>'
        ).format(kod=uroven, nazvanie=UROVNI[uroven][0])
    metki = statya.get("metki", [])
    return (
        '          <a class="guide-link" data-tags="{tags}" data-metki="{metki}" data-kod="{kod}" '
        'data-poisk="{poisk}" aria-label="{title}" href="claude-ai/{slug}/">'
        '{media}<span class="guide-body">{instrumenty}<span class="guide-summary">{summary}</span>'
        '<span class="guide-meta">{uroven}<span class="kind {klass}">{podpis}</span></span>'
        '</span></a>'
    ).format(
        tags=ekranirovat(statya["tags"]),
        metki=ekranirovat(" ".join(metki)),
        instrumenty=('<span class="guide-tools">%s</span>' % " · ".join("%s (%s)" % METKI[m] for m in INSTRUMENTY if m in metki)
                     if any(m in metki for m in INSTRUMENTY) else ""),
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
    punkty = ['        <option value="all">Все темы</option>']
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


def chislo_instrukciy(n):
    if n % 10 == 1 and n % 100 != 11:
        return "инструкция по шагам"
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return "инструкции по шагам"
    return "инструкций по шагам"


def sobrat_novoe(po_trassam, oblozhki, skolko=3):
    """Три последние статьи по дате публикации: свежая статья к сегодняшнему ролику видна сразу"""
    # при одной дате выше та, что позже добавлена в реестр
    poryadok = {s["slug"]: i for i, s in enumerate(json.loads((KORNI / "data" / "statyi.json").read_text(encoding="utf-8"))["statyi"])}
    vse = [s for v in po_trassam.values() for s in v if s.get("data_publikacii")]
    vse.sort(key=lambda s: (s["data_publikacii"], poryadok.get(s["slug"], 0)), reverse=True)
    stroki = []
    for s in vse[:skolko]:
        ob = oblozhki.get(s["slug"], {})
        kartinka = ('<img src="%s" alt="%s" width="1600" height="840" loading="lazy" decoding="async">' % (ekranirovat(ob["image"]), ekranirovat(ob.get("alt", s["title"])))
                    if ob.get("image") else "")
        stroki.append('        <a class="novoe-link" href="claude-ai/%s/">%s<span>%s</span></a>'
                      % (ekranirovat(s["slug"]), kartinka, ekranirovat(s["title"])))
    return "\n".join(stroki)


def sobrat_stranicu():
    po_trassam = zagruzit_statyi()
    oblozhki = zagruzit_oblozhki()
    shablon = (KORNI / "scripts" / "shablon_glavnoy.html").read_text(encoding="utf-8")
    return seo_for_page(dobavit_privacy(shablon.format(
        title=ekranirovat(SHAPKA["title"]),
        description=ekranirovat(SHAPKA["description"]),
        nadzagolovok=ekranirovat(SHAPKA["nadzagolovok"]),
        h1=ekranirovat(SHAPKA["h1"]),
        h1_akcent=ekranirovat(SHAPKA["h1_akcent"]),
        chislo=sum(len(v) for v in po_trassam.values()),
        chislo_slovo=chislo_instrukciy(sum(len(v) for v in po_trassam.values())),
        novoe=sobrat_novoe(po_trassam, oblozhki),
        navigaciya=sobrat_navigaciyu(),
        lead=ekranirovat(SHAPKA["lead"]),
        intro=ekranirovat(SHAPKA["intro"]),
        urovni=sobrat_urovni(),
        filtry=sobrat_filtry(),
        razdely="\n\n".join(sobrat_razdel(r, po_trassam, oblozhki) for r in RAZDELY),
        podval=ekranirovat(SHAPKA["podval"]),
        avtor_imya=ekranirovat(SHAPKA["avtor_imya"]),
        kontakt=ekranirovat(SHAPKA["kontakt"]),
        avtor_tekst=ekranirovat(SHAPKA["avtor_tekst"]),
        podval_avtor=ekranirovat(SHAPKA["podval_avtor"]),
    )), "index.html")


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
        if statya.get("status") != "live":
            continue
        page = (KORNI / "claude-ai" / statya["slug"] / "index.html").resolve()
        if not page.is_relative_to(KORNI) or not page.is_file():
            continue  # путь проверяет сборка индексации и падает с понятной ошибкой
        html = stranicy.get(page, page.read_text(encoding="utf-8"))
        html = staraya.sub("", html)
        if uroven not in UROVNI:
            # обзор без уровня: метку снимаем, если стояла
            stranicy[page] = html
            continue
        if html.count("</h1>") < 1:
            raise ValueError("%s: нет заголовка h1 для метки уровня" % statya["slug"])
        metka = ('\n<p class="uroven-metka %s" style="display:inline-block;margin:16px 0 0;padding:5px 12px;'
                 'border-radius:999px;%s;font:700 13px/1.3 -apple-system,BlinkMacSystemFont,&quot;Segoe UI&quot;,'
                 'Arial,sans-serif">%s уровень</p>' % (uroven, METKA_STIL[uroven], UROVNI[uroven][0]))
        html = html.replace("</h1>", "</h1>" + metka, 1)
        stranicy[page] = html
    return stranicy


def sobrat_indeksaciyu(podpisi):
    """Единая политика noindex и sitemap, поверх уже собранных подписей."""
    reestr = json.loads(REESTR.read_text(encoding="utf-8"))
    stranicy = {}
    adresy = [DOMEN, DOMEN + "politika/"]
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
        stranicy[page] = dobavit_privacy(html)

    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sitemap.extend("  <url><loc>%s</loc></url>" % ekranirovat(adres) for adres in adresy)
    sitemap.append("</urlset>")
    stranicy[KORNI / "sitemap.xml"] = "\n".join(sitemap) + "\n"
    stranicy[KORNI / "robots.txt"] = "User-agent: *\nAllow: /\n\nSitemap: " + DOMEN + "sitemap.xml\n"
    return stranicy


def spisok_serii(reestr, nazvanie):
    statyi = {s['slug']: s for s in reestr['statyi']}
    stroki = ['<ul>']
    for tema in reestr.get('serii', {}).get(nazvanie, []):
        slug = tema['slug']
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
            raise ValueError('Некорректный slug серии: %s' % slug)
        title = ekranirovat(tema['title'])
        if statyi.get(slug, {}).get('status') == 'live':
            stroki.append('<li><a href="../%s/">%s</a></li>' % (slug, title))
        else:
            stroki.append('<li>%s <span class="soon">(скоро)</span></li>' % title)
    return '\n'.join(stroki + ['</ul>'])


def sobrat_serii(stranicy):
    reestr = json.loads(REESTR.read_text(encoding='utf-8'))
    marker = re.compile(r'(<!-- series:start -->).*?(<!-- series:end -->)', re.S)
    for statya in reestr['statyi']:
        seriya = statya.get('seriya')
        if not seriya:
            continue
        if seriya not in reestr.get('serii', {}):
            raise ValueError('%s: состав серии отсутствует в реестре' % statya['slug'])
        page = (KORNI / 'claude-ai' / statya['slug'] / 'index.html').resolve()
        html = stranicy.get(page, page.read_text(encoding='utf-8'))
        if len(marker.findall(html)) != 1:
            raise ValueError('%s: нужен один блок series:start/series:end' % statya['slug'])
        stranicy[page] = marker.sub(lambda m: m[1] + '\n' + spisok_serii(reestr, seriya) + '\n' + m[2], html)
    return stranicy


def seo_lastmod(metadata):
    """Сохранённая дата значимой правки. Пересборка не обновляет её сама."""
    from datetime import date
    value = metadata.get('lastmod', '')
    if value:
        if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            raise ValueError('lastmod: нужна дата YYYY-MM-DD')
        date.fromisoformat(value)
    return value


def seo_plain(fragment):
    from html import unescape
    fragment = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', '', fragment, flags=re.S | re.I)
    fragment = re.sub(r'</?(?:p|div|li|ul|ol|pre|blockquote)\b[^>]*>|<br\b[^>]*>', ' ', fragment, flags=re.I)
    return ' '.join(unescape(re.sub(r'<[^>]+>', '', fragment)).split())


def seo_intro(html):
    """Исходное вступление после H1. Метка уровня, дата и подпись не являются им."""
    heading = re.search(r'<h1\b[^>]*>.*?</h1>', html, re.S | re.I)
    if not heading:
        raise ValueError('Отсутствует H1')
    start = heading.end()
    section = re.search(r'<h2\b', html[start:], re.I)
    end = start + section.start() if section else len(html)
    # Вопрос и следующий абзац могут быть отдельными p одного вступления.
    opening = '<div class="seo-intro">'
    if opening in html:
        a = html.index(opening)
        b = html.find('</div>', a + len(opening))
        if (html.count(opening) != 1 or a < start or b == -1 or b + len('</div>') > end
                or re.search(r'<div\b', html[a + len(opening):b], re.I)):
            raise ValueError('Нужен один блок seo-intro после H1 и до первого раздела, без вложенных div')
        return a, b + len('</div>'), html[a + len(opening):b]
    paragraphs = list(re.finditer(r'<p\b([^>]*)>(.*?)</p>', html[start:end], re.S | re.I))
    candidates = []
    for paragraph in paragraphs:
        classes = re.search(r'\bclass=[\'\"](.*?)[\'\"]', paragraph[1])
        classes = set(classes[1].split()) if classes else set()
        if classes & {'lead', 'intro-lede'}:
            return start + paragraph.start(), start + paragraph.end(), paragraph[2]
        if not classes & {'uroven-metka', 'meta', 'sun-caption', 'motion-note', 'source-note'}:
            candidates.append(paragraph)
    if not candidates:
        raise ValueError('После H1 отсутствует вступление')
    paragraph = candidates[0]
    return start + paragraph.start(), start + paragraph.end(), paragraph[2]


def proverit_seo_statyi(html, metadata, url):
    """Гейт штатной публикации: проверяет результат, прежде чем сборка пишет файлы."""
    modified = seo_lastmod(metadata)
    if not modified:
        raise ValueError(url + ': обязательный lastmod отсутствует')
    title = re.search(r'<title\b[^>]*>(.*?)</title>', html, re.S | re.I)
    if not title or not 20 <= len(seo_plain(title[1])) <= 65:
        raise ValueError(url + ': title должен содержать 20-65 знаков')
    if not 40 <= len(seo_plain(seo_intro(html)[2]).split()) <= 60:
        raise ValueError(url + ': исходное вступление должно содержать 40-60 слов')
    classes = re.findall(r'<[a-z][^>]*\bclass=[\'\"]([^\'\"]*)[\'\"]', html, re.I)
    if any('quick-answer' in value.split() for value in classes) or '<!-- seo:answer:start -->' in html:
        raise ValueError(url + ': отдельный быстрый ответ повторяет вступление')
    canonical = re.findall(r'<link\b(?=[^>]*\brel=[\'\"]canonical[\'\"])[^>]*\bhref=[\'\"]([^\'\"]+)[\'\"][^>]*>', html, re.I)
    if canonical != [url]:
        raise ValueError(url + ': требуется один canonical этой статьи')
    scripts = re.findall(r'<script\b[^>]*\bid=[\'\"]seo-schema[\'\"][^>]*>(.*?)</script>', html, re.S | re.I)
    try:
        if len(scripts) != 1:
            raise ValueError('Нужен один блок JSON-LD')
        articles = [x for x in json.loads(scripts[0])['@graph'] if x.get('@type') == 'Article']
        if len(articles) != 1 or articles[0].get('mainEntityOfPage') != url or articles[0].get('dateModified') != modified:
            raise ValueError('JSON-LD не соответствует статье и lastmod')
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError(url + ': некорректный JSON-LD') from error


def ubrat_seo(html):
    for part in ('schema', 'canonical', 'breadcrumbs', 'answer', 'related', 'faq'):
        html = re.sub(r'\s*<!-- seo:' + part + r':start -->.*?<!-- seo:' + part + r':end -->\s*', '\n', html, flags=re.S)
    return html


def seo_for_page(html, rel):
    source = KORNI / 'data' / 'seo.json'
    metadata = json.loads(source.read_text(encoding='utf-8')) if source.exists() else {}
    return dobavit_seo(html, DOMEN + rel.removesuffix('index.html'), metadata[rel]) if rel in metadata else html


def dobavit_seo(html, url, metadata):
    """Разметка берёт заголовок и FAQ из текущего видимого HTML."""
    from html import escape
    html = ubrat_seo(html)
    canonical = '<!-- seo:canonical:start -->\n<link rel="canonical" href="' + escape(url, quote=True) + '">\n<!-- seo:canonical:end -->'
    pattern = r'<link\b(?=[^>]*\brel\s*=\s*[\'"]canonical[\'"])[^>]*>'
    html = re.sub(pattern, '', html, flags=re.I)
    html = re.sub(r'\s*</head>', '\n' + canonical + '\n</head>', html, count=1)
    for field, tag in [('title', 'title'), ('description', 'description')]:
        if not metadata.get(field):
            continue
        value = escape(metadata[field], quote=True)
        if tag == 'title':
            html = re.sub(r'<title>.*?</title>', '<title>' + value + '</title>', html, count=1, flags=re.S)
            html = re.sub(r'(<meta\b[^>]*property="og:title"[^>]*content=")[^"]*(")', lambda m: m[1] + value + m[2], html)
        else:
            html = re.sub(r'(<meta\b[^>]*name="description"[^>]*content=")[^"]*(")', lambda m: m[1] + value + m[2], html)
            html = re.sub(r'(<meta\b[^>]*property="og:description"[^>]*content=")[^"]*(")', lambda m: m[1] + value + m[2], html)
    heading = re.search(r'<h1\b[^>]*>(.*?)</h1>', html, re.S | re.I)
    if not heading:
        raise ValueError(url + ': отсутствует H1')
    title = seo_plain(heading[1])
    graph = []
    is_article = '/claude-ai/' in url
    if is_article:
        crumbs = '<nav aria-label="Хлебные крошки" style="margin:12px 0;font:14px/1.5 -apple-system,BlinkMacSystemFont,Arial,sans-serif"><a href="/">Инструкции по нейросетям</a> <span aria-hidden="true"> / </span><span aria-current="page">' + escape(title) + '</span></nav>'
        end = re.search(r'<h1\b[^>]*>.*?</h1>', html, re.S).end()
        # После вводных абзацев, перед первым разделом: не разрывает обложку и H1.
        header_end = html.find('</header>', end)
        end = header_end if header_end != -1 else html.find('</main>', end)
        if end == -1:
            end = html.find('</body>')
        html = html[:end] + '\n<!-- seo:breadcrumbs:start -->\n' + crumbs + '\n<!-- seo:breadcrumbs:end -->\n' + html[end:]
        related = []
        for item in metadata.get('related', []):
            href = item['url']
            if not re.fullmatch(r'/claude-ai/[a-z0-9]+(?:-[a-z0-9]+)*/', href):
                raise ValueError('Неверный адрес тематической ссылки: ' + href)
            slug = href.strip('/').split('/')[-1]
            if re.search(r'href=[\'"](?:\.\./|/claude-ai/)' + re.escape(slug) + r'/[\'"]', html):
                continue
            related.append('<li><a href="' + href + '">' + escape(item['title']) + '</a></li>')
        if related:
            fragment = '<!-- seo:related:start -->\n<section class="seo-related" aria-label="Ещё по теме" style="margin:36px 0"><h2>Ещё по теме</h2><ul>' + ''.join(related) + '</ul></section>\n<!-- seo:related:end -->'
            # Перед финальной рекламной связкой, не разрывает вопрос, CTA и footer
            ends = [html.find(t) for t in ('<p class="cta-question"', '<section class="cta"', '</article>', '</main>', '<footer') if html.find(t) != -1]
            end = min(ends) if ends else html.find('</body>')
            html = html[:end] + '\n' + fragment + '\n' + html[end:]
        article = {'@type': 'Article', '@id': url + '#article', 'headline': title, 'mainEntityOfPage': url, 'inLanguage': 'ru', 'author': {'@type': 'Person', 'name': 'Жанна Слепова', 'url': DOMEN + '#about'}}
        modified = seo_lastmod(metadata)
        if modified:
            article['dateModified'] = modified
        image = re.search(r'<meta\b[^>]*property="og:image"[^>]*content="([^"]+)"', html)
        if image:
            from html import unescape
            article['image'] = unescape(image[1])
        graph.append(article)
        graph.append({'@type': 'BreadcrumbList', '@id': url + '#breadcrumbs', 'itemListElement': [{'@type': 'ListItem', 'position': 1, 'name': 'Инструкции по нейросетям', 'item': DOMEN}, {'@type': 'ListItem', 'position': 2, 'name': title, 'item': url}]})
        search_faq = metadata.get('search_faq', [])
        if search_faq:
            details = ''.join('<details class="faq-item"><summary>' + escape(x['question']) + '</summary><p>' + escape(x['answer']) + '</p></details>' for x in search_faq)
            fragment = '<!-- seo:faq:start -->\n<section class="seo-faq" aria-label="Вопросы из поиска" style="margin:36px 0"><h2>Что ещё спрашивают</h2>' + details + '</section>\n<!-- seo:faq:end -->'
            ends = [html.find(t) for t in ('<!-- seo:related:start -->', '<p class="cta-question"', '<section class="cta"', '</article>', '</main>', '<footer') if html.find(t) != -1]
            end = min(ends) if ends else html.find('</body>')
            html = html[:end] + '\n' + fragment + '\n' + html[end:]
        questions = []
        for detail in re.findall(r'<details\b[^>]*class="[^"]*\bfaq-item\b[^"]*"[^>]*>(.*?)</details>', html, re.S):
            summary = re.search(r'<summary\b[^>]*>(.*?)</summary>', detail, re.S)
            if not summary:
                raise ValueError(url + ': FAQ без вопроса')
            questions.append({'@type': 'Question', 'name': seo_plain(summary[1]), 'acceptedAnswer': {'@type': 'Answer', 'text': seo_plain(re.sub(r'<button\b[^>]*>.*?</button>', '', detail[summary.end():], flags=re.S))}})
        if questions:
            graph.append({'@type': 'FAQPage', '@id': url + '#faq', 'mainEntity': questions})
    else:
        graph.append({'@type': 'CollectionPage' if url == DOMEN else 'WebPage', '@id': url + '#page', 'name': title, 'url': url, 'inLanguage': 'ru'})
    # JSON inside HTML must not permit </script> or markup injection.
    schema = json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False, indent=2).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    block = '<!-- seo:schema:start -->\n<script type="application/ld+json" id="seo-schema">\n' + schema + '\n</script>\n<!-- seo:schema:end -->\n'
    return html.replace('</head>', block + '</head>', 1)


def sobrat_seo(stranicy):
    source = KORNI / 'data' / 'seo.json'
    metadata = json.loads(source.read_text(encoding='utf-8')) if source.exists() else {}
    registry = json.loads(REESTR.read_text(encoding='utf-8'))['statyi']
    live_paths = {'claude-ai/' + x['slug'] + '/index.html' for x in registry if x.get('status') == 'live'}
    missing = live_paths - metadata.keys()
    if missing:
        raise ValueError('Live-статья без записи data/seo.json: ' + ', '.join(sorted(missing)))
    for page, html in list(stranicy.items()):
        if page.suffix != '.html':
            continue
        rel = page.relative_to(KORNI).as_posix()
        if rel in metadata:
            url = DOMEN + rel.removesuffix('index.html')
            result = dobavit_seo(html, url, metadata[rel])
            if rel in live_paths:
                proverit_seo_statyi(result, metadata[rel], url)
            stranicy[page] = result
    if live_paths - {p.relative_to(KORNI).as_posix() for p in stranicy}:
        raise ValueError('Live-статья отсутствует в результатах сборки')
    if metadata:
        from html import escape
        xml = stranicy[KORNI / 'sitemap.xml']
        def dated(match):
            url = match[1]
            rel = url.removeprefix(DOMEN) + 'index.html'
            modified = seo_lastmod(metadata.get(rel, {}))
            return '<url><loc>' + url + '</loc>' + ('<lastmod>' + escape(modified) + '</lastmod>' if modified else '') + '</url>'
        stranicy[KORNI / 'sitemap.xml'] = re.sub(r'<url><loc>(.*?)</loc></url>', dated, xml)
    bots = ['GPTBot', 'OAI-SearchBot', 'ChatGPT-User', 'ClaudeBot', 'Claude-SearchBot', 'Claude-User', 'Anthropic-ai', 'PerplexityBot', 'Google-Extended', 'GoogleOther']
    stranicy[KORNI / 'robots.txt'] = 'User-agent: *\nAllow: /\n\n' + ''.join('User-agent: ' + bot + '\nAllow: /\n\n' for bot in bots) + 'Sitemap: ' + DOMEN + 'sitemap.xml\n'
    live = [x for x in registry if x.get('status') == 'live' and not x.get('noindex_reason')]
    lines = ['# Про новое', '', '> Инструкции по нейросетям для людей без опыта программирования. Автор: Жанна Слепова', '', '%d инструкций. Выбор материалов: [каталог](%s)' % (len(live), DOMEN), '', '## Начать', '', '- [Доступ к Claude](%sclaude-ai/podklyuchenie-iz-rossii/)' % DOMEN, '- [Первый проект](%sclaude-ai/pervyy-proekt-v-claude/)' % DOMEN, '- [Скиллы Claude Code](%sclaude-ai/pyat-skillov-claude-code/)' % DOMEN, '', '## Служебные сведения', '', '- [XML-карта всех канонических страниц](%ssitemap.xml)' % DOMEN, '- [Политика данных](%spolitika/)' % DOMEN, '', 'Контакт: pronovoe.site@yandex.ru', '']
    # Полный корпус уже в sitemap; llms содержит выбранные входы, а не её дубль.
    stranicy[KORNI / 'llms.txt'] = '\n'.join(lines)
    return stranicy


def main():
    stranica = sobrat_stranicu()
    podpisi = sobrat_metki_urovnya(sobrat_podpisi())
    rezultaty = sobrat_seo(sobrat_serii({GLAVNAYA: stranica, **sobrat_indeksaciyu(podpisi),
                             KORNI / "politika" / "index.html": sobrat_politiku()}))
    proverka = "--proverit" in sys.argv

    if proverka:
        razlichiya = [page for page, html in rezultaty.items()
                     if not page.exists() or page.read_text(encoding="utf-8") != html]
        if not razlichiya:
            print("Главная совпадает с реестром")
            print("Подписи %d статей совпадают с реестром" % len(podpisi))
            print("Индексация %d статей, sitemap.xml и robots.txt совпадают с реестром"
                  % (len(json.loads(REESTR.read_text(encoding="utf-8"))["statyi"])))
            print("Политика данных и общие блоки согласия совпадают с шаблонами")
            return 0
        for page in razlichiya:
            print("РАСХОЖДЕНИЕ: %s не совпадает с реестром" % page.relative_to(KORNI))
        print("Пересобрать: python3 scripts/sobrat_glavnuyu.py")
        return 1

    for page, html in rezultaty.items():
        if not page.exists() or page.read_text(encoding="utf-8") != html:
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text(html, encoding="utf-8")
    print("Подписи %d статей собраны из реестра" % len(podpisi))
    print("Индексация %d статей, sitemap.xml и robots.txt собраны из реестра" % (len(json.loads(REESTR.read_text(encoding="utf-8"))["statyi"])))
    print("Политика данных и общие блоки согласия собраны из шаблонов")
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
