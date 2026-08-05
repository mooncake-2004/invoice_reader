"""Tests for PLMN-based template matching and page-size warnings."""

from invoice_reader.templates.template_matcher import TemplateMatcher
from invoice_reader.templates.template_models import InvoiceTemplate


def _template(plmn: str, page_size_points: tuple[float, float] = (595.0, 842.0)) -> InvoiceTemplate:
    return InvoiceTemplate(
        schema_version=1,
        template_id=plmn,
        display_name="Example",
        company="Company",
        plmn=plmn,
        required_keywords=["remark"],
        optional_keywords=["remark"],
        page_size_points=page_size_points,
        page_size_tolerance=0.02,
        fields={},
        created_at="2026-08-05T00:00:00+00:00",
        updated_at="2026-08-05T00:00:00+00:00",
        sample_pdf_hash="sample",
    )


def test_matches_template_by_plmn_without_using_keywords() -> None:
    template = _template("ABCDE")

    assert TemplateMatcher().match([template], "ABCDE") is template


def test_returns_none_for_unknown_plmn() -> None:
    template = _template("ABCDE")

    assert TemplateMatcher().match([template], "ZZZZZ") is None


def test_flags_large_page_size_difference_as_a_soft_warning() -> None:
    template = _template("ABCDE")

    assert TemplateMatcher().page_size_differs(template, (700.0, 842.0))
