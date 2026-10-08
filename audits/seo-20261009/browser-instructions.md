# Повторение браузерной проверки

Успешного прогона в этой сессии нет. Оригинальный сайт 3c60841 нужен отдельно для before; текущая ветка для after. Сохранить результаты в одну папку audits/seo-20261009/skriny, не перезаписывать before более новой версией

В среде, где разрешён Chromium, установить Playwright и web-vitals во временную папку, затем браузер. На время проверки серверы Python должны быть подняты из корня соответствующей копии сайта: `python3 -m http.server 8768 --bind 127.0.0.1` для исходной версии и порт 8769 для ветки

```bash
npm install --prefix /private/tmp/seo-browser-tools --cache /private/tmp/seo-browser-cache playwright web-vitals
/private/tmp/seo-browser-tools/node_modules/.bin/playwright install chromium
export PLAYWRIGHT_PATH=/private/tmp/seo-browser-tools/node_modules/playwright
export WEB_VITALS_PATH=/private/tmp/seo-browser-tools/node_modules/web-vitals/dist/web-vitals.iife.js
node audits/seo-20261009/browser-check.cjs before http://127.0.0.1:8768
node audits/seo-20261009/browser-check.cjs after http://127.0.0.1:8769
```

Если нужен конкретный установленный Chromium, задать CHROMIUM_PATH. Оба запуска используют скрипт и каталог результатов текущей ветки. Для исходной копии сделать отдельный checkout 3c60841 вне рабочего проекта

18 холодных мобильных запусков на stage, 3 прогона каждой страницы. Сохранить версии браузера, условия, ошибки, отсутствующие метрики и медианы LCP/CLS. INP относится только к исполненным взаимодействиям в лаборатории; не объявлять его полевым p75 и не заменять отсутствующее значение нулём. Бюджеты: LCP <= 2500 мс, CLS <= 0.1, INP <= 200 мс. Проверить переполнение, картинки, меню и кнопку копирования вручную по скринам; наличие скрина не заменяет взаимодействия

Полевая проверка после публикации проводится отдельно в Search Console и Вебмастере по мере накопления данных
