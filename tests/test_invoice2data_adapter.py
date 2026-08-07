"""Tests for structured PDFium area extraction through invoice2data."""

import fitz

from invoice_reader.application.job_state import InvoiceStatus
from invoice_reader.application.models import FieldSource, ValidationStatus
from invoice_reader.extraction.invoice2data_adapter import Invoice2DataAdapter
from invoice_reader.templates.template_compiler import TemplateCompiler
from invoice_reader.templates.template_models import FIELD_NAMES, InvoiceTemplate, create_template_field


def _template() -> InvoiceTemplate:
    fields = {
        "invoice_no": create_template_field("invoice_no", 1, (0.05, 0.05, 0.45, 0.15)),
        "sdr_amount": create_template_field("sdr_amount", 1, (0.05, 0.20, 0.45, 0.30)),
        "tap_start": create_template_field("tap_start", 1, (0.05, 0.35, 0.45, 0.45)),
        "tap_end": create_template_field("tap_end", 1, (0.05, 0.50, 0.45, 0.60)),
    }
    return InvoiceTemplate(
        schema_version=1,
        template_id="ABCDE",
        display_name="ABCDE",
        company="ABCDE",
        plmn="ABCDE",
        required_keywords=[],
        optional_keywords=[],
        page_size_points=(600.0, 800.0),
        page_size_tolerance=0.02,
        fields=fields,
        created_at="2026-08-06T00:00:00+00:00",
        updated_at="2026-08-06T00:00:00+00:00",
        sample_pdf_hash="sample",
    )


def _pdf(path: str, sdr_amount: str = "321.45") -> None:
    document = fitz.open()
    page = document.new_page(width=600, height=800)
    page.insert_text((50, 80), "INV-1001")
    page.insert_text((50, 200), sdr_amount)
    page.insert_text((50, 320), "100")
    page.insert_text((50, 440), "200")
    document.save(path)
    document.close()


def test_extracts_template_fields_into_invoice_record(tmp_path) -> None:
    pdf_path = tmp_path / "ABCDE_invoice.pdf"
    _pdf(str(pdf_path))

    record = Invoice2DataAdapter(TemplateCompiler(0.02)).extract(
        str(pdf_path),
        _template(),
        "ABCDE",
    )

    assert record.status == InvoiceStatus.EXTRACTED
    assert record.plmn.value == "ABCDE"
    assert record.invoice_no.value == "INV-1001"
    assert record.sdr_amount.value == "321.45"
    assert record.tap_start.value == "100"
    assert record.tap_end.value == "200"
    for field_name in FIELD_NAMES:
        field = getattr(record, field_name)
        assert field.source == FieldSource.TEXT
        assert field.validation_status == ValidationStatus.VALID
        assert field.confidence == 1.0


def test_marks_an_empty_field_without_failing(tmp_path) -> None:
    pdf_path = tmp_path / "ABCDE_invoice.pdf"
    _pdf(str(pdf_path))
    template = _template()
    template.fields["tap_end"] = create_template_field("tap_end", 1, (0.50, 0.50, 0.80, 0.60))

    record = Invoice2DataAdapter(TemplateCompiler(0.02)).extract(
        str(pdf_path),
        template,
        "ABCDE",
    )

    assert record.tap_end.value == ""
    assert record.tap_end.validation_status == ValidationStatus.INVALID
    assert record.tap_end.confidence == 0.0


def test_extracts_one_current_invoice_field_without_changing_template(tmp_path) -> None:
    pdf_path = tmp_path / "ABCDE_invoice.pdf"
    _pdf(str(pdf_path))
    template = _template()
    replacement = create_template_field("tap_end", 1, (0.05, 0.48, 0.45, 0.60))

    field = Invoice2DataAdapter(TemplateCompiler(0.02)).extract_field(
        str(pdf_path),
        "ABCDE",
        "tap_end",
        replacement,
    )

    assert field.value == "200"
    assert field.source == FieldSource.TEXT
    assert template.fields["tap_end"].bbox_normalized == (0.05, 0.50, 0.45, 0.60)


def test_normalizes_decimal_comma_for_approval_and_preserves_original(tmp_path) -> None:
    pdf_path = tmp_path / "ABCDE_invoice.pdf"
    _pdf(str(pdf_path), "0,23")

    record = Invoice2DataAdapter(TemplateCompiler(0.02)).extract(
        str(pdf_path),
        _template(),
        "ABCDE",
    )

    assert record.sdr_amount.value == "0.23"
    assert record.sdr_amount.original_value == "0,23"
    assert record.sdr_amount.validation_status == ValidationStatus.VALID
