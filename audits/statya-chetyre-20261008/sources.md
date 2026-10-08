Сверка первоисточников 08.10.2026 через web

- https://github.com/perplexityai/modelcontextprotocol : remote endpoint, Bearer, perplexity_search; текущий README описывает Agent API, старые Sonar-утверждения не перенесены
- https://docs.perplexity.ai/docs/getting-started/integrations/mcp-server : API-ключ/OAuth, API-организация и отдельный расход
- https://docs.perplexity.ai/docs/getting-started/pricing : Search API $5/1000, Fast $1/1000; Agent API web_search $0.0025 сверх токенов
- https://github.com/microsoft/playwright-mcp : Node18+, npx @playwright/mcp@latest, локальный сервер, Apache2.0, отличие MCP/CLI
- https://github.com/firecrawl/firecrawl-mcp-server : mcp-oauth, keyless scrape/search/parse, Bearer для ключа
- https://docs.firecrawl.dev/quickstarts/claude-code : claude mcp add, /mcp, browser sign-in, одна активная запись
- https://www.firecrawl.dev/pricing : с04.09.2026 Free1000/месяц, Hobby19 monthly/16annual, 5000credit, basic scrape1credit
- https://github.com/upstash/context7 : версии, resolve-library-id/query-docs, API-ключ
- https://context7.com/docs/resources/all-clients : точная команда remote Bearer для Claude Code, OAuth не отменён
- https://context7.com/plans : Free1000/месяц; Pro10USD/seat,2000calls, excess5USD/1000. Unlimited означает отсутствие блокировки с дополнительным расходом
- https://claude.com/pricing : Pro20USD/month или200USD/year, Code включён, лимиты и налоги сохраняются
- https://code.claude.com/docs/en/mcp : scopes,list,remove,--,statuses,OAuth
- https://code.claude.com/docs/en/setup : установка CLI
- https://code.visualstudio.com/docs/terminal/basics : Terminal > New Terminal
- https://nextjs.org/docs/app/getting-started/layouts-and-pages : публичный адрес документации для общей проверки

В закрытые кабинеты не входили. Фактические вызовы четырёх MCP на аккаунтах читателя не тестировались
