from __future__ import annotations

import asyncio
import logging
import shutil
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Document, FSInputFile, Message

from config import (
    BOT_TOKEN,
    CONVERT_TIMEOUT_SECONDS,
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
    QUEUE_MAXSIZE,
)
from converter import ConversionError, convert_word_to_pdf


ALLOWED_EXTENSIONS = {".doc", ".docx"}
ALLOWED_MIME_TYPES = {
    "application/msword",
    "application/vnd.ms-word",
    "application/x-msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",
}

queue: asyncio.Queue[ConversionJob]
worker_task: asyncio.Task[None] | None = None


@dataclass(frozen=True)
class ConversionJob:
    bot: Bot
    chat_id: int
    document: Document
    input_name: str
    output_name: str


def sanitize_filename(filename: str | None) -> str:
    name = unicodedata.normalize("NFKC", Path(filename or "document.docx").name)
    suffix = Path(name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        suffix = ".docx"
    stem = Path(name).stem
    safe_chars: list[str] = []
    for char in stem:
        if char.isalnum() or char in {" ", ".", "_", "-"}:
            safe_chars.append(char)
        else:
            safe_chars.append("_")
    stem = "".join(safe_chars).strip(" ._-")
    if not stem:
        stem = "document"
    return f"{stem[:80]}{suffix}"


def pdf_filename_from_word(filename: str) -> str:
    return f"{Path(filename).stem}.pdf"


def is_word_document(document: Document) -> bool:
    filename = document.file_name or ""
    if Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        return False
    if document.mime_type and document.mime_type not in ALLOWED_MIME_TYPES:
        return False
    return True


async def convert_worker() -> None:
    while True:
        job = await queue.get()
        temp_dir: Path | None = None
        try:
            temp_dir = Path(tempfile.mkdtemp(prefix="docx_pdf_bot_"))
            input_path = temp_dir / job.input_name

            await job.bot.download(job.document, destination=input_path)

            pdf_path = await asyncio.to_thread(
                convert_word_to_pdf,
                input_path,
                CONVERT_TIMEOUT_SECONDS,
            )

            await job.bot.send_document(
                chat_id=job.chat_id,
                document=FSInputFile(pdf_path, filename=job.output_name),
                caption="Готово. PDF-файл во вложении.",
            )
        except asyncio.CancelledError:
            raise
        except (ConversionError, Exception):
            logging.exception("Failed to process Word conversion job")
            await job.bot.send_message(
                chat_id=job.chat_id,
                text=(
                    "Не удалось конвертировать файл. Возможно, документ "
                    "повреждён или слишком сложный."
                ),
            )
        finally:
            if temp_dir is not None:
                shutil.rmtree(temp_dir, ignore_errors=True)
            queue.task_done()


async def on_startup() -> None:
    global queue, worker_task
    queue = asyncio.Queue(maxsize=QUEUE_MAXSIZE)
    worker_task = asyncio.create_task(convert_worker())
    logging.info("Word to PDF bot started")


async def on_shutdown() -> None:
    if worker_task is not None:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
    logging.info("Word to PDF bot stopped")


async def start_handler(message: Message) -> None:
    await message.answer(
        "Отправьте DOC или DOCX-файл до 20 МБ, и я конвертирую его в PDF."
    )


async def document_handler(message: Message) -> None:
    document = message.document
    if document is None:
        return

    if not is_word_document(document):
        await message.answer("Поддерживаются только файлы DOC и DOCX.")
        return

    if document.file_size and document.file_size > MAX_FILE_SIZE_BYTES:
        await message.answer(f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE_MB} МБ.")
        return

    if queue.full():
        await message.answer("Сервер занят. Попробуйте отправить файл позже.")
        return

    input_name = sanitize_filename(document.file_name)
    queue.put_nowait(
        ConversionJob(
            bot=message.bot,
            chat_id=message.chat.id,
            document=document,
            input_name=input_name,
            output_name=pdf_filename_from_word(input_name),
        )
    )
    await message.answer("Файл принят, конвертирую в PDF…")


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.message.register(start_handler, CommandStart())
    dp.message.register(document_handler, F.document)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
