"""Current monthly Excel selection controls."""

from collections.abc import Callable
import tkinter as tk
from tkinter import ttk

from invoice_reader.i18n import t


class ExcelPanel(ttk.LabelFrame):
    """Show and change the workbook used by approved invoices."""

    def __init__(
        self,
        master: tk.Misc,
        excel_path: str,
        on_create: Callable[[], None],
        on_select: Callable[[], None],
    ) -> None:
        super().__init__(master, text=t("section.excel"), padding=8)
        self._excel_path = excel_path
        self._path = tk.StringVar()
        self._create_button = ttk.Button(self, command=on_create)
        self._create_button.pack(side="left")
        self._select_button = ttk.Button(self, command=on_select)
        self._select_button.pack(side="left", padx=(8, 0))
        ttk.Label(self, textvariable=self._path, wraplength=900).pack(side="left", padx=(12, 0))
        self.retranslate()

    def retranslate(self) -> None:
        """Refresh workbook controls and the empty-state text in the current language."""
        if self.cget("text"):
            self.configure(text=t("section.excel"))
        self._create_button.configure(text=t("btn.create_excel"))
        self._select_button.configure(text=t("btn.select_excel"))
        self._path.set(self._excel_path or t("status.no_excel_file"))

    def set_excel_path(self, excel_path: str) -> None:
        """Display the selected path, or its empty-state text."""
        self._excel_path = excel_path
        self._path.set(excel_path or t("status.no_excel_file"))
