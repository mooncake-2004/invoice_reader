"""Controls for the local PDF archive directory."""

from collections.abc import Callable
import tkinter as tk
from tkinter import ttk

from invoice_reader.i18n import t


class ArchivePanel(ttk.LabelFrame):
    """Show and update the directory used after a successful Excel write."""

    def __init__(self, master: tk.Misc, archive_directory: str, on_select: Callable[[], None]) -> None:
        super().__init__(master, text=t("section.archive"), padding=8)
        self._archive_directory = archive_directory
        self._path = tk.StringVar()
        self._select_button = ttk.Button(self, command=on_select)
        self._select_button.pack(side="left")
        ttk.Label(self, textvariable=self._path, wraplength=900).pack(side="left", padx=(12, 0))
        self.retranslate()

    def retranslate(self) -> None:
        """Refresh archive controls and the empty-state text in the current language."""
        if self.cget("text"):
            self.configure(text=t("section.archive"))
        self._select_button.configure(text=t("btn.select_archive_directory"))
        self._path.set(self._archive_directory or t("status.no_archive_directory_long"))

    def set_archive_directory(self, archive_directory: str) -> None:
        """Display the saved archive directory or the empty-state text."""
        self._archive_directory = archive_directory
        self._path.set(archive_directory or t("status.no_archive_directory_long"))
