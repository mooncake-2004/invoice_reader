"""Paths for local Windows application data."""

import os
from pathlib import Path


def settings_path() -> Path:
    """Return the local settings file path for this application."""
    return Path(os.environ["LOCALAPPDATA"]) / "InvoiceReader" / "settings.json"
