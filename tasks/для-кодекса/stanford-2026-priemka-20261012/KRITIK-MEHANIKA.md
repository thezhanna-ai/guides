# Механическая приёмка CS229 2026, 12 октября 2026

PASS. Critical: 0. Major: 0

Роль: механика. Браузер не запускался, исходные файлы не изменялись. Требование нарастания из ТЗ относится к текстовой приёмке и этой ролью не оценивалось

## Обязательные команды

Каждая команда запущена отдельно. Полный stdout/stderr и код завершения сохранены в соответствующем логе

| Команда | Результат | Тесты | Лог |
| --- | --- | ---: | --- |
| `python3.12 tasks/для-кодекса/stanford-2026-konspekt/proverka.py` | PASS, exit 0 | скрипт утверждений | `MEHANIKA-proverka.log` |
| `python3.12 -m unittest discover -s tests -p 'test_*.py'` | PASS, exit 0 | 160 | `MEHANIKA-unittest.log` |
| `node --test tests/erid.test.cjs` | PASS, exit 0 | 54 | `MEHANIKA-erid.log` |
| `node --test tests/filtry.test.cjs` | PASS, exit 0 | 57 | `MEHANIKA-filtry.log` |
| `node --test tests/image-viewer.test.cjs` | PASS, exit 0 | 16 | `MEHANIKA-image-viewer.log` |
| `node --test tests/privacy.test.cjs` | PASS, exit 0 | 11 | `MEHANIKA-privacy.log` |
| `python3.12 scripts/sobrat_glavnuyu.py --proverit` | PASS, exit 0 | проверка сборки | `MEHANIKA-glavnaya.log` |
| `git diff --check` | PASS, exit 0 | проверка diff | `MEHANIKA-diff-check.log` |

Всего 298 тестов: 160 Python и 138 Node. В Node-наборах fail 0, cancelled 0, skipped 0, todo 0. Python: `Ran 160 tests`, `OK`. Дополнительно прошли скрипт proverka.py, проверка сборки и diff

## Статическая инспекция

Результаты дополнительных Python-assertions сохранены в `MEHANIKA-static.log`. Обложки для трёх ширин физически открыты как бинарные PNG, размеры IHDR и SHA-256 сверены с `STATIC-COVER.json`; результаты в `MEHANIKA-static-cover-files.log`

- PNG обложки: 480×360, HTML width/height и OG width/height равны 480×360, размеры и SHA-256 совпадают с `data/OBLOZHKI.json`
- SHA-256 обложки: `6e5caa68114094d43a1d67cf8b8f521b36aeb61eeca94f247aadb72e464c31ee`
- Реестр обложки содержит исходный кадр 00:06, original_width 640, original_height 360 и crop x=80, y=0, width=480, height=360
- CSS `figure.cover-v2 img` ограничивает ширину `min(100%, 480px)` (index.html:469), общий `figure.cover img` сохраняет `height: auto` (index.html:464). Обложка не увеличивается сверх натурального размера. При ширинах 390 и 360 расчётная ширина 362 и 332, высота 271,5 и 249, соотношение 4:3 сохраняется
- Файлы `codex-cover-1440.png`, `codex-cover-390.png`, `codex-cover-360.png` имеют холсты 1440×404, 390×316, 360×293; все три контрольные суммы совпадают с `STATIC-COVER.json`. Это статические изображения обложки, не браузерные скриншоты всей страницы
- Порядок первых семи элементов header: eyebrow → figure.cover-v2 → h1 → p.uroven-metka.green → meta → lead → info-card, соответствует первому конспекту (index.html:710)
- Плашка уровня полностью совпадает побайтно с `claude-ai/stanford-kak-sozdayut-chatgpt/index.html`. SHA-256 байтов плашки: `daf90579f56617113719a92958217e57eb2054cc0db16eab6fbeeca49697a736`
- ImageNet, слова и робот помещены в `figure.shot > div.shot > img`, а figcaption является соседним элементом div (index.html:798, 810, 835). Существующий JS использует `img.parentElement.appendChild(button)` (index.html:983), поэтому кнопка оказывается внутри div.shot и не включает figcaption в контейнер позиционирования. `.shot` имеет position relative, кнопка position absolute/right 10px/bottom 10px
- Реестр статьи: status draft, vydacha net, kod_slovo МОЗГ, data_publikacii пусто. На странице есть `noindex, nofollow`, slug отсутствует в sitemap и ссылка на статью отсутствует на главной. Реестровый title равен h1 и title страницы
- Сборщик SEO (`scripts/sobrat_glavnuyu.py:760`) требует запись data/seo.json для live; добавляет SEO по наличию записи metadata и для других статусов (`:768`). У проверяемого draft такой записи нет. Указанного в ТЗ примера `claude-ai/konspekt-rechi-v-chatgpt/index.html` в worktree нет. Текущее состояние проверяемого draft проходит обязательную проверку сборки и не попадает в индексацию

Critical/major дефектов в объёме механической проверки не найдено. Поведение в браузере в этом заходе не проверялось по прямому запрету ТЗ
