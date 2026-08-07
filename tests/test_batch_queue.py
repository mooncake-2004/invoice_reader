"""Tests for batch queue state, scanning, and local persistence."""

from types import SimpleNamespace

from invoice_reader.application.models import ExtractedField, InvoiceRecord
from invoice_reader.excel.excel_service import ExcelService
from invoice_reader.queue.queue_models import BatchQueue, QueueItem, QueueStatus
from invoice_reader.queue.queue_repository import QueueRepository
from invoice_reader.queue.queue_scanner import QueueScanner
from invoice_reader.ui.batch_queue_panel import BatchQueuePanel, queue_statistics
from invoice_reader.ui.main_window import MainWindow


def test_scans_only_sorted_pdf_files_in_selected_directory(tmp_path) -> None:
    (tmp_path / "B.PDF").write_bytes(b"pdf")
    (tmp_path / "a.pdf").write_bytes(b"pdf")
    (tmp_path / "note.txt").write_text("ignore", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "hidden.pdf").write_bytes(b"pdf")

    paths = QueueScanner().scan(str(tmp_path))

    assert [path.rsplit("\\", maxsplit=1)[-1] for path in paths] == ["a.pdf", "B.PDF"]


def test_rescan_retains_completed_status_for_archived_source(tmp_path) -> None:
    pdf_path = str(tmp_path / "completed.pdf")
    queue = BatchQueue(str(tmp_path))
    queue.replace_paths([pdf_path], {})
    queue.set_status(pdf_path, QueueStatus.COMPLETED)

    refreshed = BatchQueue(str(tmp_path))
    refreshed.replace_paths(
        [],
        {pdf_path: QueueItem(pdf_path, QueueStatus.COMPLETED, str(tmp_path / "archive" / "completed.pdf"))},
    )

    assert refreshed.get(pdf_path).status == QueueStatus.COMPLETED
    assert refreshed.get(pdf_path).archive_path == str(tmp_path / "archive" / "completed.pdf")


def test_persists_item_status_and_archive_path_for_the_same_directory(tmp_path) -> None:
    directory = str(tmp_path / "invoices")
    pdf_path = str(tmp_path / "invoices" / "one.pdf")
    queue = BatchQueue(directory)
    queue.replace_paths([pdf_path], {})
    queue.set_status(pdf_path, QueueStatus.SKIPPED)
    queue.set_archive_path(pdf_path, str(tmp_path / "archive" / "one.pdf"))
    queue.set_plmn(pdf_path, "ABCDE")
    repository = QueueRepository(tmp_path / "batch_queue.json")

    repository.save(queue)

    saved_item = repository.load_items(directory)[pdf_path]
    assert saved_item.status == QueueStatus.SKIPPED
    assert saved_item.archive_path == str(tmp_path / "archive" / "one.pdf")
    assert saved_item.plmn == "ABCDE"
    assert repository.load_items(str(tmp_path / "other")) == {}


def test_completed_item_uses_archive_path_when_source_is_missing(tmp_path) -> None:
    archive_path = tmp_path / "archive" / "completed.pdf"
    archive_path.parent.mkdir()
    archive_path.write_bytes(b"pdf")
    item = QueueItem(str(tmp_path / "source" / "completed.pdf"), QueueStatus.COMPLETED, str(archive_path))

    assert MainWindow._queue_item_open_path(object(), item) == str(archive_path)


def test_queue_statistics_keeps_missing_templates_separate_from_extraction_failures() -> None:
    queue = BatchQueue(
        items=[
            QueueItem("no-template.pdf", QueueStatus.NO_TEMPLATE),
            QueueItem("failed.pdf", QueueStatus.EXTRACTION_FAILED),
        ]
    )

    summary = queue_statistics(queue.counts())

    assert "无模板 1" in summary
    assert "提取失败 1" in summary


def test_current_processing_item_remains_visible_when_filter_excludes_it() -> None:
    item = QueueItem("current.pdf", QueueStatus.PROCESSING)
    panel = object.__new__(BatchQueuePanel)
    panel._current_path = item.file_path
    panel._matches_filter = lambda _item: False

    assert BatchQueuePanel._item_is_visible(panel, item)

    panel._current_path = "another.pdf"
    assert not BatchQueuePanel._item_is_visible(panel, item)


def test_queue_item_becomes_current_before_processing_status_is_applied() -> None:
    events: list[tuple[str, object]] = []
    item = QueueItem("invoice.pdf")
    window = object.__new__(MainWindow)
    window._current_queue_path = ""
    window._batch_queue = BatchQueue(items=[item])
    window._queue_panel = SimpleNamespace(
        set_current=lambda path: events.append(("current", path)),
    )
    window._set_queue_status = lambda path, status: events.append(("status", (path, status)))
    window._viewer = SimpleNamespace(open_pdf=lambda path: events.append(("open", path)))

    MainWindow._load_queue_item(window, item, True)

    assert events == [
        ("current", "invoice.pdf"),
        ("status", ("invoice.pdf", QueueStatus.PROCESSING)),
        ("open", "invoice.pdf"),
    ]


