"""Extract template field values through invoice2data's PDFium backend."""

from datetime import datetime, timezone

import fitz
from invoice2data import extract_data
from invoice2data.extract.invoice_template import InvoiceTemplate as Invoice2DataTemplate
from invoice2data.input import pdfium

from invoice_reader.application.models import (
    ExtractedField,
    FieldSource,
    InvoiceRecord,
    ValidationStatus,
)
from invoice_reader.application.job_state import InvoiceStatus
from invoice_reader.templates.template_compiler import TemplateCompiler
from invoice_reader.templates.template_models import InvoiceTemplate, TemplateField


class Invoice2DataAdapter:
    """Adapt one PLMN-selected local template to an InvoiceRecord."""

    def __init__(self, template_compiler: TemplateCompiler) -> None:
        self._template_compiler = template_compiler

    def extract(self, pdf_path: str, template: InvoiceTemplate, plmn: str) -> InvoiceRecord:
        """Extract the four selected fields from one electronic PDF."""
        result = self._extract_result(pdf_path, template)
        return InvoiceRecord(
            file_path=pdf_path,
            plmn=self._plmn_field(plmn),
            invoice_no=self._result_field(result, "invoice_no"),
            sdr_amount=self._result_field(result, "sdr_amount"),
            tap_start=self._result_field(result, "tap_start"),
            tap_end=self._result_field(result, "tap_end"),
            status=InvoiceStatus.EXTRACTED,
        )

    def extract_field(
        self,
        pdf_path: str,
        plmn: str,
        field_name: str,
        field: TemplateField,
    ) -> ExtractedField:
        """Extract one current-invoice field without modifying the template."""
        result = self._extract_result(pdf_path, self._single_field_template(plmn, field_name, field))
        return self._result_field(result, field_name)

    def _single_field_template(
        self,
        plmn: str,
        field_name: str,
        field: TemplateField,
    ) -> InvoiceTemplate:
        """Build the temporary extraction rule used by one-off field selection."""
        now = datetime.now(timezone.utc).isoformat()
        return InvoiceTemplate(
            schema_version=1,
            template_id="current-invoice-field",
            display_name=plmn,
            company=plmn,
            plmn=plmn,
            required_keywords=[],
            optional_keywords=[],
            page_size_points=(0.0, 0.0),
            page_size_tolerance=0.0,
            fields={field_name: field},
            created_at=now,
            updated_at=now,
            sample_pdf_hash="",
        )

    def _extract_result(self, pdf_path: str, template: InvoiceTemplate) -> dict[str, object]:
        page_sizes = self._page_sizes(pdf_path, template)
        compiled_template = Invoice2DataTemplate(
            self._template_compiler.compile_invoice2data_template(template, page_sizes)
        )
        return extract_data(
            pdf_path,
            templates=[compiled_template],
            input_module=pdfium,
            raise_on_error=False,
        )

    def _page_sizes(
        self,
        pdf_path: str,
        template: InvoiceTemplate,
    ) -> dict[int, tuple[float, float]]:
        document = fitz.open(pdf_path)
        try:
            return {
                field.page_number: (
                    document.load_page(field.page_number - 1).rect.width,
                    document.load_page(field.page_number - 1).rect.height,
                )
                for field in template.fields.values()
            }
        finally:
            document.close()

    def _plmn_field(self, plmn: str) -> ExtractedField:
        return ExtractedField(
            value=plmn,
            original_value=plmn,
            source=FieldSource.TEXT,
            validation_status=ValidationStatus.VALID if plmn else ValidationStatus.INVALID,
            confidence=1.0 if plmn else 0.0,
        )

    def _result_field(self, result: dict[str, object], field_name: str) -> ExtractedField:
        value = str(result.get(field_name, "")).strip()
        return ExtractedField(
            value=value,
            original_value=value,
            source=FieldSource.TEXT,
            validation_status=ValidationStatus.VALID if value else ValidationStatus.INVALID,
            confidence=1.0 if value else 0.0,
        )
