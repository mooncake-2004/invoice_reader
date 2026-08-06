"""Tests for batch queue state, scanning, and local persistence."""

from invoice_reader.queue.queue_models import BatchQueue, QueueStatus
from invoice_reader.queue.queue_repository import QueueRepository
from invoice_reader.queue.queue_scanner import QueueScanner


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
    refreshed.replace_paths([], {pdf_path: QueueStatus.COMPLETED})

    assert refreshed.get(pdf_path).status == QueueStatus.COMPLETED


def test_persists_statuses_for_the_same_selected_directory(tmp_path) -> None:
    directory = str(tmp_path / "invoices")
    pdf_path = str(tmp_path / "invoices" / "one.pdf")
    queue = BatchQueue(directory)
    queue.replace_paths([pdf_path], {})
    queue.set_status(pdf_path, QueueStatus.SKIPPED)
    repository = QueueRepository(tmp_path / "batch_queue.json")

    repository.save(queue)

    assert repository.load_statuses(directory) == {pdf_path: QueueStatus.SKIPPED}
    assert repository.load_statuses(str(tmp_path / "other")) == {}
