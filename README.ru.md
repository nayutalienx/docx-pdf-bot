# DOC/DOCX to PDF Telegram Bot

[English README](README.md)

Production-ready Telegram-бот для маленького Linux VPS: пользователь отправляет `.doc` или `.docx`, бот конвертирует документ в PDF через LibreOffice headless и отправляет PDF обратно.

Архитектура намеренно простая: Python 3.11+, aiogram 3.x, `asyncio.Queue`, один worker и одна конвертация LibreOffice одновременно. Docker, Redis, Celery и база данных не используются.

## Возможности

- Принимает только `.doc` и `.docx`.
- Ограничивает размер файла до 20 МБ.
- Ставит задачи в очередь с лимитом 5.
- Выполняет только одну конвертацию одновременно.
- Для каждой задачи создает отдельную временную папку.
- Для каждой конвертации создает отдельный профиль LibreOffice.
- Удаляет временные файлы после завершения задачи.
- Логирует ошибки в stdout/stderr для `journalctl`.

## 1. Создание бота через BotFather

1. Откройте Telegram и найдите `@BotFather`.
2. Отправьте команду `/newbot`.
3. Укажите имя бота.
4. Укажите username бота, который заканчивается на `bot`.
5. Скопируйте выданный токен. Его нужно сохранить в `.env` на сервере.

Не публикуйте токен в GitHub, чатах, логах или README.

## 2. Установка системных зависимостей на Ubuntu/Debian

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip libreoffice libreoffice-writer fonts-dejavu fonts-liberation fonts-crosextra-carlito fonts-crosextra-caladea fontconfig
fc-cache -f -v
```

Пакет `libreoffice-writer` нужен для конвертации документов Word. Шрифты важны для качества PDF: если на сервере нет шрифтов, использованных в документе, LibreOffice будет подставлять похожие, и верстка может отличаться от оригинала.

## 3. Создание venv

```bash
cd /opt/docx-pdf-bot
python3 -m venv venv
```

## 4. Установка Python-зависимостей

```bash
/opt/docx-pdf-bot/venv/bin/pip install --upgrade pip
/opt/docx-pdf-bot/venv/bin/pip install -r requirements.txt
```

## 5. Настройка `.env`

```bash
cp .env.example .env
nano .env
```

Файл должен содержать:

```env
BOT_TOKEN=123456789:your_real_bot_token
```

Файл `.env` добавлен в `.gitignore` и не должен попадать в репозиторий.

## 6. Ручной запуск

```bash
cd /opt/docx-pdf-bot
/opt/docx-pdf-bot/venv/bin/python bot.py
```

После запуска отправьте боту DOC или DOCX-файл до 20 МБ. Бот должен ответить: `Файл принят, конвертирую в PDF…`, затем прислать PDF.

## 7. Установка systemd service

Скопируйте проект в `/opt/docx-pdf-bot`, затем установите unit:

```bash
sudo cp /opt/docx-pdf-bot/systemd/docx-pdf-bot.service /etc/systemd/system/docx-pdf-bot.service
sudo systemctl daemon-reload
sudo systemctl enable docx-pdf-bot
sudo systemctl start docx-pdf-bot
```

Проверка статуса:

```bash
sudo systemctl status docx-pdf-bot
```

## 8. Логи

```bash
journalctl -u docx-pdf-bot -f
```

Если конвертация падает, подробности LibreOffice и traceback Python будут видны в логах.

## 9. Ограничения качества конвертации

LibreOffice хорошо конвертирует большинство DOCX и умеет обрабатывать многие старые DOC-файлы, но результат может отличаться от Microsoft Word. Старый формат `.doc` обычно менее предсказуем, чем `.docx`. Возможные причины:

- в документе используются отсутствующие на сервере шрифты;
- есть сложные таблицы, плавающие элементы, SmartArt, макросы или нестандартные поля;
- документ поврежден или создан не полностью совместимым редактором;
- в документе есть внешние ссылки или объекты, которые LibreOffice не может корректно обработать.

Для важных шаблонов проверяйте результат на реальных документах и при необходимости добавляйте нужные шрифты на сервер.

## 10. Почему важны шрифты

Документы Word хранят ссылки на названия шрифтов, но не всегда включают сами файлы шрифтов. Если сервер не знает нужный шрифт, LibreOffice подставит другой. Из-за этого могут измениться переносы строк, размеры таблиц, номера страниц и общий вид PDF.

Минимальный набор шрифтов в инструкции выше закрывает большинство типичных документов. Для корпоративных шаблонов может потребоваться установка дополнительных лицензированных шрифтов.

## 11. Почему бот конвертирует по одному файлу за раз

LibreOffice headless потребляет заметное количество CPU и RAM. На VPS с 2 GB RAM параллельные конвертации могут привести к зависаниям, OOM killer и поврежденным результатам. Поэтому бот использует очередь, но запускает только один процесс конвертации одновременно.

## Команды для деплоя из Git

```bash
sudo mkdir -p /opt/docx-pdf-bot
sudo chown "$USER":"$USER" /opt/docx-pdf-bot
git clone <your-repo-url> /opt/docx-pdf-bot
cd /opt/docx-pdf-bot
python3 -m venv venv
/opt/docx-pdf-bot/venv/bin/pip install --upgrade pip
/opt/docx-pdf-bot/venv/bin/pip install -r requirements.txt
cp .env.example .env
nano .env
sudo cp systemd/docx-pdf-bot.service /etc/systemd/system/docx-pdf-bot.service
sudo systemctl daemon-reload
sudo systemctl enable --now docx-pdf-bot
```
