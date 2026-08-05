"""Persistence for small user settings."""

import json
from pathlib import Path

from invoice_reader.infrastructure.app_paths import settings_path


class SettingsRepository:
    """Read and save configured PLMN filename patterns."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = settings_path() if path is None else path

    def load_filename_patterns(self) -> list[str]:
        """Load the saved pattern list, or an empty list before first save."""
        if not self._path.exists():
            return []
        with self._path.open(encoding="utf-8") as file:
            return json.load(file)["filename_patterns"]

    def save_filename_patterns(self, patterns: list[str]) -> None:
        """Save the ordered PLMN filename pattern list."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as file:
            json.dump({"filename_patterns": patterns}, file, ensure_ascii=False, indent=2)
