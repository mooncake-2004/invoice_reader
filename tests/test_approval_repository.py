"""Tests for local approval-record persistence."""

from invoice_reader.application.models import ExtractedField, InvoiceRecord
from invoice_reader.repositories.approval_repository import ApprovalRepository


def test_saves_and_finds_an_approved_pdf_record(tmp_path) -> None:
    pdf_path = tmp_path / "ABCDE.pdf"
    record = InvoiceRecord(
        file_path=str(pdf_path),
        plmn=ExtractedField(value="ABCDE"),
        invoice_no=ExtractedField(value="INV-1"),
        sdr_amount=ExtractedField(value="1.23"),
        tap_start=ExtractedField(value="10"),
        tap_end=ExtractedField(value="20"),
    )
    repository = ApprovalRepository(tmp_path / "approval_records.json")

    repository.save(record, "2026-08-06T10:00:00+08:00", "C:/monthly.xlsx", True)

    assert repository.find_by_pdf_path(str(pdf_path)) == {
        "plmn": "ABCDE",
        "invoice_no": "INV-1",
        "sdr_amount": "1.23",
        "tap_start": "10",
        "tap_end": "20",
        "approved_at": "2026-08-06T10:00:00+08:00",
        "pdf_file_path": str(pdf_path.resolve()),
        "excel_path": "C:/monthly.xlsx",
        "excel_written": True,
        "archive_path": "",
        "archived": False,
    }


def test_finds_a_record_again_after_its_pdf_is_archived(tmp_path) -> None:
    source_path = tmp_path / "source.pdf"
    archive_path = tmp_path / "archive" / "source.pdf"
    record = InvoiceRecord(file_path=str(source_path), plmn=ExtractedField(value="ABCDE"))
    repository = ApprovalRepository(tmp_path / "approval_records.json")

    repository.save(record, "2026-08-06T10:00:00+08:00", "C:/monthly.xlsx", True, str(archive_path), True)

    assert repository.find_by_pdf_path(str(archive_path)) is not None


def test_finds_completed_record_only_after_excel_and_archive_succeed(tmp_path) -> None:
    pdf_path = tmp_path / "source.pdf"
    archive_path = tmp_path / "archive" / "source.pdf"
    record = InvoiceRecord(file_path=str(pdf_path), plmn=ExtractedField(value="ABCDE"))
    repository = ApprovalRepository(tmp_path / "approval_records.json")

    repository.save(record, "2026-08-06T10:00:00+08:00", "C:/monthly.xlsx", False)
    assert repository.find_completed_by_pdf_path(str(pdf_path)) is None

    repository.save(record, "2026-08-06T10:00:00+08:00", "C:/monthly.xlsx", True)
    assert repository.find_completed_by_pdf_path(str(pdf_path)) is None

    repository.save(record, "2026-08-06T10:00:00+08:00", "C:/monthly.xlsx", True, str(archive_path), True)
    assert repository.find_completed_by_pdf_path(str(archive_path)) is not None
