# Тесты окончательной версии

Python и Node запущены после последней правки HTML, 11.10.2026

## Python

Команда: `/opt/homebrew/bin/python3.12 -m unittest discover -s tests -p 'test_*.py'`

```text
----------------------------------------------------------------------
Ran 160 tests in 28.131s

OK
```

## erid.test.cjs

Команда: `node --test tests/erid.test.cjs`

```text
ℹ tests 54
ℹ suites 0
ℹ pass 54
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 97.232958
```

## filtry.test.cjs

Команда: `node --test tests/filtry.test.cjs`

```text
ℹ tests 57
ℹ suites 0
ℹ pass 57
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 906.949667
```

## image-viewer.test.cjs

Команда: `node --test tests/image-viewer.test.cjs`

```text
ℹ tests 16
ℹ suites 0
ℹ pass 16
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 66.187375
```

## privacy.test.cjs

Команда: `node --test tests/privacy.test.cjs`

```text
ℹ tests 11
ℹ suites 0
ℹ pass 11
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 61.296667
```

## Сборщик и механика

`/opt/homebrew/bin/python3.12 scripts/sobrat_glavnuyu.py --proverit`: exit 0

```text
Главная совпадает с реестром
Подписи 53 статей совпадают с реестром
Индексация 53 статей, sitemap.xml и robots.txt совпадают с реестром
Политика данных и общие блоки согласия совпадают с шаблонами
```

`proverka.py`: exit 0, результат в MEHANICHESKAYA-SVERKA.json

`git diff --check`: exit 0

Chrome не запускался
