# DOCX to PDF Telegram Bot

Production-ready Telegram bot for a small Linux VPS: a user sends a `.docx` file, the bot downloads it, converts it to PDF with LibreOffice headless, sends the PDF back, and removes temporary files.

[Русская версия](README.ru.md)

The architecture is intentionally simple: Python 3.11+, aiogram 3.x, `asyncio.Queue`, one worker, and one LibreOffice conversion at a time. No Docker, Redis, Celery, or database.

## Features

- Accepts only `.docx` files.
- Limits input files to 20 MB.
- Uses a bounded queue with `maxsize=5`.
- Runs only one conversion at a time.
- Creates a separate temporary directory for every job.
- Uses a separate LibreOffice profile directory for every conversion.
- Deletes temporary files after each job.
- Logs errors to stdout/stderr for `journalctl`.
- Preserves the original document name when sending the resulting PDF.

## 1. Create a bot with BotFather

1. Open Telegram and find `@BotFather`.
2. Send `/newbot`.
3. Choose a display name.
4. Choose a username ending with `bot`.
5. Copy the token and store it in `.env` on your server.

Do not publish the token in GitHub, chats, logs, or README files.

## 2. Install system dependencies on Ubuntu/Debian

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip libreoffice libreoffice-writer fonts-dejavu fonts-liberation fonts-crosextra-carlito fonts-crosextra-caladea fontconfig
fc-cache -f -v
```

`libreoffice-writer` is required for DOCX conversion. Fonts matter for PDF quality: if the server does not have the fonts used by the document, LibreOffice will substitute similar fonts, and the layout may differ from the original.

## 3. Create a venv

```bash
cd /opt/docx-pdf-bot
python3 -m venv venv
```

## 4. Install Python dependencies

```bash
/opt/docx-pdf-bot/venv/bin/pip install --upgrade pip
/opt/docx-pdf-bot/venv/bin/pip install -r requirements.txt
```

## 5. Configure `.env`

```bash
cp .env.example .env
nano .env
```

The file must contain:

```env
BOT_TOKEN=123456789:your_real_bot_token
```

`.env` is listed in `.gitignore` and must not be committed.

## 6. Run manually

```bash
cd /opt/docx-pdf-bot
/opt/docx-pdf-bot/venv/bin/python bot.py
```

After startup, send the bot a DOCX file up to 20 MB. The bot should reply in Russian: `Файл принят, конвертирую в PDF…`, then send the PDF.

## 7. Install the systemd service

Copy the project to `/opt/docx-pdf-bot`, then install the unit:

```bash
sudo cp /opt/docx-pdf-bot/systemd/docx-pdf-bot.service /etc/systemd/system/docx-pdf-bot.service
sudo systemctl daemon-reload
sudo systemctl enable docx-pdf-bot
sudo systemctl start docx-pdf-bot
```

Check status:

```bash
sudo systemctl status docx-pdf-bot
```

## 8. Logs

```bash
journalctl -u docx-pdf-bot -f
```

If conversion fails, LibreOffice diagnostics and Python tracebacks will be visible in the logs.

## 9. Conversion quality limits

LibreOffice converts most DOCX files well, but the result can differ from Microsoft Word. Common causes:

- the document uses fonts missing on the server;
- the document contains complex tables, floating elements, SmartArt, macros, or unusual page settings;
- the document is damaged or was created by a partially compatible editor;
- the DOCX contains external links or embedded objects LibreOffice cannot process correctly.

For important templates, test real documents and install the required fonts on the server when needed.

## 10. Why fonts matter

DOCX files often store font names without embedding the font files themselves. If the server does not have a required font, LibreOffice substitutes another one. That can change line breaks, table sizes, page numbers, and the overall PDF layout.

The minimal font set above covers many common documents. Corporate templates may require additional licensed fonts.

## 11. Why the bot converts one file at a time

LibreOffice headless can consume significant CPU and RAM. On a 2 GB RAM VPS, parallel conversions can cause stalls, OOM killer events, and unstable results. The bot therefore uses a queue but starts only one conversion process at a time.

## Deployment from Git

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
