# Development Rules

- Do not add Docker unless explicitly requested.
- Do not add Redis or Celery unless explicitly requested.
- Do not increase DOCX conversion concurrency above 1 for a 2 GB RAM VPS.
- Do not use `shell=True`.
- Do not store user files after conversion.
- Delete all temporary files after every job.
- Check any changes with a local run or syntax check before handing them off.
- Keep the architecture simple: aiogram, `asyncio.Queue`, LibreOffice CLI, systemd.
- Never commit credentials, bot tokens, passwords, `.env`, private keys, or server access details to the repository.
- Keep `.env.example` as a placeholder-only file.
