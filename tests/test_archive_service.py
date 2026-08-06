"""Tests for moving an approved PDF into its archive directory."""

import pytest

from invoice_reader.archive.archive_errors import ArchiveConflictError, ArchiveError
from invoice_reader.archive.archive_service import ArchiveService


def test_moves_pdf_to_archive_directory(tmp_path) -> None:
    source_path = tmp_path / "source.pdf"
    source_path.write_bytes(b"pdf")
    archive_directory = tmp_path / "archive"
    archive_directory.mkdir()

    archive_path = ArchiveService().archive(str(source_path), str(archive_directory))

    assert not source_path.exists()
    assert (archive_directory / "source.pdf").read_bytes() == b"pdf"
    assert archive_path == str(archive_directory / "source.pdf")


def test_requires_choice_when_archive_has_same_filename(tmp_path) -> None:
    source_path = tmp_path / "source.pdf"
    source_path.write_bytes(b"new")
    archive_directory = tmp_path / "archive"
    archive_directory.mkdir()
    (archive_directory / "source.pdf").write_bytes(b"old")

    with pytest.raises(ArchiveConflictError):
        ArchiveService().archive(str(source_path), str(archive_directory))

    ArchiveService().archive(str(source_path), str(archive_directory), overwrite=True)
    assert (archive_directory / "source.pdf").read_bytes() == b"new"


def test_rejects_a_missing_archive_directory(tmp_path) -> None:
    source_path = tmp_path / "source.pdf"
    source_path.write_bytes(b"pdf")

    with pytest.raises(ArchiveError):
        ArchiveService().archive(str(source_path), str(tmp_path / "missing"))
