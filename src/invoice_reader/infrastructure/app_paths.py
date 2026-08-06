"""Paths for local Windows application data."""

import os
from pathlib import Path
import sys


def settings_path() -> Path:
    """Return the local settings file path for this application."""
    return Path(os.environ["LOCALAPPDATA"]) / "InvoiceReader" / "settings.json"


def templates_directory() -> Path:
    """Return the local-only template directory for this application."""
    return Path(os.environ["LOCALAPPDATA"]) / "InvoiceReader" / "templates"


def approval_records_path() -> Path:
    """Return the local approval-record file path for this application."""
    return Path(os.environ["LOCALAPPDATA"]) / "InvoiceReader" / "approval_records.json"


def resource_path(relative_path: str) -> Path:
    """Return a bundled resource path for source runs and PyInstaller builds."""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[3]))
    return base_path / relative_path
