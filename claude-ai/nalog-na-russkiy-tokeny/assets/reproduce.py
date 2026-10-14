"""Повторение опыта. Зависимость: tiktoken==0.14.0. Считает только текст."""
import tiktoken
SAMPLES = {'meeting': {'en': 'The meeting starts tomorrow at ten in the morning.', 'ru': 'Встреча начнётся завтра в десять утра.', 'hi': 'बैठक कल सुबह दस बजे शुरू होगी।', 'zh': '会议明天上午十点开始。'}, 'email': {'en': 'Write a short email to the client and ask them to confirm the meeting time.', 'ru': 'Напиши короткое письмо клиенту и попроси подтвердить время встречи.', 'hi': 'ग्राहक को एक छोटा ईमेल लिखो और उससे बैठक का समय पक्का करने के लिए कहो।', 'zh': '给客户写一封简短的邮件，请他确认会议时间。'}, 'summary': {'en': 'Summarize this article in three sentences. Keep the main facts and do not add anything of your own.', 'ru': 'Перескажи эту статью в трёх предложениях. Сохрани основные факты и ничего не добавляй от себя.', 'hi': 'इस लेख का सार तीन वाक्यों में लिखो। मुख्य तथ्यों को बनाए रखो और अपनी ओर से कुछ मत जोड़ो।', 'zh': '用三句话总结这篇文章。保留主要事实，不要添加自己的内容。'}}
for name in ("cl100k_base", "o200k_base"):
    enc = tiktoken.get_encoding(name)
    print(name)
    for language in ("en", "ru", "hi", "zh"):
        counts = [len(enc.encode(texts[language])) for texts in SAMPLES.values()]
        print(language, counts, "sum:", sum(counts))
