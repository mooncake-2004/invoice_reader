"""Current monthly Excel selection controls."""

from collections.abc import Callable
import tkinter as tk
from tkinter import ttk


class ExcelPanel(ttk.LabelFrame):
    """Show and change the workbook used by approved invoices."""

    def __init__(
        self,
        master: tk.Misc,
        excel_path: str,
        on_create: Callable[[], None],
        on_select: Callable[[], None],
    ) -> None:
        super().__init__(master, text="Excel", padding=8)
        self._path = tk.StringVar(value=excel_path or "尚未选择 Excel 文件")
        ttk.Button(self, text="新建月度 Excel", command=on_create).pack(side="left")
        ttk.Button(self, text="选择已有 Excel", command=on_select).pack(side="left", padx=(8, 0))
        ttk.Label(self, textvariable=self._path, wraplength=900).pack(side="left", padx=(12, 0))

    def set_excel_path(self, excel_path: str) -> None:
        """Display the selected path, or its empty-state text."""
        self._path.set(excel_path or "尚未选择 Excel 文件")
