"""Controls for the local PDF archive directory."""

from collections.abc import Callable
import tkinter as tk
from tkinter import ttk


class ArchivePanel(ttk.LabelFrame):
    """Show and update the directory used after a successful Excel write."""

    def __init__(self, master: tk.Misc, archive_directory: str, on_select: Callable[[], None]) -> None:
        super().__init__(master, text="归档", padding=8)
        self._path = tk.StringVar(value=archive_directory or "尚未设置归档目录")
        ttk.Button(self, text="设置归档目录", command=on_select).pack(side="left")
        ttk.Label(self, textvariable=self._path, wraplength=900).pack(side="left", padx=(12, 0))

    def set_archive_directory(self, archive_directory: str) -> None:
        """Display the saved archive directory or the empty-state text."""
        self._path.set(archive_directory or "尚未设置归档目录")
