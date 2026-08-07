"""Tests for batch queue state, scanning, and local persistence."""

from types import SimpleNamespace

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
    repository = QueueRepository(tmp_path / "batch_queue.json")

    repository.save(queue)

    saved_item = repository.load_items(directory)[pdf_path]
    assert saved_item.status == QueueStatus.SKIPPED
    assert saved_item.archive_path == str(tmp_path / "archive" / "one.pdf")
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
