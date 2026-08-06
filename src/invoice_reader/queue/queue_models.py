"""Data objects for a non-recursive PDF processing queue."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class QueueStatus(StrEnum):
    """The processing state displayed for each queued PDF."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    NO_TEMPLATE = "no_template"
    EXTRACTION_FAILED = "extraction_failed"
    SKIPPED = "skipped"


STATUS_LABELS = {
    QueueStatus.PENDING: "待处理",
    QueueStatus.PROCESSING: "处理中",
    QueueStatus.COMPLETED: "已完成",
    QueueStatus.NO_TEMPLATE: "无模板",
    QueueStatus.EXTRACTION_FAILED: "提取失败",
    QueueStatus.SKIPPED: "已跳过",
}


@dataclass
class QueueItem:
    """One PDF discovered directly under the selected queue directory."""

    file_path: str
    status: QueueStatus = QueueStatus.PENDING

    @property
    def filename(self) -> str:
        """Return the queue-friendly filename."""
        return Path(self.file_path).name


class BatchQueue:
    """Own the sorted items and state transitions for one selected directory."""

    def __init__(self, directory: str = "", items: list[QueueItem] | None = None) -> None:
        self.directory = directory
        self._items = {item.file_path: item for item in items or []}

    def items(self, status: QueueStatus | None = None) -> list[QueueItem]:
        """Return sorted queue items, optionally filtered by one status."""
        entries = self._items.values()
        if status is not None:
            entries = (item for item in entries if item.status == status)
        return sorted(entries, key=lambda item: item.filename.casefold())

    def replace_paths(self, paths: list[str], saved_statuses: dict[str, QueueStatus]) -> None:
        """Refresh the physical directory while retaining stored statuses by path."""
        retained_paths = {
            path
            for path, status in saved_statuses.items()
            if status in (QueueStatus.COMPLETED, QueueStatus.SKIPPED)
        }
        self._items = {
            path: QueueItem(path, saved_statuses.get(path, QueueStatus.PENDING))
            for path in set(paths) | retained_paths
        }

    def set_status(self, file_path: str, status: QueueStatus) -> QueueItem:
        """Set and return a queued item's new state."""
        item = self._items[file_path]
        item.status = status
        return item

    def get(self, file_path: str) -> QueueItem | None:
        """Return one queued item by its absolute path."""
        return self._items.get(file_path)

    def next_pending(self) -> QueueItem | None:
        """Return the first pending item in filename order."""
        return next(iter(self.items(QueueStatus.PENDING)), None)

    def counts(self) -> dict[QueueStatus, int]:
        """Return current item counts for the queue statistics display."""
        return {status: sum(item.status == status for item in self._items.values()) for status in QueueStatus}
