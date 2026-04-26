from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


class ConversionError(RuntimeError):
    pass


ALLOWED_EXTENSIONS = {".doc", ".docx"}


def convert_word_to_pdf(input_path: Path, timeout: int = 120) -> Path:
    input_path = input_path.resolve()
    if not input_path.is_file():
        raise ConversionError(f"Input file does not exist: {input_path}")
    if input_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ConversionError("Input file must have .doc or .docx extension")

    out_dir = input_path.parent

    with tempfile.TemporaryDirectory(prefix="lo_profile_") as profile_dir:
        cmd = [
            "soffice",
            "--headless",
            "--nologo",
            "--norestore",
            "--nofirststartwizard",
            f"-env:UserInstallation={Path(profile_dir).resolve().as_uri()}",
            "--convert-to",
            "pdf:writer_pdf_Export",
            "--outdir",
            str(out_dir),
            str(input_path),
        ]

        try:
            result = subprocess.run(
                cmd,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ConversionError(f"LibreOffice conversion timed out after {timeout}s") from exc
        except FileNotFoundError as exc:
            raise ConversionError("LibreOffice executable 'soffice' was not found") from exc

    pdf_path = input_path.with_suffix(".pdf")
    if result.returncode != 0:
        raise ConversionError(
            "LibreOffice conversion failed "
            f"(exit={result.returncode}, stdout={result.stdout!r}, stderr={result.stderr!r})"
        )
    if not pdf_path.is_file():
        raise ConversionError(
            "LibreOffice did not create PDF "
            f"(stdout={result.stdout!r}, stderr={result.stderr!r})"
        )

    return pdf_path


def convert_docx_to_pdf(input_path: Path, timeout: int = 120) -> Path:
    return convert_word_to_pdf(input_path, timeout)