def test_switching_away_restores_unapproved_processing_item_to_pending() -> None:
    first = QueueItem("first.pdf", QueueStatus.PROCESSING)
    second = QueueItem("second.pdf", QueueStatus.PENDING)
    queue = BatchQueue(items=[first, second])
    window = object.__new__(MainWindow)
    window._batch_queue = queue
    window._current_queue_path = first.file_path
    window._queue_panel = SimpleNamespace(set_current=lambda _path: None)
    window._viewer = SimpleNamespace(open_pdf=lambda _path: None)
    window._set_queue_status = lambda path, status: queue.set_status(path, status)

    MainWindow._load_queue_item(window, second, True)

    assert first.status == QueueStatus.PENDING
    assert second.status == QueueStatus.PROCESSING


def test_completed_status_is_reconciled_from_current_excel_plmns() -> None:
    in_excel = QueueItem("in-excel.pdf", QueueStatus.PENDING, plmn="ABCDE")
    absent = QueueItem("absent.pdf", QueueStatus.COMPLETED, plmn="FGHIJ")
    skipped = QueueItem("skipped.pdf", QueueStatus.SKIPPED, plmn="KLMNO")
    queue = BatchQueue(items=[in_excel, absent, skipped])

    changed = queue.reconcile_completed({"ABCDE"})

    assert in_excel.status == QueueStatus.COMPLETED
    assert absent.status == QueueStatus.PENDING
    assert skipped.status == QueueStatus.SKIPPED
    assert {item.file_path for item in changed} == {"in-excel.pdf", "absent.pdf"}


def test_next_pending_archived_pdf_uses_its_archive_path(tmp_path) -> None:
    archive_path = tmp_path / "archive" / "completed.pdf"
    archive_path.parent.mkdir()
    archive_path.write_bytes(b"pdf")
    item = QueueItem(str(tmp_path / "missing" / "completed.pdf"), archive_path=str(archive_path))
    opened = []
    window = object.__new__(MainWindow)
    window._batch_queue = BatchQueue(items=[item])
    window._load_queue_item = lambda queue_item, mark_processing, open_path: opened.append(
        (queue_item, mark_processing, open_path)
    )

    MainWindow._load_next_pending_item(window)

    assert opened == [(item, True, str(archive_path))]


def test_switching_excel_reconciles_queue_from_its_plmn_column(tmp_path) -> None:
    populated_excel = tmp_path / "2026-08.xlsx"
    empty_excel = tmp_path / "2026-09.xlsx"
    excel_service = ExcelService()
    excel_service.create_monthly_workbook(str(populated_excel))
    excel_service.create_monthly_workbook(str(empty_excel))
    record = InvoiceRecord(
        file_path="ABCDE.pdf",
        plmn=ExtractedField(value="ABCDE"),
        invoice_no=ExtractedField(value="INV-1"),
        sdr_amount=ExtractedField(value="1.23"),
        tap_start=ExtractedField(value="10"),
        tap_end=ExtractedField(value="20"),
    )
    excel_service.write_record(str(populated_excel), record, "2026-08-07T10:00:00+08:00")

    item = QueueItem("ABCDE.pdf", QueueStatus.PENDING, plmn="ABCDE")
    saved_paths = []
    updated_statuses = []
    window = object.__new__(MainWindow)
    window._batch_queue = BatchQueue("C:/invoices", [item])
    window._excel_service = excel_service
    window._settings_repository = SimpleNamespace(save_excel_path=lambda path: saved_paths.append(path))
    window._excel_panel = SimpleNamespace(set_excel_path=lambda _path: None)
    window._excel_section = SimpleNamespace(set_summary=lambda _summary: None)
    window._queue_repository = SimpleNamespace(save=lambda _queue: None)
    window._queue_panel = SimpleNamespace(update_item=lambda changed: updated_statuses.append(changed.status))

    MainWindow._set_excel_path(window, str(populated_excel))
    assert item.status == QueueStatus.COMPLETED

    MainWindow._set_excel_path(window, str(empty_excel))
    assert item.status == QueueStatus.PENDING
    assert saved_paths == [str(populated_excel), str(empty_excel)]
    assert updated_statuses == [QueueStatus.COMPLETED, QueueStatus.PENDING]


def test_processing_states_cannot_override_excel_completed_status() -> None:
    item = QueueItem("ABCDE.pdf", QueueStatus.COMPLETED, plmn="ABCDE")
    queue = BatchQueue("C:/invoices", [item])
    window = object.__new__(MainWindow)
    window._batch_queue = queue
    window._queue_repository = SimpleNamespace(save=lambda _queue: None)
    window._queue_panel = SimpleNamespace(update_item=lambda _item: None)

    MainWindow._set_queue_status(window, item.file_path, QueueStatus.NO_TEMPLATE)

    assert item.status == QueueStatus.COMPLETED


def test_manual_plmn_immediately_uses_current_excel_status() -> None:
    item = QueueItem("unparsed.pdf", QueueStatus.PROCESSING)
    queue = BatchQueue("C:/invoices", [item])
    updated_statuses = []
    window = object.__new__(MainWindow)
    window._batch_queue = queue
    window._excel_path = "monthly.xlsx"
    window._excel_service = SimpleNamespace(read_plmns=lambda _path: {"ABCDE"})
    window._queue_repository = SimpleNamespace(save=lambda _queue: None)
    window._queue_panel = SimpleNamespace(update_item=lambda changed: updated_statuses.append(changed.status))

    MainWindow._set_queue_plmn(window, item.file_path, "ABCDE")

    assert item.plmn == "ABCDE"
    assert item.status == QueueStatus.COMPLETED
    assert updated_statuses == [QueueStatus.COMPLETED]
