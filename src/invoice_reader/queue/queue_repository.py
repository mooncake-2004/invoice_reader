"""JSON persistence for the currently selected batch queue."""

import json
from pathlib import Path

from invoice_reader.infrastructure.app_paths import batch_queue_path
from invoice_reader.queue.queue_models import BatchQueue, QueueStatus


class QueueRepository:
    """Store queue state locally, never beside server-side source PDFs."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = batch_queue_path() if path is None else path

    def load_statuses(self, directory: str) -> dict[str, QueueStatus]:
        """Return saved statuses only when they belong to the selected directory."""
        saved = self._load()
        if saved.get("directory") != directory:
            return {}
        return {
            file_path: QueueStatus(status)
            for file_path, status in dict(saved.get("statuses", {})).items()
        }

    def save(self, queue: BatchQueue) -> None:
        """Persist the selected directory and every currently discovered item state."""
        payload = {
            "directory": queue.directory,
            "statuses": {item.file_path: item.status.value for item in queue.items()},
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load(self) -> dict[str, object]:
        if not self._path.exists():
            return {}
        return dict(json.loads(self._path.read_text(encoding="utf-8")))
