"""JSON persistence for the currently selected batch queue."""

import json
from pathlib import Path

from invoice_reader.infrastructure.app_paths import batch_queue_path
from invoice_reader.queue.queue_models import BatchQueue, QueueItem, QueueStatus


class QueueRepository:
    """Store queue state locally, never beside server-side source PDFs."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = batch_queue_path() if path is None else path

    def load_items(self, directory: str) -> dict[str, QueueItem]:
        """Return saved queue items only when they belong to the selected directory."""
        saved = self._load()
        if saved.get("directory") != directory:
            return {}
        return self._saved_items(saved)

    def save(self, queue: BatchQueue) -> None:
        """Persist the selected directory and every queue item state locally."""
        payload = {
            "directory": queue.directory,
            "items": {
                item.file_path: {
                    "status": item.status.value,
                    "archive_path": item.archive_path,
                }
                for item in queue.items()
            },
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load(self) -> dict[str, object]:
        if not self._path.exists():
            return {}
        return dict(json.loads(self._path.read_text(encoding="utf-8")))

    def _saved_items(self, saved: dict[str, object]) -> dict[str, QueueItem]:
        """Read the current item format, accepting the prior status-only file once."""
        item_data = saved.get("items")
        if isinstance(item_data, dict):
            return {
                str(file_path): QueueItem(
                    str(file_path),
                    QueueStatus(str(values["status"])),
                    str(values.get("archive_path", "")),
                )
                for file_path, values in item_data.items()
                if isinstance(values, dict)
            }
        return {
            str(file_path): QueueItem(str(file_path), QueueStatus(str(status)))
            for file_path, status in dict(saved.get("statuses", {})).items()
        }
