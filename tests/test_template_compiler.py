"""Tests for PLMN stored in a newly compiled template."""

from invoice_reader.templates.template_compiler import TemplateCompiler
from invoice_reader.templates.template_models import FIELD_NAMES, InvoiceTemplate, create_template_field


def test_records_plmn_in_template() -> None:
    fields = {
        field_name: create_template_field(field_name, 1, (0.1, 0.2, 0.3, 0.4))
        for field_name in FIELD_NAMES
    }

    template = TemplateCompiler(0.02).compile(
        "Example",
        "Company",
        "ABCDE",
        [],
        [],
        fields,
        (595.0, 842.0),
        "sample-hash",
    )

    assert template.plmn == "ABCDE"


def test_compiles_normalized_box_to_pdfium_area() -> None:
    field = create_template_field("invoice_no", 1, (0.1, 0.2, 0.5, 0.6))
    template = InvoiceTemplate(
        schema_version=1,
        template_id="ABCDE",
        display_name="ABCDE",
        company="ABCDE",
        plmn="ABCDE",
        required_keywords=[],
        optional_keywords=[],
        page_size_points=(600.0, 800.0),
        page_size_tolerance=0.02,
        fields={"invoice_no": field},
        created_at="2026-08-06T00:00:00+00:00",
        updated_at="2026-08-06T00:00:00+00:00",
        sample_pdf_hash="sample",
    )

    compiled = TemplateCompiler(0.02).compile_invoice2data_template(
        template,
        {1: (600.0, 800.0)},
    )

    assert compiled["fields"]["invoice_no"]["area"] == {
        "f": 1,
        "l": 1,
        "r": 72,
        "x": 60.0,
        "y": 160.0,
        "W": 240.0,
        "H": 320.0,
    }
