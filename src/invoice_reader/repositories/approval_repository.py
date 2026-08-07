"""Local JSON storage for invoices that have reached approval."""

import json
from pathlib import Path

from invoice_reader.application.models import InvoiceRecord
from invoice_reader.infrastructure.app_paths import approval_records_path
from invoice_reader.templates.template_models import FIELD_NAMES


class ApprovalRepository:
    """Persist small per-invoice approval records under local app data."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = approval_records_path() if path is None else path

    def find_by_pdf_path(self, pdf_path: str) -> dict[str, object] | None:
        """Return the saved approval record for the exact PDF path, if any."""
        absolute_path = str(Path(pdf_path).resolve())
        return next(
            (
                record
                for record in self._load()
                if record["pdf_file_path"] == absolute_path or record.get("archive_path") == absolute_path
            ),
            None,
        )

    def save(
        self,
        record: InvoiceRecord,
        approved_at: str,
        excel_path: str,
        excel_written: bool,
        archive_path: str = "",
        archived: bool = False,
    ) -> None:
        """Add or replace the saved record for this PDF path."""
        entry = self._entry(record, approved_at, excel_path, excel_written, archive_path, archived)
        records = [
            saved for saved in self._load() if saved["pdf_file_path"] != entry["pdf_file_path"]
        ]
        records.append(entry)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load(self) -> list[dict[str, object]]:
        if not self._path.exists():
            return []
        return [dict(record) for record in json.loads(self._path.read_text(encoding="utf-8"))]

    def _entry(
        self,
        record: InvoiceRecord,
        approved_at: str,
        excel_path: str,
        excel_written: bool,
        archive_path: str,
        archived: bool,
    ) -> dict[str, str | bool]:
        return {
            "plmn": record.plmn.value,
            "invoice_no": record.invoice_no.value,
            "sdr_amount": record.sdr_amount.value,
            "tap_start": record.tap_start.value,
            "tap_end": record.tap_end.value,
            "approved_at": approved_at,
            "pdf_file_path": str(Path(record.file_path).resolve()),
            "excel_path": excel_path,
            "excel_written": excel_written,
            "archive_path": archive_path,
            "archived": archived,
        }
