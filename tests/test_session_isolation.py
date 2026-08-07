"""Tests that delayed PDF callbacks cannot cross document sessions."""

from types import SimpleNamespace

from invoice_reader.application.models import ExtractedField, FieldSource, InvoiceRecord
from invoice_reader.templates.template_models import create_template_field
from invoice_reader.ui.main_window import MainWindow
from invoice_reader.ui.pdf_viewer import PdfViewer, ReselectionRequest


def test_reselection_request_requires_the_current_viewer_session() -> None:
    viewer = object.__new__(PdfViewer)
    viewer._session_id = 4
    viewer._active_field = "invoice_no"
    viewer._reselection_request = None

    PdfViewer.start_field_reselection(viewer, "invoice_no", 3)

    assert viewer._reselection_request is None
    PdfViewer.start_field_reselection(viewer, "invoice_no", 4)
    assert viewer._reselection_request == ReselectionRequest(4, "invoice_no")


def test_template_application_keeps_the_current_reselection_request() -> None:
    request = ReselectionRequest(4, "invoice_no")
    viewer = object.__new__(PdfViewer)
    viewer._field_locations = {}
    viewer._field_texts = {"invoice_no": "old"}
    viewer._selected_field = "invoice_no"
    viewer._reselection_request = request
    viewer._service = SimpleNamespace(page_count=0)

    PdfViewer.apply_template_fields(viewer, {"invoice_no": create_template_field("invoice_no", 1, (0.1, 0.2, 0.3, 0.4))})

    assert viewer._reselection_request is request


def test_stale_field_reselection_callback_does_not_extract_or_write() -> None:
    window = object.__new__(MainWindow)
    window._current_session_id = 4
    window._record = object()
    window._invoice2data_adapter = SimpleNamespace(
        extract_field=lambda *_args: (_ for _ in ()).throw(AssertionError("stale callback extracted"))
    )

    MainWindow._field_reselected(
        window,
        3,
        "invoice_no",
        create_template_field("invoice_no", 1, (0.1, 0.2, 0.3, 0.4)),
    )


def test_current_field_reselection_writes_the_replacement_value() -> None:
    record = InvoiceRecord(file_path="current.pdf")
    window = object.__new__(MainWindow)
    window._current_session_id = 4
    window._current_pdf_path = "current.pdf"
    window._current_plmn = "ABCDE"
    window._record = record
    window._invoice2data_adapter = SimpleNamespace(
        extract_field=lambda *_args: ExtractedField(value="replacement")
    )
    window._show_record = lambda _record: None
    window._refresh_template_save_action = lambda: None
    window._viewer = SimpleNamespace(highlight_field=lambda _name: None)
    window._template_editor = SimpleNamespace(set_status=lambda _message: None)

    MainWindow._field_reselected(
        window,
        4,
        "invoice_no",
        create_template_field("invoice_no", 1, (0.1, 0.2, 0.3, 0.4)),
    )

    assert record.invoice_no.value == "replacement"
    assert record.invoice_no.source == FieldSource.MANUAL_SELECTION
