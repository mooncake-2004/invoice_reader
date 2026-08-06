"""Tests for opened-PDF file operations."""

import fitz

from invoice_reader.archive.archive_service import ArchiveService
from invoice_reader.services.pdf_service import PdfService


def test_renames_open_pdf_and_updates_its_path(tmp_path) -> None:
    original_path = tmp_path / "original.pdf"
    document = fitz.open()
    document.new_page()
    document.save(original_path)
    document.close()
    service = PdfService()
    service.open(str(original_path))

    renamed_path = service.rename_current("ABCDE_MACHT.pdf")

    assert renamed_path == tmp_path / "ABCDE_MACHT.pdf"
    assert not original_path.exists()
    assert renamed_path.exists()
    assert service.path == renamed_path
    assert service.page_count == 1


def test_close_releases_the_opened_pdf_reference(tmp_path) -> None:
    pdf_path = tmp_path / "invoice.pdf"
    document = fitz.open()
    document.new_page()
    document.save(pdf_path)
    document.close()
    service = PdfService()
    service.open(str(pdf_path))

    service.close()

    assert service.path is None
    assert service.page_count == 0


def test_can_archive_after_closing_the_opened_pdf(tmp_path) -> None:
    pdf_path = tmp_path / "invoice.pdf"
    archive_directory = tmp_path / "archive"
    archive_directory.mkdir()
    document = fitz.open()
    document.new_page()
    document.save(pdf_path)
    document.close()
    service = PdfService()
    service.open(str(pdf_path))
    service.close()

    archive_path = ArchiveService().archive(str(pdf_path), str(archive_directory))

    assert archive_path == str(archive_directory / "invoice.pdf")
    assert not pdf_path.exists()
