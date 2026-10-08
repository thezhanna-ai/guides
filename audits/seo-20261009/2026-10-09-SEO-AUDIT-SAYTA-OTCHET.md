# SEO-аудит pronovoe.com

Фактический срез: 08.10.2026. Имя задания и ветки содержит 09.10, но эта будущая дата не использована как lastmod

**Задание целиком НЕ закрыто**: правки, реестр и проверки сохранены в ветке, но браузерная приёмка заблокирована, Wordstat не дал частот, публичная выдача не подтверждает индекс. LCP/CLS/INP и скриншоты не выдуманы. В main ничего не вносилось; живой сайт остаётся на исходной версии

## 1. Что было не так, что изменено, доказательства

| Было | Результат | Улика в коммите SEO |
|---|---|---|
| 28 страниц без canonical | По одному self-canonical на всех 47 страницах; 2 ссылки с index.html заменены адресами со слэшем | [audits/seo-20261009/static-check.json](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/static-check.json) |
| В sitemap не было lastmod | 47 дат значимого изменения 08.10.2026; при пересборке дата сама не меняется | [data/seo.json](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/data/seo.json); [sitemap.xml](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/sitemap.xml) |
| JSON-LD отсутствовал на 47 страницах | 45 Article + 45 BreadcrumbList, 11 FAQPage; главная CollectionPage, политика WebPage. H1 и ответы берутся из видимого HTML | [tests/test_seo.py](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/tests/test_seo.py); [audits/seo-20261009/python-final.txt](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/python-final.txt) |
| llms.txt отвечал 404 | Файл подготовлен в ветке; выбранные входы, каталог и карта. ИИ-боты явно разрешены в robots. На живом сайте это появится только после публикации | [llms.txt](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/llms.txt); [robots.txt](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/robots.txt) |
| 11 title длиннее 65 символов, 3 description длиннее 165 | Уникальные title в бюджете 20-65, description 70-165 символов. Уточнены поисковые предметы и тематические H2 | [audits/seo-20261009/static-check.json](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/static-check.json) |
| Короткие маршруты не всегда были абзацем 40-60 слов сразу под H1 | 45 отдельных быстрых ответов по 45-50 слов, после H1 и метки уровня. Исходные лиды сохранены | [data/seo.json](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/data/seo.json); [tests/test_seo.py](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/tests/test_seo.py) |
| 107 изображений с src без width/height | Добавлены фактические размеры; 291 img с lazy. 234 WebP уже в корпусе, PNG/JPG/SVG и встроенные изображения сохранены без пересжатия | [audits/seo-20261009/image-dimensions.json](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/image-dimensions.json); [audits/seo-20261009/image-followup.json](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/image-followup.json) |
| У части статей единственный вход был с главной | Тематические связи добавлены без изменения URL; минимум один вход с другой статьи у всех 45 | [audits/seo-20261009/static-check.json](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/static-check.json) |
| Нельзя было подтвердить, что правки сохранили рекламный текст и факты | 46 CTA побайтово совпали с 3c60841, исходная проза вне H1/H2/TOC совпала на всех 47 страницах, исходные изображения не менялись | [audits/seo-20261009/static-check.json](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/static-check.json); [audits/seo-20261009/security-review.md](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/security-review.md) |
| Не было готового безопасного IndexNow-пинга | Payload 47 URL, публичный ключ и CLI. Dry-run выполнен; --send проверяет публикацию всех HTML и ключа перед POST. Пинг не отправлен | [scripts/indexnow.py](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/scripts/indexnow.py); [audits/seo-20261009/indexnow-dry-run.txt](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/indexnow-dry-run.txt) |
| Скорость и скриншоты не подтверждены браузером | НЕ ИСПРАВЛЕНО: браузер заблокирован. Подготовлен повторяемый прогон; измерений и 20 скриншотов нет | [audits/seo-20261009/browser-blocker.md](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/browser-blocker.md); [audits/seo-20261009/browser-instructions.md](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/browser-instructions.md) |

