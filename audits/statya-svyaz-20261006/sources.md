# Источники и изменения фактов СВЯЗЬ

Дата проверки: 06.10.2026. Только первичные страницы, чтение через web, без запуска Chrome и подключения аккаунтов

| Источник | Что подтверждает |
|---|---|
| https://composio.dev/mcp | Основной путь через Install plugin, отдельный ручной URL https://connect.composio.dev/mcp |
| https://composio.dev/toolkits/composio/framework/chatgpt | Установка плагина, вход через Allow access, @Composio, запасная форма Plugins → MCP → Add server; каталог 1500+ интеграций |
| https://chatgpt.com/plugins/plugin_asdk_app_6a58503580c08191b78cc5bdaf4eba6e | Карточка Composio в каталоге ChatGPT, кнопка Install plugin, разработчик Sampark Inc; не заявляем наличие OpenAI Verified |
| https://help.openai.com/en/articles/20001256-plugins-in-chatgpt | Плагины, установка, Connect, зависимость конкретных возможностей от аккаунта и рабочей организации |
| https://help.openai.com/en/articles/20001494-connecting-and-managing-app-accounts-in-chatgpt | Settings → Plugins, упоминание @, авторизация нужного аккаунта, Disconnect, сохранение существующих чатов после отключения |
| https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt | Ручной MCP: web; Business admins/owners, Enterprise/Edu доступ по роли; Settings → Apps → Advanced Settings, Apps → Create, OAuth, Scan Tools, Create; запись Business/Enterprise/Edu, Pro read/fetch; выбор приложения для отдельного сообщения |
| https://composio.dev/toolkits/gmail/framework/chatgpt | Авторизация Gmail и отдельный инструмент Create email draft |
| https://docs.composio.dev/toolkits/gmail | Актуальный список Gmail: Fetch emails, Get Profile, List Drafts, Create email draft, версия 20260915_00 |
| https://composio.dev/toolkits/gmail/framework/cli | Пример создания черновика с получателем, темой и текстом; в статье инструменту передаётся реальный адрес читателя, отправка запрещена |
| https://support.google.com/mail/answer/7190?hl=en | Поиск is:unread и разница между сообщениями и цепочками |
| https://support.google.com/accounts/answer/13533235?hl=ru | Отдельное управление доступом стороннего приложения в аккаунте Google |
| https://composio.dev/toolkits/notion/framework/chatgpt | Поиск страниц и чтение Notion |
| https://www.notion.com/help/add-and-manage-connections-with-the-api | Доступ подключения к выбранным страницам; настройки Connections и ограничения организации |
| https://composio.dev/pricing | В статье только ссылка на условия, чисел лимитов нет |
| https://theivansergeev.com/ailager/ | Сайт под оффер, бот с цепочкой сообщений, сборка первых частей проекта; CTA не обещает все проекты каждому участнику |

## Было в черновике → стало

- Начать с Developer mode, Plus или выше → сначала плагин через актуальную карточку каталога ChatGPT; каталог доступен по планам, возможности конкретного плагина зависят от аккаунта и рабочего пространства
- Settings → Security and login → основной путь без ручного режима разработчика; запасной путь Apps → Advanced Settings по OpenAI, альтернативная форма Plugins → MCP только по документации Composio и только если она есть в аккаунте
- Справка OpenAI не открылась у предыдущего проверяющего → 06.10 открылась. Ограничения записи приведены конкретно для ручного MCP, без переноса этого списка тарифов на плагин
- https://developers.openai.com/api/docs/guides/developer-mode из черновика → у текущего web возвращает 404; использована доступная справка OpenAI
- Composio 1000+ приложений → актуальная страница заявляет 1500+ интеграций. В статье оставлено консервативное «более чем тысяча», с атрибуцией Composio
- Числа лимитов и срок настройки в минуту → удалены, только ссылка на Pricing и конкретные шаги без обещания времени
- Черновик без точного содержимого → отдельный копируемый запрос с тестовой темой, текстом, своим адресом получателя, запретом отправки, проверкой идентификатора и открытием результата в Gmail
- Ответ приложения в чате → сверка с Gmail, затем реально сохранённый черновик как критерий результата. Это инструкция для читателя, не заявление об исполнении в аккаунте владельца

## Границы проверки

Не выполнялись вход в Composio, Google и Notion, запросы к частной почте и создание черновика. Их живую проверку и съёмку экранов выполняет Claude по заданию владельца. Текст не выдаёт документационную проверку за работу в аккаунте
