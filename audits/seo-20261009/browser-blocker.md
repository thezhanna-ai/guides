# Браузерная проверка

2026-10-08. Запуск настоящего Chromium через Playwright завершился SIGABRT; лог browser-before.log содержит ошибку kill EPERM. Замеров LCP/CLS/INP нет, результаты не выдуманы

Playwright MCP browser_navigate и browser_run_code_unsafe вернули `MCP tool call requires approval, but approval policy is never`. CUA не обнаружил браузеров, createBrowserTab вернул `Browser is not available: chrome`, getApp Google Chrome вернул `Computer Use was not approved to use Google Chrome`

Готов воспроизводимый browser-check.cjs: 390x844, 4G 1.6 Мбит/с, задержка 150 мс, CPU x4, холодный кэш, по 3 прогона главной и 5 статей, web-vitals, реальные взаимодействия, скрины 1470/390. Он должен быть исполнен в среде с разрешённым браузером. Наличие скрипта не считается выполненным замером
