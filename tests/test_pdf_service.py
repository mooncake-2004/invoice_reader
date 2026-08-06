"""Tests for opened-PDF file operations."""

import fitz

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