Штатные проверки: **122 Python-теста OK**, **103 Node-теста pass**, **сборка --proverit совпадает с реестром**, **static-check 47 страниц, 0 ошибок**, **Gitleaks no leaks found** с узким исключением публичного токена IndexNow. Улики: [audits/seo-20261009/python-final.txt](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/python-final.txt), [audits/seo-20261009/node-final.txt](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/node-final.txt), [audits/seo-20261009/build-check.txt](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/build-check.txt), [audits/seo-20261009/static-check.txt](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/static-check.txt), [audits/seo-20261009/gitleaks.txt](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/gitleaks.txt)

Два последовательных круга по четырём осям: [SEO-1](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/round1-seo.md), [SEO-2](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/round2-seo.md), [интенты-1](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/round1-semantics.md), [интенты-2](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/round2-semantics.md), [текст-1](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/round1-text.md), [текст-2](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/round2-text.md), [телефон-1](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/round1-mobile.md), [телефон-2](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/round2-mobile.md). Это повторная проверка одного исполнителя, не независимое ревью разных моделей

47 канонических URL живого сайта ответили **200 без редиректов**. http/www и проверенный адрес без слэша дают 301 на https без www и со слэшем. Серверный /index.html остаётся 200 на GitHub Pages; canonical сводит его к основному адресу, но выбор поисковиком подтверждается в кабинетах. Отсутствие HTML-дублей на уровне сервера для index.html не заявлено. Улика: [audits/seo-20261009/live-http.json](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/live-http.json)

Все 340 img с src имеют alt и размеры. 30 пустых img относятся к динамическим просмотрщикам. Обложки остаются eager; влияние lazy и размеров на CWV не измерено. Перевод исходных скриншотов в другой формат не выполнен по запрету менять скрины. Символьный бюджет метаданных не гарантирует длину сниппета в выдаче

## 2. Все 47 страниц: запрос, спрос, интент, индекс

Формулировки предварительные, до Wordstat. Для главной интент каталога, для политики служебный. Wordstat вернул HTTP 200 с оболочкой SPA без цифр. Из 45 запросов к Google Suggest семь вернули подсказки; это подтверждает формулировки, но не частоту. Четыре подходящих вопроса добавлены в FAQ. Источник: [audits/seo-20261009/search-suggestions.json](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/search-suggestions.json)

В колонке индекса **Г? / Я?** означает: Google не подтверждён публичным site:, Яндекс не подтверждён из-за SmartCaptcha. Пустой результат site: не доказывает отсутствие страницы в индексе. HTTP 200 не является доказательством индексации. Экспорт кабинетов в этой сессии не использовался

