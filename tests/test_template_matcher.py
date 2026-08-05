"""Tests for required-keyword, page-size, and score-based template matching."""

from invoice_reader.templates.template_matcher import TemplateMatcher
from invoice_reader.templates.template_models import InvoiceTemplate


def _template(
    template_id: str,
    required_keywords: list[str],
    optional_keywords: list[str],
) -> InvoiceTemplate:
    return InvoiceTemplate(
        schema_version=1,
        template_id=template_id,
        display_name=template_id,
        company="Example",
        required_keywords=required_keywords,
        optional_keywords=optional_keywords,
        page_size_points=(595.0, 842.0),
        page_size_tolerance=0.02,
        fields={},
        created_at="2026-08-05T00:00:00+00:00",
        updated_at="2026-08-05T00:00:00+00:00",
        sample_pdf_hash="sample",
    )


def test_matches_template_with_required_keywords_and_page_size() -> None:
    template = _template("one", ["Invoice", "MACHT"], ["SDR", "TAP"])
    matcher = TemplateMatcher(score_threshold=0.5, score_gap=0.2)

    assert matcher.match([template], "INVOICE macHT SDR TAP", (595.0, 842.0)) is template


def test_rejects_template_when_a_required_keyword_is_missing() -> None:
    template = _template("one", ["Invoice", "MACHT"], [])
    matcher = TemplateMatcher(score_threshold=0.5, score_gap=0.2)

    assert matcher.match([template], "Invoice only", (595.0, 842.0)) is None


def test_rejects_ambiguous_top_scores() -> None:
    first = _template("first", ["Invoice"], ["SDR"])
    second = _template("second", ["Invoice"], ["SDR"])
    matcher = TemplateMatcher(score_threshold=0.5, score_gap=0.2)

    assert matcher.match([first, second], "Invoice SDR", (595.0, 842.0)) is None
