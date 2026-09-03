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
        return [str(pattern) for pattern in self._load().get("filename_patterns", [])]

    def save_filename_patterns(self, patterns: list[str]) -> None:
        """Save the ordered PLMN filename pattern list."""
        settings = self._load()
        settings["filename_patterns"] = patterns
        self._save(settings)

    def load_excel_path(self) -> str:
        """Load the last selected monthly Excel path."""
        return str(self._load().get("excel_path", ""))

    def save_excel_path(self, excel_path: str) -> None:
        """Save the current monthly Excel path without changing other settings."""
        settings = self._load()
        settings["excel_path"] = excel_path
        self._save(settings)

    def load_archive_directory(self) -> str:
        """Load the last selected PDF archive directory."""
        return str(self._load().get("archive_directory", ""))

    def save_archive_directory(self, archive_directory: str) -> None:
        """Save the PDF archive directory without changing other settings."""
        settings = self._load()
        settings["archive_directory"] = archive_directory
        self._save(settings)

    def load_language(self) -> str:
        """Load the saved UI language, defaulting to Chinese."""
        return str(self._load().get("language", "zh"))

    def save_language(self, language: str) -> None:
        """Save the UI language without changing other settings."""
        settings = self._load()
        settings["language"] = language
        self._save(settings)

    def _load(self) -> dict[str, object]:
        if not self._path.exists():
            return {}
        with self._path.open(encoding="utf-8") as file:
            return dict(json.load(file))

    def _save(self, settings: dict[str, object]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as file:
            json.dump(settings, file, ensure_ascii=False, indent=2)
