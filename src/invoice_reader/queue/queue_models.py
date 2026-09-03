"""Data objects for a non-recursive PDF processing queue."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from invoice_reader.i18n import t


class QueueStatus(StrEnum):
    """The processing state displayed for each queued PDF."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    NO_TEMPLATE = "no_template"
    EXTRACTION_FAILED = "extraction_failed"
    SKIPPED = "skipped"


STATUS_LABELS = {
    QueueStatus.PENDING: t("status.pending"),
    QueueStatus.PROCESSING: t("status.processing"),
    QueueStatus.COMPLETED: t("status.completed"),
    QueueStatus.NO_TEMPLATE: t("status.no_template"),
    QueueStatus.EXTRACTION_FAILED: t("status.extraction_failed"),
    QueueStatus.SKIPPED: t("status.skipped"),
}


@dataclass
class QueueItem:
    """One PDF discovered directly under the selected queue directory."""

    file_path: str
    status: QueueStatus = QueueStatus.PENDING
    archive_path: str = ""
    plmn: str = ""

    @property
    def filename(self) -> str:
        """Return the queue-friendly filename."""
        return Path(self.archive_path or self.file_path).name


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

    def replace_paths(self, paths: list[str], saved_items: dict[str, QueueItem]) -> None:
        """Refresh the directory while retaining completed and skipped queue items."""
        retained_paths = {
            path
            for path, item in saved_items.items()
            if item.status in (QueueStatus.COMPLETED, QueueStatus.SKIPPED)
        }
        self._items = {
            path: QueueItem(
                path,
                saved_items.get(path, QueueItem(path)).status,
                saved_items.get(path, QueueItem(path)).archive_path,
                saved_items.get(path, QueueItem(path)).plmn,
            )
            for path in set(paths) | retained_paths
        }

    def set_status(self, file_path: str, status: QueueStatus) -> QueueItem:
        """Set and return a queued item's new state."""
        item = self._items[file_path]
        item.status = status
        return item

    def set_archive_path(self, file_path: str, archive_path: str) -> QueueItem:
        """Save the completed PDF location without changing its queue identity."""
        item = self._items[file_path]
        item.archive_path = archive_path
        return item

    def set_plmn(self, file_path: str, plmn: str) -> QueueItem:
        """Associate the queue identity with its parsed or manually supplied PLMN."""
        item = self._items[file_path]
        item.plmn = plmn
        return item

    def rename_disk_path(self, queue_path: str, old_disk_path: str, new_disk_path: str) -> QueueItem:
        """Update the queue identity after its source or archived PDF is renamed."""
        item = self._items.pop(queue_path)
        if item.file_path == old_disk_path:
            item.file_path = new_disk_path
        elif item.archive_path == old_disk_path:
            item.archive_path = new_disk_path
        else:
            self._items[queue_path] = item
            raise ValueError("重命名的 PDF 路径与当前队列项目不一致。")
        self._items[item.file_path] = item
        return item

    def merge_renamed_paths(self, scanned_paths: set[str]) -> None:
        """Merge a retained old-name item into its uniquely matching scanned PLMN."""
        scanned_by_plmn: dict[str, list[QueueItem]] = {}
        for path in scanned_paths:
            item = self._items.get(path)
            if item is not None and item.plmn:
                scanned_by_plmn.setdefault(item.plmn, []).append(item)
        for old_path, old_item in list(self._items.items()):
            matches = scanned_by_plmn.get(old_item.plmn, [])
            if old_path in scanned_paths or len(matches) != 1:
                continue
            scanned_item = matches[0]
            scanned_item.status = old_item.status
            del self._items[old_path]

    def reconcile_completed(self, completed_plmns: set[str]) -> list[QueueItem]:
        """Make completed status reflect only PLMNs found in the current Excel file."""
        changed_items: list[QueueItem] = []
        for item in self._items.values():
            target_status = self._reconciled_status(item, completed_plmns)
            if target_status != item.status:
                item.status = target_status
                changed_items.append(item)
        return changed_items

    def _reconciled_status(self, item: QueueItem, completed_plmns: set[str]) -> QueueStatus:
        if item.plmn and item.plmn in completed_plmns:
            return QueueStatus.COMPLETED
        if item.status == QueueStatus.COMPLETED:
            return QueueStatus.PENDING
        return item.status

    def get(self, file_path: str) -> QueueItem | None:
        """Return one queued item by its absolute path."""
        return self._items.get(file_path)

    def next_pending(self) -> QueueItem | None:
        """Return the first pending item in filename order."""
        return next(iter(self.items(QueueStatus.PENDING)), None)

    def counts(self) -> dict[QueueStatus, int]:
        """Return current item counts for the queue statistics display."""
        return {status: sum(item.status == status for item in self._items.values()) for status in QueueStatus}
