# Факты ЧЕТЫРЕ: проверка 06.10.2026

Официальные страницы открыты через web, Chrome не запускался. Сохранены выводы с привязкой к первоисточникам, а не выдуманные результаты вызовов MCP

| Источник | Что взято в статью |
|---|---|
| https://github.com/perplexityai/modelcontextprotocol | Удалённый адрес api.perplexity.ai/mcp, команда Claude Code с Authorization: Bearer, кабинет console.perplexity.ai, поиск текущих сведений |
| https://docs.perplexity.ai/docs/getting-started/integrations/mcp-server | Поддерживаются OAuth и API-ключ; выбранный в статье API-ключ не означает отмену OAuth. Вызовы относятся к организации API |
| https://github.com/microsoft/playwright-mcp | Node.js 18+, пакет @playwright/mcp@latest, локальное управление браузером, отличие MCP от CLI |
| https://github.com/firecrawl/firecrawl-mcp-server | Удалённый OAuth-адрес /v2/mcp-oauth, вариант /v2/mcp с Authorization: Bearer, scrape/map/crawl, ограниченный набор без ключа |
| https://docs.firecrawl.dev/quickstarts/claude-code | Команда claude mcp add для OAuth, /mcp и авторизация в браузере, повторный запуск после смены подключения |
| https://www.firecrawl.dev/app/api-keys | Официальный адрес кабинета ключей из README Firecrawl |
| https://github.com/upstash/context7 | Документация библиотек, запрос под версию, ручной удалённый адрес /mcp и Bearer-заголовок, ограничения полноты документации |
| https://context7.com/docs/resources/all-clients#claude-code | Точная команда Claude Code: --scope user --header ... --transport http context7 ... |
| https://context7.com/dashboard | Кабинет создания ключа, переход на страницу входа подтверждён |
| https://code.claude.com/docs/en/mcp | --scope user, личное хранение ~/.claude.json, -- перед npx, list/remove, статусы и различие OAuth и ключей |
| https://code.claude.com/docs/en/setup | Ссылка установки программы claude для команд терминала |
| https://code.visualstudio.com/docs/terminal/basics | Terminal → New Terminal |
| https://nodejs.org/en/download | Открыта официальная загрузка LTS на 06.10, номер версии не закреплён в тексте |
| https://nextjs.org/docs/app/getting-started/layouts-and-pages | Рабочий публичный адрес общей проверки; App Router задаёт адреса папками и файлами |
| https://theivansergeev.com/ailager/ | Предметный CTA: сайт под оффер и бот с цепочкой сообщений, без выдуманного срока или обещания всем участникам |

Дополнительная локальная проверка: claude mcp add --help и claude mcp remove --help. Подтверждены --scope, --transport, --header и --env, никакое подключение на компьютере пользователя не добавлялось и не удалялось

## Черновик 04.10 → статья 06.10

- Perplexity: основной маршрут OAuth → выбран маршрут с API-ключом по текущему README. OAuth также поддерживается по официальной справке; не утверждаем, что исчез
- Context7: основной маршрут /mcp/oauth → выбран ручной /mcp с Bearer-ключом по README и официальной инструкции Claude Code. OAuth по-прежнему поддерживается
- Firecrawl: OAuth сохранён; добавлена раскрываемая альтернатива с API-ключом и объяснение, что нельзя держать два подключения вместо одного
- Playwright: пакет и требование Node.js 18+ сохранены; понятное объяснение отличия MCP от CLI и проверка существующего файла скриншота
- Отдельные команды Codex → одна строка о совместимости, весь маршрут относится к Claude Code
- Численные лимиты Firecrawl, цены и неподтверждённые обещания → убраны. «10%», «самая мощная», «любые сайты», «весь стиль», «все инструменты» не перенесены как факты
- Общая задача без конкретных шагов → запрос для Next.js /about, версия из проекта либо свежий стабильный выпуск, четыре вызова и таблица результатов

Запросы читателю проверяют текущую версию в момент выполнения, номер версии не зафиксирован как вечный факт

Загрузка raw.githubusercontent.com через Python завершилась тайм-аутами TLS, поэтому на сохранённые копии README не ссылаемся. Все сведения выше получены с открытых официальных страниц через web
