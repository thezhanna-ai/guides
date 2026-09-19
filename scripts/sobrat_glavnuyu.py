#!/usr/bin/env python3
"""Сборка index.html из реестра data/statyi.json.

Руками index.html НЕ править: любая правка затрётся следующей сборкой.
Новая статья = запись в реестре, потом `python3 scripts/sobrat_glavnuyu.py`.

Текст шапки, названия разделов и описания трасс лежат ниже в РАЗДЕЛЫ -
это содержание, которого нет в реестре, оно правится здесь.

Проверка без записи: `python3 scripts/sobrat_glavnuyu.py --proverit`
Возвращает код 1, если собранное расходится с тем, что лежит в index.html
"""

import json
import sys
from pathlib import Path

KORNI = Path(__file__).resolve().parent.parent
REESTR = KORNI / "data" / "statyi.json"
GLAVNAYA = KORNI / "index.html"

SHAPKA = {
    "nadzagolovok": "Надо только научиться ставить задачу",
    "h1": "Нейросети работают на тебя",
    "lead": "Ты попал по адресу. Здесь инструкции, разборы и гайды по нейросетям - от первой кнопки до собранных проектов",
    "intro": "Начни с простого: отдай нейросети рутину, которая съедает твой день - посчитать, написать, разобрать, оформить. Дальше научишься собирать свои проекты, находить решения для своего дела и делать то, что раньше заказывал на стороне",
    "title": "Нейросети работают на тебя",
    "description": "Инструкции, разборы и гайды по нейросетям для не-программистов: от первой кнопки до собственных проектов",
    "podval": "Гайды обновляются регулярно - если нужной инструкции ещё нет, она уже готовится",
}

UROVNI = {
    "green": ("Начальный", "если открываешь нейросеть впервые"),
    "blue": ("Средний", "если уже работаешь и хочешь собирать своё"),
}

TIPY = {
    "instr": ("Инструкция", "kind-instr"),
    "razbor": ("Разбор", "kind-razbor"),
    "obzor": ("Обзор", "kind-obzor"),
}

