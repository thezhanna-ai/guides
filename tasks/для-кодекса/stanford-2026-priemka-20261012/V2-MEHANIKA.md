# V2: независимая приёмка механики и security-review

Вердикт: PASS на финальном HTML с SHA256 `693066c3630c8bfb55d7188d2c7ea67f2d59619440d3109acef1b9533671e996`

Проверяльщик механики, 12 октября 2026 года. Рабочая папка: `/Users/zslepova/IvanOS/.worktrees/stanford-2026-konspekt`, файл: `claude-ai/stanford-2026-kak-uchitsya-ii/index.html`

Базовый HEAD: `5867ff93ff83f03ec4a3d8cd3b8dcdb15126866e`. Все восемь команд, независимый аудит и повторное чтение HTML относятся к одному SHA256. Хеш до и после каждой команды одинаковый. Исходники, основной отчёт, коммиты и публикация не изменялись, браузер не запускался

## Команды, коды выхода и вывод

| Команда | Код выхода | Наблюдаемый вывод | Полный лог |
|---|---:|---|---|
| `python3.12 tasks/для-кодекса/stanford-2026-konspekt/proverka.py` | 0 | JSON: `words_new=3385`, 8 мыслей, нулевые запрещённые формы, нет сломанных якорей и copy targets | [PROVERKA](V2-MEHANIKA-PROVERKA.log) |
| `python3.12 -m unittest discover -s tests -p 'test_*.py'` | 0 | `Ran 160 tests in 25.664s`, `OK` | [PYTHON](V2-MEHANIKA-PYTHON.log) |
| `node --test tests/erid.test.cjs` | 0 | `tests 54`, `pass 54`, `fail 0` | [NODE-ERID](V2-MEHANIKA-NODE-ERID.log) |
| `node --test tests/filtry.test.cjs` | 0 | `tests 57`, `pass 57`, `fail 0` | [NODE-FILTRY](V2-MEHANIKA-NODE-FILTRY.log) |
| `node --test tests/image-viewer.test.cjs` | 0 | `tests 16`, `pass 16`, `fail 0` | [NODE-IMAGE-VIEWER](V2-MEHANIKA-NODE-IMAGE-VIEWER.log) |
| `node --test tests/privacy.test.cjs` | 0 | `tests 11`, `pass 11`, `fail 0` | [NODE-PRIVACY](V2-MEHANIKA-NODE-PRIVACY.log) |
| `python3.12 scripts/sobrat_glavnuyu.py --proverit` | 0 | Главная, подписи 53 статей, индексация, sitemap.xml, robots.txt, политика данных и общие блоки согласия совпадают с реестром и шаблонами | [GLAVNAYA](V2-MEHANIKA-GLAVNAYA.log) |
| `git diff --check` | 0 | Пустой вывод, ошибок пробелов нет | [DIFF-CHECK](V2-MEHANIKA-DIFF-CHECK.log) |
| `python3.12 /Users/zslepova/IvanOS/tasks/для-кодекса/stanford-2026-priemka-20261012/V2-MEHANIKA-AUDIT.py` | 0 | Все сравнения защищённых блоков, URL, JS и счётчики прошли | [SECURITY](V2-MEHANIKA-SECURITY.log) |

Всего: 160 Python-тестов и 138 Node-тестов, во всех четырёх Node-прогонах нет fail, cancelled, skipped или todo

## Объём и служебные ограничения

После удаления HTML-тегов и комментариев, раскрытия HTML entities и разбиения по пробельным символам: **3385 слов <= 3400**, запас 15 слов. Независимый пересчёт совпал с `proverka.py`

Счётчик Ма/лектор в видимом тексте `article`: **8**. Все восемь находятся в неизменяемых блоках. В сыром HTML: **9**, дополнительное совпадение находится в `alt` обложки. В редактируемой части после исключения header, #original, четырёх figures, CTA и footer: **0**. Нулём для всего article это не объявляется

`proverka.py`: длинных тире 0, чужих имён вне рекламы 0, ценовых слов вне рекламы 0, шага 0 нет, гендерных обращений 0, формульных маркеров 0, конечных точек в абзацах и запросах 0, неправильных окончаний абзацев 0. Якоря и кнопки копирования указывают на существующие ID, четыре PNG существуют и их размеры соответствуют HTML

CTA побайтно совпадает с эталоном: `f0dc1147e178181d07604d3e1ed41836ca0ce830982ff46321c13f49964baba7`. Описания metadata совпадают с реестром. Статус `draft`, выдача `net`, код-слово `МОЗГ`, присутствует `noindex, nofollow`, статьи нет на главной и в sitemap

## Независимый security-review текстового diff

Сравнение выполнено непосредственно с `git show HEAD:claude-ai/stanford-2026-kak-uchitsya-ii/index.html`, а не со спецификацией или пересказом прежних проверок

| Защищённая область | Результат |
|---|---|
| Все script-блоки | Побайтно равны HEAD |
| Все style-блоки | Побайтно равны HEAD |
| HTML вне article | Побайтно равен HEAD |
| Header `#nachalo` | Побайтно равен HEAD |
| Section `#original` | Побайтно равна HEAD |
| Четыре figure целиком, включая img и figcaption | Все четыре побайтно равны HEAD |
| CTA | Побайтно равна HEAD |
| Footer | Побайтно равен HEAD |
| Внешние URL | Множество добавленных URL пусто, удалённых тоже нет |
| Inline обработчики `on*` и `javascript:` URL | Не изменены |

Нового JavaScript и новых внешних URL нет. Единственный изменённый tracked-файл: HTML статьи, изменена редактируемая часть article. Diff не расширяет исполняемый код, сетевые назначения или обработку данных. Защищённые блоки сохранены. Security-review: PASS

Текстовый diff сохранён полностью в [DIFF](V2-MEHANIKA-DIFF.log), контрольные SHA256 защищённых блоков и все найденные упоминания со строками сохранены в [SECURITY.json](V2-MEHANIKA-SECURITY.json). Исполняемый независимый аудит: [AUDIT.py](V2-MEHANIKA-AUDIT.py), манифест всех прогонов: [RUNS.json](V2-MEHANIKA-RUNS.json)

Критерий нарастания текста этой приёмкой не оценивался, он относится к отдельной текстовой проверке

Перед коммитом в сохранённом diff убраны пробелы на пустых контекстных строках. Это нормализация файла для чтения, текст изменения HTML не менялся. Дополнительный `git diff --cached --check` проверяет весь пакет улик перед коммитом
