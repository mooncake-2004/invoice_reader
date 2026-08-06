"""Move approved PDFs into a user-selected archive directory."""

import os
from pathlib import Path
import shutil
from uuid import uuid4

from invoice_reader.archive.archive_errors import ArchiveConflictError, ArchiveError


class ArchiveService:
    """Archive one approved source PDF without changing Excel data."""

    def archive(self, pdf_path: str, archive_directory: str, filename: str | None = None, overwrite: bool = False) -> str:
        """Move the PDF and return its final archive path."""
        source_path = Path(pdf_path)
        target_path = self._target_path(archive_directory, filename or source_path.name)
        if target_path.exists() and not overwrite:
            raise ArchiveConflictError(target_path.name)
        self._move(source_path, target_path)
        return str(target_path)

    def _target_path(self, archive_directory: str, filename: str) -> Path:
        directory = Path(archive_directory)
        if not directory.is_dir():
            raise ArchiveError("归档目录不存在或无法访问。")
        if not filename or Path(filename).name != filename:
            raise ArchiveError("归档文件名无效。")
        return directory / filename

    def _move(self, source_path: Path, target_path: Path) -> None:
        if not source_path.is_file():
            raise ArchiveError("源 PDF 文件不存在或无法访问。")
        try:
            if source_path.drive.casefold() == target_path.drive.casefold():
                os.replace(source_path, target_path)
            else:
                self._copy_then_remove(source_path, target_path)
        except OSError as error:
            raise ArchiveError(str(error)) from error

    def _copy_then_remove(self, source_path: Path, target_path: Path) -> None:
        temporary_path = target_path.with_name(f".{target_path.name}.{uuid4().hex}.tmp")
        try:
            shutil.copy2(source_path, temporary_path)
            os.replace(temporary_path, target_path)
            source_path.unlink()
        finally:
            if temporary_path.exists():
                temporary_path.unlink()
