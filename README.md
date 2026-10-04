# Каталог гайдов

Один репозиторий для всех публичных раздаток и статей

## Постоянная структура

- `claude-ai/` - инструкции по Claude.ai
- `vaybkoding-claude/` - материалы по Claude Code
- `vaybkoding-codex/` - материалы по Codex
- `gpt-dlya-nachinayushchih/` - GPT для начинающих
- `gpt-dlya-prodolzhayushchih/` - GPT для продолжающих

Каждый материал хранится в собственной папке с `index.html` и получает отдельный URL. Главная страница отвечает только за каталог и переходы между категориями

## Сборка и индексация

После добавления статьи или изменения статуса в `data/statyi.json`:

```sh
python3 scripts/sobrat_glavnuyu.py
python3 scripts/sobrat_glavnuyu.py --proverit
python3 -m unittest discover -s tests -q
node --test tests/*.test.cjs
```

Сборка обновляет главную, подписи обложек, метатеги robots статей, `sitemap.xml` и `robots.txt`. В sitemap входят главная и статьи со `status: live`, у которых нет непустого `noindex_reason`. Остальные сохраняют `noindex, nofollow`. Проверка `--proverit` обнаруживает расхождения без записи файлов

`noindex_reason` хранит причину запрета индексации, например высокий риск из юридического аудита. Изменение статуса на `live` не снимает этот запрет. Удалять причину следует после решения владельца и повторного аудита. Юридический аудит 05.10.2026: `audits/2026-10-05-yurist.md`
