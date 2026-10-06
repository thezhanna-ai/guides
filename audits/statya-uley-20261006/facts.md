# Факты УЛЕЙ, 06.10.2026

Проверены живые официальные README, USERGUIDE, CLAUDE.md, STATUS.md, CHANGELOG.md и исходный init.ts. Commit main Ruflo: 7128ff26f3979e8c7829e061831d11036926c2a5, 06.10.2026 07:15:49 UTC. Запись npm latest: ruflo 3.53.0, engines.node >=20.0.0. Снимки метаданных: source-snapshot.json и package-check.json

## Было в черновике 04.10 -> стало

- `npx ruflo@latest init wizard` -> основной путь `npx ruflo@latest init --no-global`; wizard остаётся упомянутым интерактивным вариантом. Короткий init подтверждён [README](https://github.com/ruvnet/ruflo#cli-install), --no-global - живым CLI help и [исходником init.ts](https://github.com/ruvnet/ruflo/blob/main/v3/@claude-flow/cli/src/commands/init.ts). Флаг отключает запись указателя в пользовательский CLAUDE.md
- Node.js 20+, npm 9+ -> требования сохранились, удалён не относящийся к Ruflo совет про HyperFrames. [USERGUIDE, Prerequisites](https://github.com/ruvnet/ruflo/blob/main/docs/USERGUIDE.md#prerequisites)
- Пакет Ruflo, имя сервера claude-flow -> сохранились. Команда `claude mcp add claude-flow -- npx -y ruflo@latest mcp start` соответствует [USERGUIDE](https://github.com/ruvnet/ruflo/blob/main/docs/USERGUIDE.md#claude-code-mcp-integration). В свежем init действительно создаётся .mcp.json с этим именем
- Запись сервера в списке -> различаем запись, Pending approval и успешный вызов. Добавлен переход в Claude Code для одобрения проектного сервера. [MCP Server status](https://code.claude.com/docs/en/mcp#server-status)
- Учебный текстовый checklist.md -> локальная demo/index.html с флажками, счётчиком и сбросом, отдельным исполнителем и проверяющим. Это составленное для статьи учебное задание, не команда разработчика Ruflo. Видимая ручная проверка: 2 из 6, затем 0 из 6
- Координация/роли в Ruflo -> отдельно требуются реальные задания субагентам Claude Code. [Ruflo, Claude Code vs MCP tools](https://github.com/ruvnet/ruflo/blob/main/CLAUDE.md#claude-code-vs-mcp-tools) прямо различает координацию и выполнение
- Семантический поиск чек-листа -> точное чтение ключей uley-demo-brief и uley-demo-result в одном namespace uley-demo; новый чат сверяет память с файлами. Живые схемы memory_store и memory_retrieve подтверждают key/value/namespace. Запись и чтение проверены через MCP, включая чтение после перезапуска процесса
- 60+ / 100+ агентов, экономия токенов, +250% объёма, номер один на GitHub -> в публичную статью не перенесены. Документы содержат разновременные показатели, они не являются проверкой скорости или числа одновременно работающих исполнителей читателя
- Бывший Claude Flow -> подтверждено официальным [CHANGELOG](https://github.com/ruvnet/ruflo/blob/main/CHANGELOG.md), переименование в выпуске 3.5.0

## Выполненная техническая проба

В отдельной папке /private/tmp/statya-uley-smoke, с отдельным npm-кэшем, установлен и запущен ruflo@3.53.0. --version: ruflo v3.53.0. init --help содержит короткий init и --no-global. Инициализация завершилась с 12 папками и 110 файлами. Для пробы отключены необязательные моды, автоматическое подключение Codex, регистрация skills.sh и предложение регистрации: `init --no-global --no-mods --no-codex-detect --no-skills-sh --no-signup`. Это проверка основного механизма, не заявление о выполнении всех необязательных действий дефолтного init

Созданы CLAUDE.md, .claude-flow/config.yaml, .mcp.json. Сервер запущен через `node .../ruflo/bin/ruflo.js mcp start` с текущей папкой пробы и CLAUDE_FLOW_CWD. initialize и tools/list успешны, получено 358 инструментов. memory_store: success=true, stored=true. memory_retrieve: found=true и исходное значение. После остановки сервера новый процесс вернул ту же запись с found=true, без повторной записи. Подробности: mcp-transcript.json и mcp-restart-transcript.json

Не запускалась модельная сессия Claude Code с командным промптом, не менялись пользовательские MCP-подключения. Полная командная задача, клики в странице и скрины предназначены для живого прохода Claude по ТЗ. Проба доказывает работу инициализации, MCP и хранения памяти, а не выполнение demo/index.html

## Официальные источники остальных действий

- [Claude Code setup](https://code.claude.com/docs/en/setup): терминальная установка, вход и доступ
- [VS Code Terminal basics](https://code.visualstudio.com/docs/terminal/basics): терминал в текущей папке
- [Node.js download](https://nodejs.org/en/download): LTS
- [Subagents](https://code.claude.com/docs/en/sub-agents): отдельный контекст, последовательная передача задания, границы применения
- [Ruflo Troubleshooting](https://github.com/ruvnet/ruflo/wiki/Troubleshooting): doctor, Node.js, MCP

Оболочка и действующий CTA взяты из pyat-skillov-claude-code на guides main 32050d7. Условия и сроки обучения не добавлены. Лендинг Лагеря при обращении web вернул Internal Error; статья использует уже действующую формулировку сайта
