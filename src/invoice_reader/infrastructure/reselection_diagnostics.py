"""Temporary, narrowly scoped diagnostics for field reselection."""

import logging
import os
from pathlib import Path


_LOGGER = logging.getLogger("invoice_reader.reselection")


def log_reselection(message: str, *arguments: object) -> None:
    """Append one field-reselection diagnostic event to the local debug log."""
    if not _LOGGER.handlers:
        log_path = Path(os.environ["LOCALAPPDATA"]) / "InvoiceReader" / "debug.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        _LOGGER.addHandler(handler)
        _LOGGER.setLevel(logging.DEBUG)
        _LOGGER.propagate = False
    _LOGGER.debug(message, *arguments)