# Порядок разделов на странице и трасс внутри них.
# "trassa" совпадает с полем razdel в реестре, статьи подставляются автоматически
RAZDELY = [
    {
        "tag": "dostup",
        "zagolovok": "Доступ и оплата",
        "opisanie": "Нужно любой нейросети: как открыть, чем платить, что делать, когда перестало работать",
        "trassy": [
            {
                "trassa": "obychnyy-vhod",
                "uroven": "green",
                "nazvanie": "Обычный вход",
                "opisanie": "Хватает большинству: VPN, регистрация, оплата. Разобрано на примере Claude",
            },
            {
                "trassa": "svoy-server",
                "uroven": "blue",
                "nazvanie": "Свой сервер",
                "opisanie": "Постоянный доступ без VPN: своя машина в другой стране",
                "pusto": "Гайды готовятся",
            },
        ],
    },
    {
        "tag": "claude",
        "zagolovok": "Claude",
        "opisanie": "Чат Claude.ai и работа в коде через Claude Code",
        "trassy": [
            {
                "trassa": "knopka-za-knopkoy",
                "uroven": "green",
                "nazvanie": "Кнопка за кнопкой",
                "opisanie": "Чат Claude.ai по одной настройке за раз. Ничего не нужно знать заранее",
            },
            {
                "trassa": "vaybkoding",
                "uroven": "blue",
                "nazvanie": "Claude Code: вайбкодинг",
                "opisanie": "Переход от чата к коду: свои проекты, CLI и настройка под задачу",
            },
        ],
    },
    {
        "tag": "gpt",
        "zagolovok": "ChatGPT и Codex",
        "opisanie": "Чат ChatGPT и работа в коде через Codex CLI",
        "trassy": [
            {
                "trassa": "gpt-knopka",
                "uroven": "green",
                "nazvanie": "Кнопка за кнопкой",
                "opisanie": "Та же серия, что и в Claude, только кнопки и экраны - из ChatGPT",
                "pusto": "Гайды готовятся",
            },
            {
                "trassa": "gpt-vaybkoding",
                "uroven": "blue",
                "nazvanie": "Codex: вайбкодинг",
                "opisanie": "Работа в Codex CLI, доступ и Remote Control",
                "pusto": "Гайды готовятся",
            },
        ],
    },
    {
        "tag": "kartinki",
        "zagolovok": "Картинки и видео",
        "opisanie": "Чем рисовать, чем монтировать, что из этого стоит своих денег",
        "trassy": [{"trassa": "kartinki", "pusto": "Гайды готовятся"}],
    },
    {
        "tag": "proekty",
        "zagolovok": "Свои проекты",
        "opisanie": "Собранное под ключ: сайт, бот, рабочая система под конкретную задачу",
        "trassy": [{"trassa": "proekty", "pusto": "Гайды готовятся"}],
    },
    {
        "tag": "proishodit",
        "zagolovok": "Что происходит",
        "opisanie": "Разборы событий, которые меняют работу с нейросетями. Кнопки нажимать не нужно, уровень не важен",
        "trassy": [{"trassa": "proishodit", "pusto": "Разборы готовятся"}],
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
        po_trassam.setdefault(statya["razdel"], []).append(statya)
    return po_trassam


def sobrat_kartochku(statya):
    podpis, klass = TIPY[statya["tip"]]
    return (
        '          <a class="guide-link" data-tags="{tags}" href="claude-ai/{slug}/">'
        '<span class="kind {klass}">{podpis}</span>'
        "<span class=\"guide-title\">{title}</span></a>"
    ).format(
        tags=ekranirovat(statya["tags"]),
        slug=statya["slug"],
        klass=klass,
        podpis=podpis,
        title=ekranirovat(statya["title"]),
    )


def sobrat_trassu(trassa, po_trassam):
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
        stroki.extend(sobrat_kartochku(s) for s in statyi)
        stroki.append("        </div>")
    else:
        stroki.append('        <span class="soon">%s</span>' % ekranirovat(trassa["pusto"]))

    stroki.append("      </div>")
    return "\n".join(stroki)


def sobrat_razdel(razdel, po_trassam):
    stroki = [
        '    <section class="tool-block" data-section="%s" aria-label="%s">'
        % (razdel["tag"], ekranirovat(razdel["zagolovok"])),
        '      <div class="tool-head">',
        "        <h2>%s</h2>" % ekranirovat(razdel["zagolovok"]),
        "        <p>%s</p>" % ekranirovat(razdel["opisanie"]),
        "      </div>",
        "",
    ]
    stroki.append("\n\n".join(sobrat_trassu(t, po_trassam) for t in razdel["trassy"]))
    stroki.append("    </section>")
    return "\n".join(stroki)


def sobrat_filtry():
    knopki = ['        <button class="tag-btn active" data-tag="all" type="button">Все</button>']
    for razdel in RAZDELY:
        knopki.append(
            '        <button class="tag-btn" data-tag="%s" type="button">%s</button>'
            % (razdel["tag"], ekranirovat(razdel["zagolovok"]))
        )
    return "\n".join(knopki)


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
    shablon = (KORNI / "scripts" / "shablon_glavnoy.html").read_text(encoding="utf-8")
    return shablon.format(
        title=ekranirovat(SHAPKA["title"]),
        description=ekranirovat(SHAPKA["description"]),
        nadzagolovok=ekranirovat(SHAPKA["nadzagolovok"]),
        h1=ekranirovat(SHAPKA["h1"]),
        lead=ekranirovat(SHAPKA["lead"]),
        intro=ekranirovat(SHAPKA["intro"]),
        urovni=sobrat_urovni(),
        filtry=sobrat_filtry(),
        razdely="\n\n".join(sobrat_razdel(r, po_trassam) for r in RAZDELY),
        podval=ekranirovat(SHAPKA["podval"]),
    )


def main():
    stranica = sobrat_stranicu()
    proverka = "--proverit" in sys.argv

    if proverka:
        tekushchaya = GLAVNAYA.read_text(encoding="utf-8") if GLAVNAYA.exists() else ""
        if tekushchaya == stranica:
            print("Главная совпадает с реестром")
            return 0
        print("РАСХОЖДЕНИЕ: index.html не совпадает с тем, что собирается из реестра")
        print("Пересобрать: python3 scripts/sobrat_glavnuyu.py")
        return 1

    GLAVNAYA.write_text(stranica, encoding="utf-8")
    po_trassam = zagruzit_statyi()
    vsego = sum(len(v) for v in po_trassam.values())
    print("Собрано: %s, статей на главной %d" % (GLAVNAYA.name, vsego))
    for razdel in RAZDELY:
        for trassa in razdel["trassy"]:
            kolvo = len(po_trassam.get(trassa["trassa"], []))
            if kolvo:
                print("  %-22s %d" % (trassa["trassa"], kolvo))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