| URL | Главный запрос | Спрос Wordstat | Интент | Индекс |
|---|---|---|---|---|
| [/](https://pronovoe.com/) | инструкции по нейросетям | нет замера | Выбрать инструкцию для своей задачи | Г? / Я? |
| [/politika/](https://pronovoe.com/politika/) | политика данных pronovoe.com | нет замера | Узнать условия обработки данных на сайте | Г? / Я? |
| [/claude-ai/10-besplatnyh-zamen/](https://pronovoe.com/claude-ai/10-besplatnyh-zamen/) | замены платным нейросетям | нет замера | Найти альтернативу подписке для конкретной задачи | Г? / Я? |
| [/claude-ai/10-saytov-starogo-interneta/](https://pronovoe.com/claude-ai/10-saytov-starogo-interneta/) | полезные сайты без регистрации | нет замера | Решить разовую бытовую задачу в браузере | Г? / Я? |
| [/claude-ai/animirovannaya-karusel/](https://pronovoe.com/claude-ai/animirovannaya-karusel/) | анимированная карусель | нет замера | Собрать плавное движение между слайдами карусели | Г? / Я? |
| [/claude-ai/artefakty-v-claude/](https://pronovoe.com/claude-ai/artefakty-v-claude/) | артефакты в Claude | нет замера | Создать отдельное интерактивное окно результата в Claude | Г? / Я? |
| [/claude-ai/besplatnye-video-iz-teksta/](https://pronovoe.com/claude-ai/besplatnye-video-iz-teksta/) | видео из текста | нет замера | Выбрать сервис для первого видео по описанию | Г? / Я? |
| [/claude-ai/claude-i-codex-v-vscode/](https://pronovoe.com/claude-ai/claude-i-codex-v-vscode/) | Claude Code и Codex в VS Code | нет замера | Разместить два агента и общие файлы в одном редакторе | Г? / Я? |
| [/claude-ai/claude-iz-rossii-bez-banov/](https://pronovoe.com/claude-ai/claude-iz-rossii-bez-banov/) | Claude не пускает | нет замера | Восстановить существующий доступ: ошибка, оплата, отключённый аккаунт | Г? / Я? |
| [/claude-ai/dannye-v-claude/](https://pronovoe.com/claude-ai/dannye-v-claude/) | удаление данных в Claude | нет замера | Удалить историю, память или аккаунт, сохранив нужные разговоры | Г? / Я? |
| [/claude-ai/golosovoy-vvod-v-claude/](https://pronovoe.com/claude-ai/golosovoy-vvod-v-claude/) | голосовой ввод в Claude | нет замера | Продиктовать запрос или поговорить голосом | Г? / Я? |
| [/claude-ai/gotovye-fayly-excel-word-pdf/](https://pronovoe.com/claude-ai/gotovye-fayly-excel-word-pdf/) | файлы Excel Word PDF в Claude | нет замера | Получить скачиваемый документ вместо текста в чате | Г? / Я? |
| [/claude-ai/incognito-chat-v-claude/](https://pronovoe.com/claude-ai/incognito-chat-v-claude/) | инкогнито в Claude | нет замера | Открыть разовый разговор без истории и памяти | Г? / Я? |
| [/claude-ai/kak-rasskazat-o-sebe/](https://pronovoe.com/claude-ai/kak-rasskazat-o-sebe/) | память Claude | нет замера | Настроить личный контекст для новых разговоров | Г? / Я? |
| [/claude-ai/kopirovat-stil-foto-v-chatgpt/](https://pronovoe.com/claude-ai/kopirovat-stil-foto-v-chatgpt/) | скопировать стиль фото в ChatGPT | нет замера | Перенести стиль изображения-образца на свой снимок | Г? / Я? |
| [/claude-ai/kopiya-higgsfield-open-generative-ai/](https://pronovoe.com/claude-ai/kopiya-higgsfield-open-generative-ai/) | копия Higgsfield Open Generative AI | нет замера | Установить Open Generative AI и создать первый кадр | Г? / Я? |
| [/claude-ai/montazh-video-claude-code-codex/](https://pronovoe.com/claude-ai/montazh-video-claude-code-codex/) | монтаж видео Claude Code Codex | нет замера | Передать исходники и подробное задание агенту для монтажа | Г? / Я? |
| [/claude-ai/otozvat-ssylku-na-chat-claude/](https://pronovoe.com/claude-ai/otozvat-ssylku-na-chat-claude/) | отозвать ссылку на чат Claude | нет замера | Закрыть ранее опубликованный доступ к разговору | Г? / Я? |
| [/claude-ai/ozhivit-maket-bez-keyframe/](https://pronovoe.com/claude-ai/ozhivit-maket-bez-keyframe/) | анимация Figma Magic Animator | нет замера | Оживить макет плагином без настройки ключевых кадров | Г? / Я? |
| [/claude-ai/pdf-v-markdown-markitdown/](https://pronovoe.com/claude-ai/pdf-v-markdown-markitdown/) | PDF в markdown MarkItDown | нет замера | Перевести документы в простой текст перед анализом | Г? / Я? |
| [/claude-ai/pervyy-proekt-v-claude/](https://pronovoe.com/claude-ai/pervyy-proekt-v-claude/) | проект в Claude | нет замера | Собрать чаты, инструкции и документы в одном проекте | Г? / Я? |
| [/claude-ai/podklyuchenie-iz-rossii/](https://pronovoe.com/claude-ai/podklyuchenie-iz-rossii/) | Claude из России подключение | нет замера | Подготовить сеть и зарегистрироваться для первого чата | Г? / Я? |
| [/claude-ai/podklyuchit-gmail-drive-calendar/](https://pronovoe.com/claude-ai/podklyuchit-gmail-drive-calendar/) | Gmail Google Drive Calendar в Claude | нет замера | Подключить почту, документы и календарь к Claude | Г? / Я? |
| [/claude-ai/postery-iz-odnogo-foto/](https://pronovoe.com/claude-ai/postery-iz-odnogo-foto/) | постер из фото | нет замера | Сделать постер из своего снимка с готовым запросом | Г? / Я? |
| [/claude-ai/promty-blog-biznes-chatgpt/](https://pronovoe.com/claude-ai/promty-blog-biznes-chatgpt/) | промпты для блога в ChatGPT | нет замера | Выбрать визуальные запросы для блога и деловых материалов | Г? / Я? |
| [/claude-ai/promty-eda-dom-chatgpt/](https://pronovoe.com/claude-ai/promty-eda-dom-chatgpt/) | промпты для еды и дома в ChatGPT | нет замера | Изменить подачу еды, комнаты и бытовых предметов | Г? / Я? |
| [/claude-ai/promty-igrushki-personazhi-chatgpt/](https://pronovoe.com/claude-ai/promty-igrushki-personazhi-chatgpt/) | промпты для игрушек в ChatGPT | нет замера | Превратить фото в игрушку, фигурку или игрового персонажа | Г? / Я? |
| [/claude-ai/promty-retro-ustroystvo-chatgpt/](https://pronovoe.com/claude-ai/promty-retro-ustroystvo-chatgpt/) | промпты для ретро в ChatGPT | нет замера | Показать предмет в ретро-стиле или условно разобрать на детали | Г? / Я? |
| [/claude-ai/promty-risunok-zhivopis-chatgpt/](https://pronovoe.com/claude-ai/promty-risunok-zhivopis-chatgpt/) | промпты для рисунка в ChatGPT | нет замера | Превратить фото в иллюстрацию или живопись | Г? / Я? |
| [/claude-ai/promty-sveta-dlya-foto-chatgpt/](https://pronovoe.com/claude-ai/promty-sveta-dlya-foto-chatgpt/) | промпты для света в ChatGPT | нет замера | Изменить освещение, фон и подачу портрета | Г? / Я? |
| [/claude-ai/promty-tovar-reklama-chatgpt/](https://pronovoe.com/claude-ai/promty-tovar-reklama-chatgpt/) | промпты для товара в ChatGPT | нет замера | Подготовить изображение товара, рекламу или упаковку | Г? / Я? |
| [/claude-ai/pyat-instrumentov-claude-code/](https://pronovoe.com/claude-ai/pyat-instrumentov-claude-code/) | дополнения для Claude Code | нет замера | Выбрать помощник для лимита, памяти, отчётов или настройки проекта | Г? / Я? |
| [/claude-ai/pyat-skillov-claude-code/](https://pronovoe.com/claude-ai/pyat-skillov-claude-code/) | скиллы для Claude Code установка | нет замера | Пошагово установить пять конкретных дополнений Claude Code | Г? / Я? |
| [/claude-ai/raspisanie-zadach-v-claude/](https://pronovoe.com/claude-ai/raspisanie-zadach-v-claude/) | задачи по расписанию в Claude | нет замера | Настроить регулярный разбор почты и календаря | Г? / Я? |
| [/claude-ai/shest-skillov/](https://pronovoe.com/claude-ai/shest-skillov/) | как найти подключить вызвать скиллы Claude | нет замера | Освоить поиск, подключение и вызов готовых инструкций | Г? / Я? |
| [/claude-ai/shtat-agentov-paperclip/](https://pronovoe.com/claude-ai/shtat-agentov-paperclip/) | штат ИИ-агентов Paperclip | нет замера | Создать организацию с ролями и общей целью в Paperclip | Г? / Я? |
| [/claude-ai/skrinshot-vmesto-obyasneniy/](https://pronovoe.com/claude-ai/skrinshot-vmesto-obyasneniy/) | скриншот в Claude | нет замера | Получить помощь по конкретному экрану вместо пересказа | Г? / Я? |
| [/claude-ai/stanford-kak-sozdayut-chatgpt/](https://pronovoe.com/claude-ai/stanford-kak-sozdayut-chatgpt/) | как создают ChatGPT | нет замера | Понять обучение языковой модели по лекции Стэнфорда | Г? / Я? |
| [/claude-ai/svoy-sayt-ne-bliznec/](https://pronovoe.com/claude-ai/svoy-sayt-ne-bliznec/) | свой сайт нейросетью | нет замера | Собрать сайт по образцу без типовых признаков ИИ-дизайна | Г? / Я? |
| [/claude-ai/svoy-server-dlya-claude/](https://pronovoe.com/claude-ai/svoy-server-dlya-claude/) | свой сервер для Claude | нет замера | Выбрать личный VPN или серверный запуск Claude Code | Г? / Я? |
| [/claude-ai/svoy-stil-otvetov/](https://pronovoe.com/claude-ai/svoy-stil-otvetov/) | свой стиль ответов Claude | нет замера | Сохранить правила письма по своим образцам | Г? / Я? |
| [/claude-ai/urovni-vaybkodera/](https://pronovoe.com/claude-ai/urovni-vaybkodera/) | уровни вайбкодера | нет замера | Определить недостающий навык и следующий шаг в работе с агентом | Г? / Я? |
| [/claude-ai/vybor-modeli-i-effort/](https://pronovoe.com/claude-ai/vybor-modeli-i-effort/) | выбор модели и effort Claude | нет замера | Подобрать модель и глубину работы под сложность задачи | Г? / Я? |
| [/claude-ai/web-search-v-claude/](https://pronovoe.com/claude-ai/web-search-v-claude/) | веб-поиск в Claude | нет замера | Включить поиск и проверять актуальные источники ответа | Г? / Я? |
| [/claude-ai/whatsapp-nomer-dlya-agenta/](https://pronovoe.com/claude-ai/whatsapp-nomer-dlya-agenta/) | номер WhatsApp для ИИ-агента | нет замера | Проверить интеграцию в песочнице и подключить рабочий номер | Г? / Я? |
| [/claude-ai/zagruzka-faylov-v-claude/](https://pronovoe.com/claude-ai/zagruzka-faylov-v-claude/) | загрузка файлов в Claude | нет замера | Прикрепить документ или пачку и проверить прочитанное | Г? / Я? |
| [/claude-ai/zakryt-sekrety-ot-claude-code/](https://pronovoe.com/claude-ai/zakryt-sekrety-ot-claude-code/) | закрыть секретные файлы от Claude Code | нет замера | Ограничить чтение ключей и проверить запрет на тестовом файле | Г? / Я? |

Реестр сохранён в `.business/marketing/seo/reestr-intentov.md`; копия для просмотра: [audits/seo-20261009/intent-register.md](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/intent-register.md). Статус каждой страницы: SEO в ветке, публикация правок и индекс не подтверждены. Точные словоформы не повторялись механически: заголовки и ответы содержат поисковый предмет естественно

## 3. Каннибализация и решения

| Пересечение | Владелец общего интента | Что оставить отдельно |
|---|---|---|
| Claude из России | podklyuchenie-iz-rossii: первое подключение | claude-iz-rossii-bez-banov: существующий аккаунт и ошибки; svoy-server-dlya-claude: сервер и удалённая работа |
| Скиллы Claude Code | pyat-skillov-claude-code: установка конкретного набора | shest-skillov: подключение/вызов Claude Skills с примерами; pyat-instrumentov-claude-code: выбор дополнения под помеху |
| Память и контекст Claude | kak-rasskazat-o-sebe: личная память | pervyy-proekt-v-claude: база проекта; svoy-stil-otvetov: голос ответов |
| Данные и приватность | dannye-v-claude: удаление | incognito-chat-v-claude: разовый разговор; otozvat-ssylku-na-chat-claude: закрыть ссылку |
| Промпты ChatGPT | Общий запрос всем подборкам не назначать | Семь владельцев по предметам: свет, товар, блог, игрушки, рисунок, ретро, еда; JSON-стиль и постер имеют свои инструкции |
| Видео и анимация | besplatnye-video-iz-teksta: выбор генератора | Монтаж исходников, карусель, анимация Figma и установка студии отличаются по результату |

Ни один URL не удалён и не объединён. Самое заметное потенциальное пересечение: claude-mem в нескольких подборках. Фактическое конкурирование URL за одинаковые показы не доказано без кабинетов. Решение на сейчас: сохранить самостоятельные инструкции и владельцев интентов; объединять можно только после подтверждённых данных. Подробности: [audits/seo-20261009/intent-register.md](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/intent-register.md)

## 4. Топ-10 новых тем со спросом

**Топ-10 со спросом не сформирован**: нет ни одной измеренной частоты. В `.business/marketing/seo/ochered.md` допущенных новых тем **0**, правило движка не нарушено

Подготовлены десять гипотез для следующего замера, без ранжирования и без допуска в публикацию: MCP в Claude Code, Codex Skills, CLAUDE.md, восстановление файла, Git worktree, ревью в Codex, временный чат ChatGPT, экспорт данных ChatGPT, Google Drive в ChatGPT, расход токенов Claude Code. Спрос каждой: **нет замера**. Улики: [audits/seo-20261009/topic-queue.md](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/topic-queue.md), [audits/seo-20261009/topics-to-measure.md](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/topics-to-measure.md)

## 5. Что остаётся сделать руками, не больше трёх пунктов

1. Повторить браузерную приёмку в среде, где разрешён Chromium, и получить Wordstat по 47 формулировкам и десяти гипотезам с регионом/периодом. Команды подготовлены в [audits/seo-20261009/browser-instructions.md](https://github.com/thezhanna-ai/guides/blob/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8/audits/seo-20261009/browser-instructions.md). Нужны 20 скриншотов и мобильные LCP/CLS/INP, затем заполнение спроса и очереди. Это незакрытые критерии, не рекомендация на будущее
2. После прохождения приёмки опубликовать ветку выбранным владельцем способом. Сейчас main не менялся. После публикации выполнить `python3 scripts/indexnow.py --send`; до совпадения HTML и ключа отправка запрещена самим скриптом
3. В Вебмастере Яндекса и Google Search Console проверить основной https-адрес без www, sitemap, статус всех 47 URL и выбранный canonical. Выгрузить страницы/запросы, подтвердить или снять риски каннибализации. Повторную индексацию запросить после публикации правок; обещание индекса всех страниц без данных не даётся

Автоматическая проверка разрешений отклонила Playwright MCP browser_navigate и browser_run_code_unsafe: `MCP tool call requires approval, but approval policy is never`. Локальный Chromium завершился SIGABRT/EPERM; CUA Chrome также не разрешён. Поэтому скорость и скриншоты физически не проверены

## 6. Коммит ветки

Коммит SEO-изменений: [c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8](https://github.com/thezhanna-ai/guides/commit/c8bbd5b149f0d4b32e2190b2681cdafb5e7cadb8)

Ветка: [codex/seo-audit-20261009](https://github.com/thezhanna-ai/guides/tree/codex/seo-audit-20261009). Push подтверждён через git ls-remote. Main сохранил `3c608416fb599779eb8017ffb92f21638c8fcb62`

Метаданные исходного worktree не доступны для записи: создание index.lock запрещено средой. Коммит и push выполнены из временной Git-копии с теми же рабочими файлами. Локальная ссылка HEAD исходного worktree остаётся 3c60841; удалённая ветка содержит указанный SEO-коммит. Отчёт доставляется отдельным документным коммитом на этой же ветке
