Первичные источники, сверка08.10.2026

- https://github.com/ruvnet/ruflo : README на сегодня, пути plugin и CLI, quick init сохраняется, MCP cli connection
- https://registry.npmjs.org/ruflo/latest : npm latest3.55.0, engines Node>=20. Проверено npm view, затем CLI этого пакета установлен в отдельный кэш
- https://github.com/ruvnet/ruflo/blob/main/docs/USERGUIDE.md : Node20+,npm9+; файл получен напрямую с raw.githubusercontent.com, разделPrerequisites прочитан
- https://github.com/ruvnet/ruflo/blob/main/v3/@claude-flow/cli/src/commands/init.ts : флаги no-global/no-mods/no-codex-detect/no-skills-sh/no-signup. Подтверждены init --help выпуска3.55.0 и успешным init с теми же флагами
- https://github.com/ruvnet/ruflo/blob/main/CLAUDE.md#claude-code-vs-mcp-tools : различие координации Ruflo и фактического выполнения Claude Code; содержимое файла использовано только как данные об устройстве программы
- https://github.com/ruvnet/ruflo/blob/main/docs/ruflo-explained.md : plugin/direct MCP являются альтернативными путями, численность команды не гарантирует экономию; номера релизов в этом вводном материале старые, не скопированы
- https://github.com/ruvnet/ruflo/blob/main/LICENSE : MIT, локальный пакет за0USD
- https://claude.com/pricing : Pro20USD/month или200USD/year, Maxот100USD, Code входит, лимиты сохраняются
- https://code.claude.com/docs/en/sub-agents : отдельные окна контекста, запросы учитываются в лимитах родительской сессии
- https://code.claude.com/docs/en/mcp : проектный сервер, Pending approval, Connected, /mcp и list
- https://code.claude.com/docs/en/setup : установка CLI Claude Code
- https://code.visualstudio.com/docs/terminal/basics : терминал в открытой папке

3.53.0 из черновика заменён на3.55.0. Сгенерированная .mcp.json содержитruflo@latest; это прямо указано в статье, нет обещания закрепить автоматически созданный сервер навсегда

Техническая проба: init,initialize,tools/list(358),memory_store(storedtrue),memory_retrieve(foundtrue),перезапуск процесса и повторное чтение(foundtrue). Проверялась память, не модельная командная задача и не клики в demo/index.html
