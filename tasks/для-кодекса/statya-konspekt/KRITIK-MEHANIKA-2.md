# Механика, круг 2

Чисто. Проверка /private/tmp/audit-konspekt.py по итоговой странице:

```json
{
  "p_without_final_mark": 0,
  "long_dashes": 0,
  "step_zero": 0,
  "names_outside_standard_ad": 0,
  "banned_cost_words_outside_standard_ad": 0,
  "reader_gender_verbs": 0,
  "prompt_count": 5,
  "result_comments": 5,
  "b": 38,
  "result": 6,
  "warn_card": 5,
  "standard_ad_bytes_equal": true,
  "robots": [
    "noindex, nofollow"
  ]
}
```

Штатный section.cta исключён только из текстовых запретов и пунктуации: его байты должны быть идентичны образцу. ID копирования и якоря уникальны и существуют. Пять невидимых комментариев результата; чужих скринов и видимых заглушек нет.

Исключённые рекламные байты: section.cta целиком и две штатные строки PARTNER_LINK. Если исключить только section.cta, останется одно вхождение theivansergeev в штатном JavaScript, который побайтно совпадает с образцом. Нового имени или ссылки вне рекламы нет
