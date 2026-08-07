"""Tests that delayed PDF callbacks cannot cross document sessions."""

from types import SimpleNamespace

from invoice_reader.application.models import ExtractedField, FieldSource, InvoiceRecord
from invoice_reader.queue.queue_models import BatchQueue, QueueItem
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


def test_apply_template_keeps_reselect_state() -> None:
    request = ReselectionRequest(4, "invoice_no")
    viewer = object.__new__(PdfViewer)
    viewer._field_locations = {}
    viewer._field_texts = {"invoice_no": "old"}
    viewer._selected_field = "invoice_no"
    viewer._reselection_request = request
    viewer._service = SimpleNamespace(page_count=0)

    PdfViewer.apply_template_fields(viewer, {"invoice_no": create_template_field("invoice_no", 1, (0.1, 0.2, 0.3, 0.4))})

    assert viewer._reselection_request is request


def test_stale_reselect_ignored() -> None:
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


def test_field_reselect_fills_value() -> None:
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


def test_no_plmn_dialog_then_reselect(monkeypatch) -> None:
    reselections: list[tuple[str, int]] = []
    window = object.__new__(MainWindow)
    window._current_session_id = 7
    window._current_pdf_path = "unparsed.pdf"
    window._current_plmn = ""
    window._record = None
    window.winfo_toplevel = lambda: object()
    window._continue_with_plmn = lambda _service, plmn, _session_id: (
        setattr(window, "_current_plmn", plmn),
        setattr(window, "_record", InvoiceRecord(file_path=window._current_pdf_path)),
    )
    window._viewer = SimpleNamespace(
        start_field_reselection=lambda field_name, session_id: reselections.append(
            (field_name, session_id)
        ),
    )
    window._template_editor = SimpleNamespace(set_status=lambda _message: None)
    monkeypatch.setattr("invoice_reader.ui.main_window.simpledialog.askstring", lambda *_args, **_kwargs: "ABCDE")

    MainWindow._handle_unparsed_plmn_action(window, object(), object(), 7, "manual")
    MainWindow._start_field_reselection(window, "invoice_no")

    assert window._current_plmn == "ABCDE"
    assert reselections == [("invoice_no", 7)]


def test_skip_then_reopen_can_reselect() -> None:
    item = QueueItem("skipped.pdf")
    queue = BatchQueue(items=[item])
    reselections: list[tuple[str, int]] = []
    window = object.__new__(MainWindow)
    window._batch_queue = queue
    window._current_queue_path = item.file_path
    window._current_session_id = 1
    window._record = InvoiceRecord(file_path=item.file_path)
    window._queue_panel = SimpleNamespace(set_current=lambda _path: None)
    window._template_editor = SimpleNamespace(set_status=lambda _message: None)
    window._set_queue_status = lambda path, status: queue.set_status(path, status)
    window._load_next_pending_item = lambda: None

    def open_pdf(path: str) -> None:
        window._current_session_id += 1
        window._record = InvoiceRecord(file_path=path)

    window._viewer = SimpleNamespace(
        close_current_pdf=lambda: None,
        open_pdf=open_pdf,
        start_field_reselection=lambda field_name, session_id: reselections.append(
            (field_name, session_id)
        ),
    )

    MainWindow._skip_current_queue_item(window)
    MainWindow._load_queue_item(window, item, True)
    MainWindow._start_field_reselection(window, "invoice_no")

    assert reselections == [("invoice_no", 2)]
