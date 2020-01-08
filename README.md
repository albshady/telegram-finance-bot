Telegram бот для учёта личных расходов и ведения бюджета, вдохновленный 
[данным великолепным видео](https://www.youtube.com/watch?v=Kh16iosOTIQ),
но, в отличие от [первоисточника](https://github.com/alexey-goloburdin/telegram-finance-bot), 
вместо `SQLite` используется `Google Spreadsheets`, так как мне показалось это более удобным для последующей аналитики.


В переменных окружения надо проставить API токен бота, а также словарь, [полученный для доступа к Google Drive API]
(https://console.developers.google.com/apis/).

`API_TOKEN` — API токен бота

`CREDS` — словарь с данными API

Для более точной настройки бота можете изучить константы в файле `settings.py`.


[Таблица для мониторинга изменений](https://docs.google.com/spreadsheets/d/1xBJutyuL4vJp0C_3T7cXQgOO-wLx-dbrHUxtJNiUjvM/edit?usp=sharing)
