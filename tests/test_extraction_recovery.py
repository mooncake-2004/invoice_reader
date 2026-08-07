"""Tests for manual recovery when automatic template extraction fails."""

from types import SimpleNamespace

from invoice_reader.application.job_state import InvoiceStatus
from invoice_reader.queue.queue_models import QueueStatus
from invoice_reader.ui.main_window import MainWindow


def test_failed_template_extraction_still_allows_field_reselection() -> None:
    template = SimpleNamespace(
        template_id="ABCDE",
        display_name="ABCDE",
        fields={"invoice_no": object()},
    )
    queue_statuses: list[QueueStatus] = []
    reselections: list[tuple[str, int]] = []
    shown_records = []
    status_messages: list[str] = []
    window = object.__new__(MainWindow)
    window._templates_by_id = {template.template_id: template}
    window._current_template = None
    window._current_pdf_path = "correct-name.pdf"
    window._current_plmn = "ABCDE"
    window._current_session_id = 8
    window._record = None
    window._viewer = SimpleNamespace(
        apply_template_fields=lambda _fields: None,
        start_field_reselection=lambda field_name, session_id: reselections.append(
            (field_name, session_id)
        ),
    )
    window._invoice2data_adapter = SimpleNamespace(
        extract=lambda *_args: (_ for _ in ()).throw(OSError("cannot extract")),
    )
    window._template_editor = SimpleNamespace(
        select_template=lambda _template: None,
        set_status=lambda message: status_messages.append(message),
    )
    window._template_section = SimpleNamespace(set_summary=lambda _summary: None)
    window._queue_status_path = lambda: window._current_pdf_path
    window._set_queue_status = lambda _path, status: queue_statuses.append(status)
    window._show_record = lambda record: shown_records.append(record)
    window._refresh_template_save_action = lambda: None

    assert not MainWindow._apply_template(window, template.template_id)
    MainWindow._start_field_reselection(window, "invoice_no")

    assert window._record is shown_records[-1]
    assert window._record.status == InvoiceStatus.REVIEW_REQUIRED
    assert window._record.plmn.value == "ABCDE"
    assert queue_statuses == [QueueStatus.EXTRACTION_FAILED]
    assert reselections == [("invoice_no", 8)]
    assert "cannot extract" in status_messages[0]
